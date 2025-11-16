"""Pytest configuration and fixtures."""
import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.services import GeminiService, VectorStoreService, DatabaseService, CacheService
from app.core.orchestrator import QueryOrchestrator
from app.core.strategies import RAGSearchStrategy, StructuredQueryStrategy, HybridFusionStrategy
from app.models.schemas import SearchRequest


@pytest.fixture(scope="session")
def gemini_service():
    """Create Gemini service instance."""
    return GeminiService()


@pytest.fixture(scope="session")
def vector_store_service():
    """Create vector store service instance."""
    return VectorStoreService(
        persist_directory=str(settings.chroma_dir),
        collection_name=settings.collection_name
    )


@pytest.fixture(scope="session")
def database_service():
    """Create database service instance."""
    data_path = settings.processed_data_dir / "interventions.json"
    return DatabaseService(data_path=data_path)


@pytest.fixture(scope="session")
def cache_service():
    """Create cache service instance."""
    return CacheService(maxsize=1000, ttl=settings.cache_ttl)


@pytest.fixture(scope="session")
def orchestrator(gemini_service, vector_store_service, database_service, cache_service):
    """Create query orchestrator instance."""
    rag_strategy = RAGSearchStrategy(
        vector_store=vector_store_service,
        gemini_service=gemini_service
    )
    structured_strategy = StructuredQueryStrategy(database=database_service)
    hybrid_strategy = HybridFusionStrategy(
        rag_strategy=rag_strategy,
        structured_strategy=structured_strategy
    )
    
    return QueryOrchestrator(
        rag_strategy=rag_strategy,
        structured_strategy=structured_strategy,
        hybrid_strategy=hybrid_strategy,
        gemini_service=gemini_service,
        cache_service=cache_service,
    )


@pytest.fixture
def search_request():
    """Create a basic search request."""
    def _create_request(query: str, **kwargs):
        return SearchRequest(query=query, **kwargs)
    return _create_request

