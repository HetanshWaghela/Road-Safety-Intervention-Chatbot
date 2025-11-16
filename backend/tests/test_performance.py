"""Performance tests for query response times and cache effectiveness."""
import pytest
import time
import json
from pathlib import Path

from tests.conftest import orchestrator, search_request


# Load performance test data
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PERFORMANCE_QUERIES_PATH = FIXTURES_DIR / "performance_queries.json"


@pytest.fixture
def performance_benchmarks():
    """Load performance benchmarks from fixtures."""
    with open(PERFORMANCE_QUERIES_PATH) as f:
        data = json.load(f)
    return data["performance_benchmarks"]


@pytest.mark.asyncio
async def test_simple_query_response_time(orchestrator, search_request, performance_benchmarks):
    """Test response time for simple queries."""
    query = "stop sign"
    request = search_request(query=query, max_results=5)
    
    start_time = time.time()
    response = await orchestrator.process_query(request)
    elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
    
    max_time = performance_benchmarks["simple_query_max_time_ms"]
    assert elapsed_time < max_time, \
        f"Simple query took {elapsed_time:.0f}ms, should be < {max_time}ms"
    
    assert response.metadata.query_time_ms < max_time, \
        f"Query time in metadata is {response.metadata.query_time_ms}ms, should be < {max_time}ms"


@pytest.mark.asyncio
async def test_medium_query_response_time(orchestrator, search_request, performance_benchmarks):
    """Test response time for medium complexity queries."""
    query = "faded stop sign on highway"
    request = search_request(query=query, max_results=5)
    
    start_time = time.time()
    response = await orchestrator.process_query(request)
    elapsed_time = (time.time() - start_time) * 1000
    
    max_time = performance_benchmarks["medium_query_max_time_ms"]
    assert elapsed_time < max_time, \
        f"Medium query took {elapsed_time:.0f}ms, should be < {max_time}ms"


@pytest.mark.asyncio
async def test_complex_query_response_time(orchestrator, search_request, performance_benchmarks):
    """Test response time for complex queries."""
    query = "faded red octagonal stop sign with white border on national highway at 65 kmph speed limit"
    request = search_request(query=query, max_results=5)
    
    start_time = time.time()
    response = await orchestrator.process_query(request)
    elapsed_time = (time.time() - start_time) * 1000
    
    max_time = performance_benchmarks["complex_query_max_time_ms"]
    assert elapsed_time < max_time, \
        f"Complex query took {elapsed_time:.0f}ms, should be < {max_time}ms"


@pytest.mark.asyncio
async def test_cache_effectiveness(orchestrator, search_request, performance_benchmarks):
    """Test cache hit rate and response time."""
    query = "faded stop sign"
    request = search_request(query=query, max_results=5)
    
    # First request (cache miss)
    start_time = time.time()
    response1 = await orchestrator.process_query(request)
    first_time = (time.time() - start_time) * 1000
    
    # Second request (should be cached)
    start_time = time.time()
    response2 = await orchestrator.process_query(request)
    cached_time = (time.time() - start_time) * 1000
    
    # Cached response should be faster
    max_cache_time = performance_benchmarks["cache_response_max_time_ms"]
    assert cached_time < max_cache_time, \
        f"Cached response took {cached_time:.0f}ms, should be < {max_cache_time}ms"
    
    # Results should be the same
    assert len(response1.results) == len(response2.results), "Cached results should match"


@pytest.mark.asyncio
async def test_concurrent_queries(orchestrator, search_request):
    """Test handling of multiple concurrent queries."""
    import asyncio
    
    queries = ["stop sign", "road marking", "speed breaker"]
    requests = [search_request(query=q, max_results=3) for q in queries]
    
    start_time = time.time()
    responses = await asyncio.gather(*[orchestrator.process_query(req) for req in requests])
    total_time = (time.time() - start_time) * 1000
    
    # All queries should complete
    assert len(responses) == len(queries), "All queries should complete"
    
    # Each response should have results
    for response in responses:
        assert response.results is not None, "Each response should have results"


@pytest.mark.asyncio
async def test_sequential_query_batch(orchestrator, search_request):
    """Test sequential processing of query batch."""
    queries = ["stop sign", "road marking", "speed breaker", "pedestrian crossing"]
    
    start_time = time.time()
    for query in queries:
        request = search_request(query=query, max_results=3)
        response = await orchestrator.process_query(request)
        assert response.results is not None, f"Should return results for: {query}"
    total_time = (time.time() - start_time) * 1000
    
    # Should complete in reasonable time (less than sum of individual max times)
    max_total_time = 2000 * len(queries)  # 2s per query
    assert total_time < max_total_time, \
        f"Batch processing took {total_time:.0f}ms, should be < {max_total_time}ms"

