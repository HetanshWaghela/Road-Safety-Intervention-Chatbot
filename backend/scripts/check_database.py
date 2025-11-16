"""Quick script to check database status."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.app.config import settings
from backend.app.services.database import DatabaseService
from backend.app.services.vector_store import VectorStoreService
import json

print("=" * 60)
print("DATABASE STATUS CHECK")
print("=" * 60)

# Check JSON database
print("\n[1] Checking JSON database...")
data_path = settings.processed_data_dir / "interventions.json"
if data_path.exists():
    db = DatabaseService(data_path=data_path)
    count = len(db.df) if db.df is not None else 0
    print(f"✅ JSON database: {count} interventions")
    if count > 0:
        print(f"   Sample: {db.df.iloc[0]['problem']} - {db.df.iloc[0]['category']}")
else:
    print(f"❌ JSON database not found: {data_path}")

# Check vector store
print("\n[2] Checking vector store...")
try:
    vs = VectorStoreService(
        persist_directory=str(settings.chroma_dir),
        collection_name=settings.collection_name
    )
    collection = vs.get_collection()
    count = vs.count()
    print(f"✅ Vector store: {count} documents")
    if count == 0:
        print("⚠️  Vector store is EMPTY!")
        print("   Run: python backend/scripts/setup_database.py")
except Exception as e:
    print(f"❌ Vector store error: {e}")

print("\n" + "=" * 60)
print("STATUS CHECK COMPLETE")
print("=" * 60)

