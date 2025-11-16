"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .config import settings
from .utils.logger import setup_logging, get_logger
from .api.middleware.logging import RequestLoggingMiddleware
from .services import (
    GeminiService,
    VectorStoreService,
    DatabaseService,
    CacheService,
    VisualGenerator,
    PDFReportGenerator,
    ImageAnalyzer,
    ScenarioPlanner,
    ComparisonService,
    AnalyticsService,
)
from .core.orchestrator import QueryOrchestrator
from .core.strategies import RAGSearchStrategy, StructuredQueryStrategy, HybridFusionStrategy
from .api.routes import search, interventions, health, wow_features, advanced_features

# Setup structured JSON logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered road safety intervention recommendation system using Google Gemini",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add request logging middleware (before CORS)
app.add_middleware(RequestLoggingMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
gemini_service: GeminiService = None
vector_store_service: VectorStoreService = None
database_service: DatabaseService = None
cache_service: CacheService = None
orchestrator: QueryOrchestrator = None

# 🌟 WOW Features Services 🌟
visual_generator: VisualGenerator = None
pdf_generator: PDFReportGenerator = None
image_analyzer: ImageAnalyzer = None
scenario_planner: ScenarioPlanner = None
comparison_service: ComparisonService = None
analytics_service: AnalyticsService = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global gemini_service
    global vector_store_service
    global database_service
    global cache_service
    global orchestrator
    global visual_generator
    global pdf_generator
    global image_analyzer
    global scenario_planner
    global comparison_service
    global analytics_service

    logger.info("🚀 Starting Road Safety Intervention API with WOW Features...")

    try:
        # Initialize services
        logger.info("Initializing Gemini service...")
        gemini_service = GeminiService()

        logger.info("Initializing vector store...")
        vector_store_service = VectorStoreService(
            persist_directory=str(settings.chroma_dir), collection_name=settings.collection_name
        )
        # Get or create collection
        try:
            collection = vector_store_service.get_collection()
            count = vector_store_service.count()
            logger.info(f"Vector store loaded with {count} documents")
            if count == 0:
                logger.warning("⚠️ Vector store is empty! Please run: python backend/scripts/setup_database.py")
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            logger.warning("⚠️ Vector store may not be initialized. Please run: python backend/scripts/setup_database.py")

        logger.info("Initializing database...")
        data_path = settings.processed_data_dir / "interventions.json"
        if not data_path.exists():
            logger.error(f"❌ Data file not found: {data_path}")
            logger.error("Please run setup script first: python backend/scripts/setup_database.py")
            raise FileNotFoundError(f"Database file not found: {data_path}")
        database_service = DatabaseService(data_path=data_path)
        count = len(database_service.df) if database_service.df is not None else 0
        logger.info(f"Database loaded with {count} interventions")
        if count == 0:
            logger.error("❌ Database is empty! Please run: python backend/scripts/setup_database.py")
            raise ValueError("Database is empty")

        logger.info("Initializing cache...")
        cache_service = CacheService(maxsize=1000, ttl=settings.cache_ttl)

        # Initialize search strategies
        logger.info("Initializing search strategies...")
        rag_strategy = RAGSearchStrategy(vector_store=vector_store_service, gemini_service=gemini_service)

        structured_strategy = StructuredQueryStrategy(database=database_service)

        hybrid_strategy = HybridFusionStrategy(rag_strategy=rag_strategy, structured_strategy=structured_strategy)

        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        orchestrator = QueryOrchestrator(
            rag_strategy=rag_strategy,
            structured_strategy=structured_strategy,
            hybrid_strategy=hybrid_strategy,
            gemini_service=gemini_service,
            cache_service=cache_service,
        )

        # 🌟 Initialize WOW Features Services 🌟
        logger.info("Initializing WOW features...")

        logger.info("- Visual Generator...")
        visual_generator = VisualGenerator()

        logger.info("- PDF Report Generator...")
        pdf_generator = PDFReportGenerator()

        logger.info("- Image Analyzer...")
        image_analyzer = ImageAnalyzer()

        logger.info("- Scenario Planner...")
        scenario_planner = ScenarioPlanner()

        logger.info("- Comparison Service...")
        comparison_service = ComparisonService()

        logger.info("- Analytics Service...")
        analytics_service = AnalyticsService(database_service)

        # Set dependencies for routes
        search.orchestrator_dependency = orchestrator
        interventions.database_dependency = database_service
        health.database_dependency = database_service
        health.vector_store_dependency = vector_store_service

        # Set WOW features dependencies
        wow_features.visual_generator_dependency = visual_generator
        wow_features.pdf_generator_dependency = pdf_generator
        wow_features.image_analyzer_dependency = image_analyzer

        advanced_features.scenario_planner_dependency = scenario_planner
        advanced_features.comparison_service_dependency = comparison_service
        advanced_features.analytics_service_dependency = analytics_service

        logger.info("✅ API initialized successfully with all WOW features!")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Road Safety Intervention API...")


# Include routers
app.include_router(search.router, prefix=settings.api_prefix)
app.include_router(interventions.router, prefix=settings.api_prefix)
app.include_router(health.router)

# 🌟 Include WOW Features Routers 🌟
app.include_router(wow_features.router, prefix=settings.api_prefix)
app.include_router(advanced_features.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint with WOW features info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "features": {
            "core": [
                "Multi-Strategy Search (RAG, Structured, Hybrid)",
                "AI-Powered Recommendations",
                "105+ Interventions from IRC Standards",
            ],
            "wow_features": [
                "🎨 Visual Sign/Marking Generator",
                "📄 PDF Report Generation",
                "📸 Image Analysis with Gemini Vision",
                "📊 Multi-Intervention Scenario Planning",
                "⚖️ Cost-Benefit Optimization",
                "📈 Interactive Comparison Tool",
                "📊 Analytics Dashboard",
                "🎯 Priority Matrix Visualization",
            ],
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "search": f"{settings.api_prefix}/search",
            "interventions": f"{settings.api_prefix}/interventions",
            "wow_features": f"{settings.api_prefix}/wow",
            "advanced": f"{settings.api_prefix}/advanced",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port, log_level=settings.log_level.lower())
