"""Main query orchestrator."""
from typing import List, Dict, Any, Optional
import time
from ..models.schemas import SearchRequest, SearchResponse, SearchMetadata, ExtractedEntities
from ..models.intervention import InterventionResult, InterventionRecommendation, Specifications, IRCReference
from ..services.gemini_service import GeminiService
from ..services.cache import CacheService
from ..utils.helpers import generate_cache_key, estimate_cost, estimate_installation_time, extract_maintenance_info
from ..utils.logger import get_logger
from .entity_extractor import EntityExtractor
from .ranker import ResultRanker
from .strategies import RAGSearchStrategy, StructuredQueryStrategy, HybridFusionStrategy

logger = get_logger(__name__)


class QueryOrchestrator:
    """Orchestrate query processing through all strategies."""

    def __init__(
        self,
        rag_strategy: RAGSearchStrategy,
        structured_strategy: StructuredQueryStrategy,
        hybrid_strategy: HybridFusionStrategy,
        gemini_service: GeminiService,
        cache_service: CacheService,
    ):
        """Initialize orchestrator."""
        self.rag_strategy = rag_strategy
        self.structured_strategy = structured_strategy
        self.hybrid_strategy = hybrid_strategy
        self.gemini_service = gemini_service
        self.cache_service = cache_service
        self.entity_extractor = EntityExtractor(gemini_service)
        self.ranker = ResultRanker()

    async def process_query(self, request: SearchRequest) -> SearchResponse:
        """Process search query end-to-end."""
        start_time = time.time()

        try:
            # Check cache
            cache_key = generate_cache_key(request.query, request.filters.dict() if request.filters else None)
            cached_response = self.cache_service.get(cache_key)

            if cached_response:
                logger.log_operation(
                    "cache_hit",
                    "Returning cached response",
                    query_id=getattr(request, "request_id", None),
                )
                # Still log evaluation metrics for cached responses
                # Extract data from cached response
                if hasattr(cached_response, "results") and cached_response.results:
                    # Convert recommendations back to results for metrics
                    # This is a simplified version - in production, you might want to store metrics with cache
                    pass
                return cached_response

            # Extract entities
            entities = await self.entity_extractor.extract(request.query)
            logger.log_operation(
                "entity_extraction",
                "Entities extracted from query",
                query_id=getattr(request, "request_id", None),
                entities=entities.dict() if entities else {},
            )

            # Merge entities into filters if not provided
            filters = self._merge_filters(request.filters.dict() if request.filters else {}, entities)

            # Select strategy
            strategy = self._select_strategy(request.strategy)
            logger.log_operation(
                "strategy_selection",
                f"Using search strategy: {strategy.name}",
                strategy=strategy.name,
                query_id=getattr(request, "request_id", None),
            )

            # Execute search
            results = await strategy.search(query=request.query, filters=filters, max_results=request.max_results * 2)

            # Post-process results
            results = self.ranker.apply_boost(results, request.query)
            results = self.ranker.deduplicate(results)
            results = self.ranker.rank_by_confidence(results)
            results = results[: request.max_results]

            # Convert to recommendations
            recommendations = self._convert_to_recommendations(results)

            # Generate synthesis
            synthesis = await self._generate_synthesis(request.query, results, entities)

            # Build metadata
            query_time_ms = int((time.time() - start_time) * 1000)
            metadata = SearchMetadata(
                search_strategy=strategy.name,
                total_results=len(results),
                query_time_ms=query_time_ms,
                gemini_tokens=self.gemini_service.get_token_usage(),
                entities_extracted=entities,
            )

            # Build response
            response = SearchResponse(
                query=request.query, results=recommendations, synthesis=synthesis, metadata=metadata
            )

            # Calculate and log evaluation metrics
            self._log_evaluation_metrics(
                query=request.query,
                results=results,
                recommendations=recommendations,
                entities=entities,
                filters=filters,
                strategy_name=strategy.name,
                query_time_ms=query_time_ms,
            )

            # Cache response
            self.cache_service.set(cache_key, response)

            logger.info("Query processed successfully", operation="query_processing", query_time_ms=query_time_ms)
            return response

        except Exception as e:
            logger.error("Error processing query", operation="query_error", error=str(e), error_type=type(e).__name__)
            raise

    def _select_strategy(self, strategy_name: Optional[str] = None):
        """Select appropriate search strategy."""
        if strategy_name == "rag":
            return self.rag_strategy
        elif strategy_name == "structured":
            return self.structured_strategy
        elif strategy_name == "hybrid":
            return self.hybrid_strategy
        else:
            # Auto-select (default to hybrid)
            return self.hybrid_strategy

    def _merge_filters(self, filters: Dict[str, Any], entities: ExtractedEntities) -> Dict[str, Any]:
        """Merge extracted entities into filters."""
        # Add category from entities
        if entities.category and not filters.get("category"):
            filters["category"] = [entities.category]

        # Add problem types from entities
        if entities.problems and not filters.get("problem"):
            filters["problem"] = entities.problems

        # Add speed range from entities
        if entities.speed:
            if not filters.get("speed_min") and not filters.get("speed_max"):
                # Create a range around the speed
                filters["speed_min"] = max(0, entities.speed - 20)
                filters["speed_max"] = entities.speed + 20

        return filters

    def _convert_to_recommendations(self, results: List[InterventionResult]) -> List[InterventionRecommendation]:
        """Convert intervention results to detailed recommendations."""
        recommendations = []

        for result in results:
            intervention = result.intervention

            # Build specifications
            specs = Specifications(
                dimensions=", ".join(intervention.dimensions) if intervention.dimensions else None,
                colors=intervention.colors if intervention.colors else None,
                placement=", ".join(intervention.placement_distances) if intervention.placement_distances else None,
            )

            # Build IRC reference
            irc_ref = IRCReference(
                code=intervention.code, clause=intervention.clause, excerpt=intervention.data[:200] + "..."
            )

            # Create recommendation
            recommendation = InterventionRecommendation(
                id=intervention.id,
                title=f"{intervention.problem} - {intervention.type}",
                confidence=result.confidence,
                problem=intervention.problem,
                category=intervention.category,
                type=intervention.type,
                specifications=specs,
                explanation=result.match_reason or "Matched based on query relevance",
                irc_reference=irc_ref,
                cost_estimate=estimate_cost(intervention.problem, intervention.category),
                installation_time=estimate_installation_time(intervention.category, intervention.problem),
                maintenance=extract_maintenance_info(intervention.data),
                raw_data=intervention.data,
            )

            recommendations.append(recommendation)

        return recommendations

    async def _generate_synthesis(
        self, query: str, results: List[InterventionResult], entities: ExtractedEntities
    ) -> str:
        """Generate AI synthesis of results."""
        if not results:
            return "No interventions found matching your query. Please try rephrasing or broadening your search."

        # Convert results to dict format for Gemini
        interventions_data = [result.intervention.dict() for result in results[:3]]  # Top 3 for context

        # Generate synthesis
        synthesis = await self.gemini_service.synthesize_recommendation(query, interventions_data, entities)

        return synthesis

    def _calculate_relevance_score(
        self, results: List[InterventionResult], entities: ExtractedEntities, filters: Dict[str, Any]
    ) -> float:
        """Calculate relevance score based on entity matching and filter accuracy."""
        if not results:
            return 0.0

        # Calculate entity match quality
        entity_matches = 0
        total_entities = 0

        # Check problem type matches
        if entities.problems:
            total_entities += len(entities.problems)
            for result in results[:3]:  # Top 3 results
                if result.intervention.problem in entities.problems:
                    entity_matches += 1

        # Check category match
        if entities.category:
            total_entities += 1
            for result in results[:3]:
                if result.intervention.category == entities.category:
                    entity_matches += 1
                    break

        # Check speed range match
        if entities.speed:
            total_entities += 1
            for result in results[:3]:
                intervention = result.intervention
                if intervention.speed_min and intervention.speed_max:
                    if intervention.speed_min <= entities.speed <= intervention.speed_max:
                        entity_matches += 1
                        break

        # Calculate average confidence of top results
        top_confidences = [r.confidence for r in results[:3]]
        avg_confidence = sum(top_confidences) / len(top_confidences) if top_confidences else 0.0

        # Calculate filter match accuracy
        filter_match_score = 1.0
        if filters:
            filter_matches = 0
            filter_total = 0

            if filters.get("category"):
                filter_total += 1
                for result in results[:3]:
                    if result.intervention.category in filters["category"]:
                        filter_matches += 1
                        break

            if filters.get("problem"):
                filter_total += 1
                for result in results[:3]:
                    if result.intervention.problem in filters["problem"]:
                        filter_matches += 1
                        break

            if filter_total > 0:
                filter_match_score = filter_matches / filter_total

        # Combine scores: entity match (40%), confidence (40%), filter match (20%)
        entity_score = entity_matches / total_entities if total_entities > 0 else 0.5
        relevance_score = (entity_score * 0.4) + (avg_confidence * 0.4) + (filter_match_score * 0.2)

        return min(1.0, max(0.0, relevance_score))

    def _calculate_comprehensiveness_score(self, recommendations: List[InterventionRecommendation]) -> float:
        """Calculate comprehensiveness score based on result count and detail level."""
        if not recommendations:
            return 0.0

        # Result count score (normalized to 0-1, max at 5+ results)
        result_count_score = min(1.0, len(recommendations) / 5.0)

        # Detail level score
        detail_scores = []
        for rec in recommendations:
            detail_score = 0.0

            # Has specifications
            if rec.specifications:
                if rec.specifications.dimensions:
                    detail_score += 0.2
                if rec.specifications.colors:
                    detail_score += 0.2
                if rec.specifications.placement:
                    detail_score += 0.2

            # Has IRC reference
            if rec.irc_reference and rec.irc_reference.code:
                detail_score += 0.2

            # Has explanation
            if rec.explanation and len(rec.explanation) > 50:
                detail_score += 0.2

            detail_scores.append(detail_score)

        avg_detail_score = sum(detail_scores) / len(detail_scores) if detail_scores else 0.0

        # Category diversity score
        categories = set(rec.category for rec in recommendations)
        category_diversity = min(1.0, len(categories) / 3.0)  # Max score at 3+ categories

        # Combine scores: result count (30%), detail level (50%), diversity (20%)
        comprehensiveness_score = (
            (result_count_score * 0.3) + (avg_detail_score * 0.5) + (category_diversity * 0.2)
        )

        return min(1.0, max(0.0, comprehensiveness_score))

    def _log_evaluation_metrics(
        self,
        query: str,
        results: List[InterventionResult],
        recommendations: List[InterventionRecommendation],
        entities: ExtractedEntities,
        filters: Dict[str, Any],
        strategy_name: str,
        query_time_ms: int,
    ):
        """Log evaluation metrics for the search query."""
        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(results, entities, filters)

        # Calculate comprehensiveness score
        comprehensiveness_score = self._calculate_comprehensiveness_score(recommendations)

        # Extract confidence scores
        confidence_scores = [r.confidence for r in results]

        # Extract intervention IDs
        matched_intervention_ids = [r.intervention.id for r in results]

        # Calculate additional metrics
        unique_categories = len(set(r.intervention.category for r in results))
        irc_references_count = len(set(r.intervention.code for r in results if r.intervention.code))

        # Log evaluation metrics
        logger.log_evaluation_metrics(
            query=query,
            relevance_score=relevance_score,
            comprehensiveness_score=comprehensiveness_score,
            confidence_scores=confidence_scores,
            matched_intervention_ids=matched_intervention_ids,
            response_time_ms=query_time_ms,
            strategy=strategy_name,
            unique_categories=unique_categories,
            irc_references_count=irc_references_count,
            entity_extraction_quality=self._calculate_entity_extraction_quality(entities),
        )

    def _calculate_entity_extraction_quality(self, entities: ExtractedEntities) -> float:
        """Calculate quality of entity extraction."""
        score = 0.0
        total_fields = 5  # problems, category, type, speed, road_type

        if entities.problems:
            score += 1.0
        if entities.category:
            score += 1.0
        if entities.type:
            score += 1.0
        if entities.speed:
            score += 1.0
        if entities.road_type:
            score += 1.0

        return score / total_fields
