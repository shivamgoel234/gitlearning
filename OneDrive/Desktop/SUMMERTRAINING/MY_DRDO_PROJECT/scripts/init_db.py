"""
Database initialization script for DRDO Equipment Maintenance Prediction System.

Creates all necessary tables across all microservices.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def init_all_databases():
    """Initialize databases for all services."""
    print("🔧 Initializing databases for all services...")
    
    # Service 1: Sensor Ingestion
    try:
        print("\n📊 Initializing sensor-ingestion database...")
        sys.path.insert(0, str(project_root / "sensor-data-ingestion-service"))
        from app.database import init_db as init_sensor_db
        await init_sensor_db()
        print("✅ Sensor ingestion database initialized")
    except Exception as e:
        print(f"❌ Failed to initialize sensor ingestion database: {e}")
    
    print("\n✨ Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_all_databases())
