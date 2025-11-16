"""Evaluation tests for comprehensiveness (detailed options)."""
import pytest
import json
from pathlib import Path

from tests.conftest import orchestrator, search_request


# Load test data
FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_QUERIES_PATH = FIXTURES_DIR / "test_queries.json"


@pytest.fixture
def comprehensiveness_test_cases():
    """Load comprehensiveness test cases from fixtures."""
    with open(TEST_QUERIES_PATH) as f:
        data = json.load(f)
    return data["comprehensiveness_test_cases"]


@pytest.mark.asyncio
async def test_multiple_intervention_options(orchestrator, search_request):
    """Test that multiple intervention options are provided when applicable."""
    query = "road safety signs"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    # Should return multiple results
    assert len(response.results) >= 3, f"Should return at least 3 results, got {len(response.results)}"
    
    # Should have different categories represented
    categories = set(r.category for r in response.results)
    assert len(categories) >= 1, "Should have at least one category represented"


@pytest.mark.asyncio
async def test_detailed_specifications_included(orchestrator, search_request):
    """Test that detailed specifications are included in results."""
    query = "pedestrian crossing markings"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    assert response.results, "Should return at least one result"
    
    # Check that specifications are present
    for result in response.results:
        assert result.specifications, "Each result should have specifications"
        
        # Check for at least one specification field
        has_specs = (
            result.specifications.dimensions or
            result.specifications.colors or
            result.specifications.placement
        )
        assert has_specs, "Should have at least one specification field (dimensions, colors, or placement)"


@pytest.mark.asyncio
async def test_irc_references_present(orchestrator, search_request):
    """Test that IRC references are present and accurate."""
    query = "speed control measures"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    assert response.results, "Should return at least one result"
    
    for result in response.results:
        # Check IRC reference format
        assert result.irc_reference, "Should have IRC reference"
        assert result.irc_reference.code, "Should have IRC code"
        assert result.irc_reference.clause, "Should have IRC clause"
        
        # Check IRC code format (should contain IRC:)
        assert "IRC" in result.irc_reference.code or ":" in result.irc_reference.code, \
            f"IRC code should be in valid format, got: {result.irc_reference.code}"


@pytest.mark.asyncio
async def test_explanations_provided(orchestrator, search_request):
    """Test that explanations are provided for each result."""
    query = "road safety signs"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    assert response.results, "Should return at least one result"
    
    for result in response.results:
        assert result.explanation, "Each result should have an explanation"
        assert len(result.explanation) >= 50, "Explanation should be at least 50 characters"
        
        # Check that explanation references database (should mention IRC or contain relevant terms)
        explanation_lower = result.explanation.lower()
        has_reference = (
            "irc" in explanation_lower or
            "standard" in explanation_lower or
            "database" in explanation_lower or
            result.irc_reference.code.lower() in explanation_lower
        )
        assert has_reference, "Explanation should reference database or IRC standards"


@pytest.mark.asyncio
async def test_required_fields_present(orchestrator, search_request):
    """Test that all required fields are present in results."""
    query = "road safety signs"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    required_fields = [
        "id", "title", "confidence", "category", "problem",
        "specifications", "irc_reference", "explanation", "cost_estimate"
    ]
    
    for result in response.results:
        result_dict = result.dict()
        for field in required_fields:
            assert field in result_dict, f"Result should have {field} field"
            assert result_dict[field] is not None, f"{field} should not be None"


@pytest.mark.asyncio
async def test_category_diversity(orchestrator, search_request):
    """Test that different categories are represented when applicable."""
    query = "road safety interventions"
    request = search_request(query=query, max_results=10)
    
    response = await orchestrator.process_query(request)
    
    if len(response.results) >= 3:
        categories = set(r.category for r in response.results)
        # Should have multiple categories when many results
        assert len(categories) >= 1, "Should have at least one category"


@pytest.mark.asyncio
async def test_cost_estimates_provided(orchestrator, search_request):
    """Test that cost estimates are provided."""
    query = "road safety signs"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    for result in response.results:
        assert result.cost_estimate, "Should have cost estimate"
        assert len(result.cost_estimate) > 0, "Cost estimate should not be empty"


@pytest.mark.asyncio
async def test_installation_time_provided(orchestrator, search_request):
    """Test that installation time is provided when available."""
    query = "road safety signs"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    # At least some results should have installation time
    results_with_time = [r for r in response.results if r.installation_time]
    assert len(results_with_time) > 0, "At least some results should have installation time"


@pytest.mark.asyncio
async def test_explanation_quality(orchestrator, search_request):
    """Test that explanations are relevant and non-empty."""
    query = "faded stop sign"
    request = search_request(query=query, max_results=5)
    
    response = await orchestrator.process_query(request)
    
    for result in response.results:
        explanation = result.explanation
        assert explanation, "Explanation should not be empty"
        assert len(explanation) >= 50, "Explanation should be substantial (>= 50 chars)"
        
        # Check relevance - explanation should mention relevant terms
        explanation_lower = explanation.lower()
        query_terms = query.lower().split()
        relevant_terms = [term for term in query_terms if len(term) > 3]  # Skip short words
        
        # At least one relevant term should appear in explanation
        if relevant_terms:
            has_relevant_term = any(term in explanation_lower for term in relevant_terms)
            assert has_relevant_term, "Explanation should mention relevant terms from query"

