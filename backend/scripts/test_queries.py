"""Test script with sample queries and evaluation criteria checks."""
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.app.config import settings
from backend.app.services import GeminiService, VectorStoreService, DatabaseService, CacheService
from backend.app.core.orchestrator import QueryOrchestrator
from backend.app.core.strategies import RAGSearchStrategy, StructuredQueryStrategy, HybridFusionStrategy
from backend.app.models.schemas import SearchRequest
from backend.app.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def evaluate_relevance(response, query: str) -> dict:
    """Evaluate relevance of results."""
    if not response.results:
        return {"score": 0.0, "passed": False, "details": "No results returned"}
    
    top_result = response.results[0]
    score = top_result.confidence
    
    # Check if top result has high confidence
    passed = score >= 0.7
    
    details = {
        "top_confidence": score,
        "top_result_category": top_result.category,
        "top_result_problem": top_result.problem,
        "has_irc_reference": bool(top_result.irc_reference.code),
    }
    
    return {"score": score, "passed": passed, "details": details}


def evaluate_comprehensiveness(response) -> dict:
    """Evaluate comprehensiveness of results."""
    if not response.results:
        return {"score": 0.0, "passed": False, "details": "No results returned"}
    
    result_count = len(response.results)
    result_count_score = min(1.0, result_count / 5.0)
    
    # Check detail level
    detail_scores = []
    for result in response.results:
        detail_score = 0.0
        if result.specifications:
            if result.specifications.dimensions:
                detail_score += 0.2
            if result.specifications.colors:
                detail_score += 0.2
            if result.specifications.placement:
                detail_score += 0.2
        if result.irc_reference and result.irc_reference.code:
            detail_score += 0.2
        if result.explanation and len(result.explanation) > 50:
            detail_score += 0.2
        detail_scores.append(detail_score)
    
    avg_detail_score = sum(detail_scores) / len(detail_scores) if detail_scores else 0.0
    
    # Category diversity
    categories = set(r.category for r in response.results)
    category_diversity = min(1.0, len(categories) / 3.0)
    
    comprehensiveness_score = (result_count_score * 0.3) + (avg_detail_score * 0.5) + (category_diversity * 0.2)
    passed = comprehensiveness_score >= 0.6
    
    details = {
        "result_count": result_count,
        "unique_categories": len(categories),
        "avg_detail_score": avg_detail_score,
        "all_have_irc_references": all(r.irc_reference.code for r in response.results),
        "all_have_explanations": all(r.explanation and len(r.explanation) > 50 for r in response.results),
    }
    
    return {"score": comprehensiveness_score, "passed": passed, "details": details}


def validate_output_format(response) -> dict:
    """Validate that output format matches evaluation criteria."""
    issues = []
    
    # Check recommended interventions present
    if not response.results:
        issues.append("No recommended interventions present")
    else:
        # Check each result has required fields
        required_fields = ["id", "title", "confidence", "category", "problem", "specifications", "irc_reference", "explanation"]
        for idx, result in enumerate(response.results, 1):
            result_dict = result.dict()
            for field in required_fields:
                if field not in result_dict or result_dict[field] is None:
                    issues.append(f"Result {idx} missing field: {field}")
    
    # Check explanations include database references
    for idx, result in enumerate(response.results, 1):
        if not result.explanation:
            issues.append(f"Result {idx} missing explanation")
        elif not (result.irc_reference.code in result.explanation.lower() or "irc" in result.explanation.lower()):
            issues.append(f"Result {idx} explanation doesn't reference database")
    
    # Validate IRC references
    for idx, result in enumerate(response.results, 1):
        if not result.irc_reference.code:
            issues.append(f"Result {idx} missing IRC code")
        if not result.irc_reference.clause:
            issues.append(f"Result {idx} missing IRC clause")
    
    passed = len(issues) == 0
    return {"passed": passed, "issues": issues}


async def test_query(orchestrator: QueryOrchestrator, query: str):
    """Test a single query with evaluation criteria checks."""
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Query: {query}")
    logger.info("=" * 60)

    request = SearchRequest(query=query, max_results=5)
    start_time = asyncio.get_event_loop().time()

    response = await orchestrator.process_query(request)
    
    elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000

    logger.info(f"\nFound {response.metadata.total_results} results in {response.metadata.query_time_ms}ms")
    logger.info(f"Strategy: {response.metadata.search_strategy}")

    # Evaluation criteria checks
    relevance = evaluate_relevance(response, query)
    comprehensiveness = evaluate_comprehensiveness(response)
    output_format = validate_output_format(response)
    
    # Display results
    for idx, result in enumerate(response.results, 1):
        logger.info(f"\n{idx}. {result.title}")
        logger.info(f"   Confidence: {result.confidence:.2%}")
        logger.info(f"   Category: {result.category}")
        logger.info(f"   Problem: {result.problem}")
        logger.info(f"   IRC: {result.irc_reference.code} {result.irc_reference.clause}")

    # Evaluation report
    logger.info(f"\n{'=' * 60}")
    logger.info("EVALUATION REPORT")
    logger.info("=" * 60)
    
    logger.info(f"\n📊 Relevance Score: {relevance['score']:.2%}")
    logger.info(f"   Status: {'✅ PASSED' if relevance['passed'] else '❌ FAILED'}")
    logger.info(f"   Details: {json.dumps(relevance['details'], indent=2)}")
    
    logger.info(f"\n📋 Comprehensiveness Score: {comprehensiveness['score']:.2%}")
    logger.info(f"   Status: {'✅ PASSED' if comprehensiveness['passed'] else '❌ FAILED'}")
    logger.info(f"   Details: {json.dumps(comprehensiveness['details'], indent=2)}")
    
    logger.info(f"\n📝 Output Format Validation: {'✅ PASSED' if output_format['passed'] else '❌ FAILED'}")
    if output_format['issues']:
        logger.info(f"   Issues:")
        for issue in output_format['issues']:
            logger.info(f"     - {issue}")
    
    logger.info(f"\n⏱️  Performance Metrics:")
    logger.info(f"   Query Time: {response.metadata.query_time_ms}ms")
    logger.info(f"   Actual Time: {elapsed_time:.0f}ms")
    
    logger.info(f"\n📝 AI Synthesis:")
    logger.info(response.synthesis[:500] + "..." if len(response.synthesis) > 500 else response.synthesis)
    
    return {
        "query": query,
        "relevance": relevance,
        "comprehensiveness": comprehensiveness,
        "output_format": output_format,
        "performance": {
            "query_time_ms": response.metadata.query_time_ms,
            "actual_time_ms": elapsed_time,
        }
    }


async def main():
    """Run test queries with evaluation criteria."""
    logger.info("=" * 60)
    logger.info("ROAD SAFETY INTERVENTION EVALUATION TEST SUITE")
    logger.info("=" * 60)
    logger.info("Initializing services...")

    # Initialize services
    gemini_service = GeminiService()
    vector_store = VectorStoreService(
        persist_directory=str(settings.chroma_dir), collection_name=settings.collection_name
    )
    database = DatabaseService(data_path=settings.processed_data_dir / "interventions.json")
    cache = CacheService()

    # Initialize strategies
    rag_strategy = RAGSearchStrategy(vector_store=vector_store, gemini_service=gemini_service)
    structured_strategy = StructuredQueryStrategy(database=database)
    hybrid_strategy = HybridFusionStrategy(rag_strategy=rag_strategy, structured_strategy=structured_strategy)

    # Initialize orchestrator
    orchestrator = QueryOrchestrator(
        rag_strategy=rag_strategy,
        structured_strategy=structured_strategy,
        hybrid_strategy=hybrid_strategy,
        gemini_service=gemini_service,
        cache_service=cache,
    )

    # Test queries
    test_queries = [
        "Faded STOP sign on 65 kmph highway",
        "Missing road markings at pedestrian crossing",
        "Damaged speed breaker on urban road",
        "Obstruction blocking road sign visibility",
    ]

    results = []
    for query in test_queries:
        result = await test_query(orchestrator, query)
        results.append(result)
        await asyncio.sleep(1)  # Brief pause between queries

    # Summary report
    logger.info("\n" + "=" * 60)
    logger.info("EVALUATION SUMMARY")
    logger.info("=" * 60)
    
    total_queries = len(results)
    relevance_passed = sum(1 for r in results if r["relevance"]["passed"])
    comprehensiveness_passed = sum(1 for r in results if r["comprehensiveness"]["passed"])
    format_passed = sum(1 for r in results if r["output_format"]["passed"])
    
    avg_relevance = sum(r["relevance"]["score"] for r in results) / total_queries
    avg_comprehensiveness = sum(r["comprehensiveness"]["score"] for r in results) / total_queries
    avg_query_time = sum(r["performance"]["query_time_ms"] for r in results) / total_queries
    
    logger.info(f"\nTotal Queries Tested: {total_queries}")
    logger.info(f"\nRelevance:")
    logger.info(f"  Passed: {relevance_passed}/{total_queries} ({relevance_passed/total_queries*100:.1f}%)")
    logger.info(f"  Average Score: {avg_relevance:.2%}")
    
    logger.info(f"\nComprehensiveness:")
    logger.info(f"  Passed: {comprehensiveness_passed}/{total_queries} ({comprehensiveness_passed/total_queries*100:.1f}%)")
    logger.info(f"  Average Score: {avg_comprehensiveness:.2%}")
    
    logger.info(f"\nOutput Format:")
    logger.info(f"  Passed: {format_passed}/{total_queries} ({format_passed/total_queries*100:.1f}%)")
    
    logger.info(f"\nPerformance:")
    logger.info(f"  Average Query Time: {avg_query_time:.0f}ms")
    
    logger.info("\n✅ Evaluation test suite completed!")


if __name__ == "__main__":
    asyncio.run(main())
