"""Evaluation tests for relevance (accurate matching)."""
import pytest
import json
from pathlib import Path

from tests.conftest import orchestrator, search_request


# Load test data
FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_QUERIES_PATH = FIXTURES_DIR / "test_queries.json"


@pytest.fixture
def relevance_test_cases():
    """Load relevance test cases from fixtures."""
    with open(TEST_QUERIES_PATH) as f:
        data = json.load(f)
    return data["relevance_test_cases"]


@pytest.mark.asyncio
async def test_faded_stop_sign_relevance(orchestrator, search_request):
    """Test relevance for faded STOP sign query."""
    query = "Faded STOP sign on 65 kmph highway"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    # Assertions
    assert response.results, "Should return at least one result"
    assert response.results[0].confidence >= 0.7, "Top result should have confidence >= 0.7"
    
    # Check category match
    top_result = response.results[0]
    assert top_result.category == "Road Sign", "Should match Road Sign category"
    
    # Check problem type match
    assert "Faded" in top_result.problem or top_result.problem == "Faded", "Should match Faded problem type"
    
    # Check IRC reference present
    assert top_result.irc_reference.code, "Should have IRC reference code"
    assert top_result.irc_reference.clause, "Should have IRC clause"


@pytest.mark.asyncio
async def test_missing_pedestrian_crossing_relevance(orchestrator, search_request):
    """Test relevance for missing pedestrian crossing markings."""
    query = "Missing road markings at pedestrian crossing"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    # Assertions
    assert response.results, "Should return at least one result"
    assert response.results[0].confidence >= 0.7, "Top result should have confidence >= 0.7"
    
    top_result = response.results[0]
    assert top_result.category == "Road Marking", "Should match Road Marking category"
    assert "Missing" in top_result.problem or top_result.problem == "Missing", "Should match Missing problem type"


@pytest.mark.asyncio
async def test_damaged_speed_breaker_relevance(orchestrator, search_request):
    """Test relevance for damaged speed breaker."""
    query = "Damaged speed breaker on urban road"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    # Assertions
    assert response.results, "Should return at least one result"
    assert response.results[0].confidence >= 0.7, "Top result should have confidence >= 0.7"
    
    top_result = response.results[0]
    assert top_result.category == "Traffic Calming Measures", "Should match Traffic Calming Measures category"
    assert "Damaged" in top_result.problem or top_result.problem == "Damaged", "Should match Damaged problem type"


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", [
    {
        "query": "Faded STOP sign on 65 kmph highway",
        "expected_category": "Road Sign",
        "expected_problem": "Faded",
        "min_confidence": 0.7
    },
    {
        "query": "Missing road markings at pedestrian crossing",
        "expected_category": "Road Marking",
        "expected_problem": "Missing",
        "min_confidence": 0.7
    },
    {
        "query": "Damaged speed breaker on urban road",
        "expected_category": "Traffic Calming Measures",
        "expected_problem": "Damaged",
        "min_confidence": 0.7
    }
])
async def test_relevance_parametrized(orchestrator, search_request, test_case):
    """Parametrized test for relevance."""
    request = search_request(query=test_case["query"], max_results=5)
    response = await orchestrator.process_query(request)
    
    assert response.results, f"Should return results for: {test_case['query']}"
    top_result = response.results[0]
    
    assert top_result.confidence >= test_case["min_confidence"], \
        f"Confidence {top_result.confidence} should be >= {test_case['min_confidence']}"
    
    assert top_result.category == test_case["expected_category"], \
        f"Category {top_result.category} should be {test_case['expected_category']}"
    
    assert test_case["expected_problem"] in top_result.problem or top_result.problem == test_case["expected_problem"], \
        f"Problem {top_result.problem} should match {test_case['expected_problem']}"


@pytest.mark.asyncio
async def test_entity_extraction_accuracy(orchestrator, search_request):
    """Test entity extraction accuracy."""
    query = "Faded STOP sign on 65 kmph highway"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    # Check that entities were extracted
    assert response.metadata.entities_extracted, "Should extract entities from query"
    
    entities = response.metadata.entities_extracted
    assert entities.problems or entities.category or entities.speed, "Should extract at least one entity"


@pytest.mark.asyncio
async def test_filter_application_correctness(orchestrator, search_request):
    """Test that filters are applied correctly."""
    query = "Faded STOP sign"
    request = search_request(
        query=query,
        max_results=5,
        filters={"category": ["Road Sign"], "problem": ["Faded"]}
    )
    
    response = await orchestrator.process_query(request)
    
    # All results should match filters
    for result in response.results:
        assert result.category == "Road Sign", "All results should match category filter"
        assert result.problem == "Faded" or "Faded" in result.problem, "All results should match problem filter"


@pytest.mark.asyncio
async def test_result_ranking_quality(orchestrator, search_request):
    """Test that results are ranked by relevance."""
    query = "Faded STOP sign on highway"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    # Results should be sorted by confidence (descending)
    if len(response.results) > 1:
        confidences = [r.confidence for r in response.results]
        assert confidences == sorted(confidences, reverse=True), "Results should be sorted by confidence descending"

