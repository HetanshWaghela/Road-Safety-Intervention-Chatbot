"""Integration tests for end-to-end search flow."""
import pytest

from tests.conftest import orchestrator, search_request


@pytest.mark.asyncio
async def test_end_to_end_search_flow(orchestrator, search_request):
    """Test complete search flow from query to response."""
    query = "Faded STOP sign on 65 kmph highway"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    # Validate response structure
    assert response.query == query, "Response should contain original query"
    assert response.results is not None, "Response should have results list"
    assert response.metadata is not None, "Response should have metadata"
    
    # Validate metadata
    assert response.metadata.search_strategy, "Should have search strategy"
    assert response.metadata.total_results >= 0, "Should have total results count"
    assert response.metadata.query_time_ms > 0, "Should have query time"


@pytest.mark.asyncio
async def test_response_format_matches_evaluation_criteria(orchestrator, search_request):
    """Test that response format matches evaluation criteria requirements."""
    query = "Missing road markings at pedestrian crossing"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    # Check for recommended interventions
    assert response.results, "Should have recommended interventions"
    
    # Check for explanations
    for result in response.results:
        assert result.explanation, "Each result should have explanation"
    
    # Check for database references
    for result in response.results:
        assert result.irc_reference, "Each result should have IRC reference"
        assert result.irc_reference.code, "Should have IRC code"
        assert result.irc_reference.clause, "Should have IRC clause"


@pytest.mark.asyncio
async def test_simple_query(orchestrator, search_request):
    """Test simple query processing."""
    query = "stop sign"
    request = search_request(query=query, max_results=3)
    
    response = await orchestrator.process_query(request)
    
    assert response.results, "Should return results for simple query"
    assert len(response.results) <= 3, "Should respect max_results limit"


@pytest.mark.asyncio
async def test_complex_query_with_filters(orchestrator, search_request):
    """Test complex query with filters."""
    query = "faded road sign"
    request = search_request(
        query=query,
        max_results=5,
        filters={"category": ["Road Sign"], "problem": ["Faded"]}
    )
    
    response = await orchestrator.process_query(request)
    
    # All results should match filters
    for result in response.results:
        assert result.category == "Road Sign", "Should match category filter"
        assert result.problem == "Faded" or "Faded" in result.problem, "Should match problem filter"


@pytest.mark.asyncio
async def test_query_with_speed_range(orchestrator, search_request):
    """Test query with speed range filter."""
    query = "road sign on highway"
    request = search_request(
        query=query,
        max_results=5,
        filters={"speed_min": 50, "speed_max": 100}
    )
    
    response = await orchestrator.process_query(request)
    
    # Results should be relevant to speed range (if speed data available)
    assert response.results is not None, "Should return results"


@pytest.mark.asyncio
async def test_empty_results_handling(orchestrator, search_request):
    """Test handling of queries with no results."""
    query = "xyzabc123nonexistent"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    # Should return empty results list, not error
    assert response.results is not None, "Should have results list (even if empty)"
    assert isinstance(response.results, list), "Results should be a list"
    
    # Should have synthesis explaining no results
    if not response.results:
        assert response.synthesis, "Should have synthesis explaining no results"


@pytest.mark.asyncio
async def test_data_types_correct(orchestrator, search_request):
    """Test that response data types are correct."""
    query = "road safety sign"
    request = search_request(query=query, max_results=3)
    
    response = await orchestrator.process_query(request)
    
    # Check types
    assert isinstance(response.query, str), "Query should be string"
    assert isinstance(response.results, list), "Results should be list"
    assert isinstance(response.metadata.total_results, int), "Total results should be int"
    assert isinstance(response.metadata.query_time_ms, int), "Query time should be int"
    
    if response.results:
        result = response.results[0]
        assert isinstance(result.confidence, float), "Confidence should be float"
        assert isinstance(result.category, str), "Category should be string"
        assert isinstance(result.problem, str), "Problem should be string"

