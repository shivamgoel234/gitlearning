"""
Business logic for Dashboard Service.

Aggregates data from all microservices for visualization.
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis
import httpx

from .config import settings
from .models import DashboardSummary, EquipmentOverview, EquipmentDetail

logger = logging.getLogger(__name__)


class DashboardService:
    """Service class for dashboard data aggregation."""
    
    def __init__(self):
        """Initialize service with Redis and HTTP client."""
        self.redis_client: Optional[redis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None
    
    async def init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}", exc_info=True)
            raise
    
    async def init_http_client(self) -> None:
        """Initialize HTTP client for service communication."""
        self.http_client = httpx.AsyncClient(timeout=10.0)
        logger.info("HTTP client initialized")
    
    async def close_redis(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def close_http_client(self) -> None:
        """Close HTTP client."""
        if self.http_client:
            await self.http_client.aclose()
            logger.info("HTTP client closed")
    
    async def get_dashboard_summary(self, db: AsyncSession) -> DashboardSummary:
        """
        Get dashboard summary with aggregated statistics.
        
        Args:
            db: Database session
            
        Returns:
            DashboardSummary with system-wide statistics
        """
        try:
            # Get total equipment count
            result = await db.execute(text(
                "SELECT COUNT(DISTINCT equipment_id) FROM sensor_data"
            ))
            total_equipment = result.scalar() or 0
            
            # Get critical alerts count
            result = await db.execute(text(
                "SELECT COUNT(*) FROM alerts WHERE severity = 'CRITICAL' AND acknowledged = false"
            ))
            critical_alerts = result.scalar() or 0
            
            # Get pending maintenance count
            result = await db.execute(text(
                "SELECT COUNT(*) FROM maintenance_schedules WHERE completed = false"
            ))
            pending_maintenance = result.scalar() or 0
            
            # Get average health score
            result = await db.execute(text(
                """
                SELECT AVG(health_score) 
                FROM (
                    SELECT DISTINCT ON (equipment_id) equipment_id, health_score
                    FROM predictions
                    ORDER BY equipment_id, timestamp DESC
                ) AS latest_predictions
                """
            ))
            avg_health = result.scalar() or 0.0
            
            # Get equipment by status
            equipment_by_status = await self._get_equipment_by_status(db)
            
            # Get recent alerts
            recent_alerts = await self._get_recent_alerts(db, limit=5)
            
            return DashboardSummary(
                total_equipment=total_equipment,
                critical_alerts=critical_alerts,
                pending_maintenance=pending_maintenance,
                average_health_score=round(avg_health, 1),
                equipment_by_status=equipment_by_status,
                recent_alerts=recent_alerts,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}", exc_info=True)
            raise
    
    async def get_equipment_overview(self, db: AsyncSession) -> List[EquipmentOverview]:
        """
        Get overview of all equipment.
        
        Args:
            db: Database session
            
        Returns:
            List of EquipmentOverview objects
        """
        try:
            query = text("""
                WITH latest_data AS (
                    SELECT DISTINCT ON (equipment_id)
                        equipment_id,
                        timestamp AS last_reading
                    FROM sensor_data
                    ORDER BY equipment_id, timestamp DESC
                ),
                latest_predictions AS (
                    SELECT DISTINCT ON (equipment_id)
                        equipment_id,
                        health_score,
                        severity
                    FROM predictions
                    ORDER BY equipment_id, timestamp DESC
                ),
                alert_counts AS (
                    SELECT equipment_id, COUNT(*) as alert_count
                    FROM alerts
                    WHERE acknowledged = false
                    GROUP BY equipment_id
                ),
                maintenance_status AS (
                    SELECT equipment_id, COUNT(*) > 0 as has_maintenance
                    FROM maintenance_schedules
                    WHERE completed = false
                    GROUP BY equipment_id
                )
                SELECT 
                    ld.equipment_id,
                    COALESCE(lp.health_score, 0) as health_score,
                    COALESCE(lp.severity, 'UNKNOWN') as status,
                    ld.last_reading,
                    COALESCE(ac.alert_count, 0) as alert_count,
                    COALESCE(ms.has_maintenance, false) as maintenance_scheduled
                FROM latest_data ld
                LEFT JOIN latest_predictions lp ON ld.equipment_id = lp.equipment_id
                LEFT JOIN alert_counts ac ON ld.equipment_id = ac.equipment_id
                LEFT JOIN maintenance_status ms ON ld.equipment_id = ms.equipment_id
                ORDER BY ld.equipment_id
            """)
            
            result = await db.execute(query)
            rows = result.fetchall()
            
            return [
                EquipmentOverview(
                    equipment_id=row[0],
                    health_score=float(row[1]),
                    status=row[2],
                    last_reading=row[3],
                    alert_count=int(row[4]),
                    maintenance_scheduled=bool(row[5])
                )
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Failed to get equipment overview: {e}", exc_info=True)
            raise
    
    async def get_equipment_detail(
        self,
        equipment_id: str,
        db: AsyncSession
    ) -> Optional[EquipmentDetail]:
        """
        Get detailed information for specific equipment.
        
        Args:
            equipment_id: Equipment identifier
            db: Database session
            
        Returns:
            EquipmentDetail with comprehensive information
        """
        try:
            equipment_id = equipment_id.upper()
            
            # Get latest sensor data
            latest_sensor = await self._get_latest_sensor_data(equipment_id, db)
            
            # Get latest prediction
            latest_prediction = await self._get_latest_prediction(equipment_id, db)
            
            # Get active alerts
            active_alerts = await self._get_active_alerts(equipment_id, db)
            
            # Get maintenance schedule
            maintenance = await self._get_maintenance_schedule(equipment_id, db)
            
            # Get trend data (last 24 hours)
            trend_data = await self._get_trend_data(equipment_id, db)
            
            if not latest_sensor:
                return None
            
            health_score = latest_prediction.get("health_score", 0) if latest_prediction else 0
            status = latest_prediction.get("severity", "UNKNOWN") if latest_prediction else "UNKNOWN"
            
            return EquipmentDetail(
                equipment_id=equipment_id,
                health_score=health_score,
                status=status,
                latest_sensor_data=latest_sensor,
                latest_prediction=latest_prediction,
                active_alerts=active_alerts,
                maintenance_schedule=maintenance,
                trend_data=trend_data
            )
            
        except Exception as e:
            logger.error(f"Failed to get equipment detail: {e}", exc_info=True)
            raise
    
    async def _get_equipment_by_status(self, db: AsyncSession) -> Dict[str, int]:
        """Get equipment count by health status."""
        query = text("""
            WITH latest_predictions AS (
                SELECT DISTINCT ON (equipment_id)
                    equipment_id, severity
                FROM predictions
                ORDER BY equipment_id, timestamp DESC
            )
            SELECT severity, COUNT(*) as count
            FROM latest_predictions
            GROUP BY severity
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        return {row[0]: int(row[1]) for row in rows}
    
    async def _get_recent_alerts(self, db: AsyncSession, limit: int = 5) -> List[dict]:
        """Get recent alerts."""
        query = text("""
            SELECT equipment_id, severity, message, timestamp
            FROM alerts
            WHERE acknowledged = false
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        
        result = await db.execute(query, {"limit": limit})
        rows = result.fetchall()
        
        return [
            {
                "equipment_id": row[0],
                "severity": row[1],
                "message": row[2],
                "timestamp": row[3].isoformat()
            }
            for row in rows
        ]
    
    async def _get_latest_sensor_data(
        self,
        equipment_id: str,
        db: AsyncSession
    ) -> Optional[dict]:
        """Get latest sensor data for equipment."""
        query = text("""
            SELECT temperature, vibration, pressure, humidity, voltage, timestamp
            FROM sensor_data
            WHERE equipment_id = :equipment_id
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        result = await db.execute(query, {"equipment_id": equipment_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return {
            "temperature": float(row[0]),
            "vibration": float(row[1]),
            "pressure": float(row[2]),
            "humidity": float(row[3]) if row[3] else None,
            "voltage": float(row[4]) if row[4] else None,
            "timestamp": row[5].isoformat()
        }
    
    async def _get_latest_prediction(
        self,
        equipment_id: str,
        db: AsyncSession
    ) -> Optional[dict]:
        """Get latest prediction for equipment."""
        query = text("""
            SELECT failure_probability, severity, health_score, 
                   days_until_failure, confidence, timestamp
            FROM predictions
            WHERE equipment_id = :equipment_id
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        result = await db.execute(query, {"equipment_id": equipment_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        return {
            "failure_probability": float(row[0]),
            "severity": row[1],
            "health_score": float(row[2]),
            "days_until_failure": int(row[3]),
            "confidence": row[4],
            "timestamp": row[5].isoformat()
        }
    
    async def _get_active_alerts(
        self,
        equipment_id: str,
        db: AsyncSession
    ) -> List[dict]:
        """Get active alerts for equipment."""
        query = text("""
            SELECT id, severity, message, timestamp
            FROM alerts
            WHERE equipment_id = :equipment_id AND acknowledged = false
            ORDER BY timestamp DESC
        """)
        
        result = await db.execute(query, {"equipment_id": equipment_id})
        rows = result.fetchall()
        
        return [
            {
                "alert_id": row[0],
                "severity": row[1],
                "message": row[2],
                "timestamp": row[3].isoformat()
            }
            for row in rows
        ]
    
    async def _get_maintenance_schedule(
        self,
        equipment_id: str,
        db: AsyncSession
    ) -> List[dict]:
        """Get maintenance schedule for equipment."""
        query = text("""
            SELECT id, scheduled_date, priority, task_type, 
                   description, status, completed
            FROM maintenance_schedules
            WHERE equipment_id = :equipment_id
            ORDER BY scheduled_date
        """)
        
        result = await db.execute(query, {"equipment_id": equipment_id})
        rows = result.fetchall()
        
        return [
            {
                "schedule_id": row[0],
                "scheduled_date": row[1].isoformat(),
                "priority": row[2],
                "task_type": row[3],
                "description": row[4],
                "status": row[5],
                "completed": bool(row[6])
            }
            for row in rows
        ]
    
    async def _get_trend_data(
        self,
        equipment_id: str,
        db: AsyncSession
    ) -> List[dict]:
        """Get trend data for equipment (last 24 hours)."""
        query = text("""
            SELECT timestamp, temperature, vibration, pressure
            FROM sensor_data
            WHERE equipment_id = :equipment_id
                AND timestamp >= NOW() - INTERVAL '24 hours'
            ORDER BY timestamp
        """)
        
        result = await db.execute(query, {"equipment_id": equipment_id})
        rows = result.fetchall()
        
        return [
            {
                "timestamp": row[0].isoformat(),
                "temperature": float(row[1]),
                "vibration": float(row[2]),
                "pressure": float(row[3])
            }
            for row in rows
        ]


# Global service instance
dashboard_service = DashboardService()
