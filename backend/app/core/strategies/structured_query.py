"""Structured query strategy using database filters."""
from typing import List, Dict, Any, Optional
import logging
from .base import BaseStrategy
from ...models.intervention import InterventionResult, Intervention
from ...services.database import DatabaseService

logger = logging.getLogger(__name__)


class StructuredQueryStrategy(BaseStrategy):
    """Exact match search using structured database queries."""

    def __init__(self, database: DatabaseService):
        """Initialize structured query strategy."""
        self.database = database

    @property
    def name(self) -> str:
        return "structured"

    async def search(
        self, query: str, filters: Optional[Dict[str, Any]] = None, max_results: int = 10
    ) -> List[InterventionResult]:
        """Search using structured filters and text matching."""
        try:
            # Always try text search first (works without filters)
            results = self.database.text_search(query, limit=max_results * 2)
            
            # If filters are provided AND we have results, optionally refine with filters
            # But don't use filters if they would eliminate all results
            if filters and (filters.get("category") or filters.get("problem") or filters.get("speed_min") or filters.get("speed_max") or filters.get("irc_code")):
                # Try filtered search
                filtered_results = self.database.search_by_filters(
                    category=filters.get("category"),
                    problem=filters.get("problem"),
                    speed_min=filters.get("speed_min"),
                    speed_max=filters.get("speed_max"),
                    irc_code=filters.get("irc_code"),
                    limit=max_results * 2,
                )
                # Use filtered results if we got some, otherwise keep text search results
                if filtered_results:
                    results = filtered_results
                else:
                    logger.info(f"Filters returned no results, using text search results instead")
                
            # If still no results, return top interventions as fallback
            if not results:
                logger.warning(f"No results found for query: {query}. Returning top interventions.")
                results = self.database.get_all(limit=max_results)

            # Convert to InterventionResult objects
            intervention_results = []

            for result in results:
                # Normalize column names - handle 'S. No.' -> 's_no' mismatch
                normalized_result = result.copy()
                if 'S. No.' in normalized_result:
                    normalized_result['s_no'] = int(normalized_result.pop('S. No.'))
                elif 'S.No.' in normalized_result:
                    normalized_result['s_no'] = int(normalized_result.pop('S.No.'))
                elif 's_no' not in normalized_result:
                    # Create s_no from index if missing
                    normalized_result['s_no'] = normalized_result.get('id', '').split('_')[-1] if 'id' in normalized_result else 0
                    try:
                        normalized_result['s_no'] = int(normalized_result['s_no'])
                    except:
                        normalized_result['s_no'] = 0
                
                # Calculate confidence based on exact matches
                confidence = self._calculate_confidence(query, normalized_result, filters)

                intervention = Intervention(**normalized_result)

                intervention_results.append(
                    InterventionResult(
                        intervention=intervention,
                        confidence=confidence,
                        relevance_score=confidence,
                        match_reason=self._get_match_reason(result, filters),
                    )
                )

            logger.info(f"Structured search found {len(intervention_results)} results")
            return intervention_results

        except Exception as e:
            logger.error(f"Error in structured search: {e}")
            return []

    def _calculate_confidence(
        self, query: str, result: Dict[str, Any], filters: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score based on exact matches."""
        score = 0.5  # Base score

        query_lower = query.lower()

        # Exact problem match
        if result.get("problem", "").lower() in query_lower:
            score += 0.2

        # Category match
        if result.get("category", "").lower() in query_lower:
            score += 0.15

        # Type match
        if result.get("type", "").lower() in query_lower:
            score += 0.15

        # Filter matches
        if filters:
            if filters.get("category") and result.get("category") in filters["category"]:
                score += 0.1
            if filters.get("problem") and result.get("problem") in filters["problem"]:
                score += 0.1

        return min(score, 1.0)

    def _get_match_reason(self, result: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> str:
        """Get human-readable match reason."""
        reasons = []

        if filters:
            if filters.get("category"):
                reasons.append("Category filter match")
            if filters.get("problem"):
                reasons.append("Problem type filter match")
            if filters.get("speed_min") or filters.get("speed_max"):
                reasons.append("Speed range match")

        if not reasons:
            reasons.append("Text search match")

        return ", ".join(reasons)
