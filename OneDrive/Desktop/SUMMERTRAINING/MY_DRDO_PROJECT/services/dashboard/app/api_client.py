"""
HTTP client to fetch data from other microservices.

Provides clients for Alert & Maintenance service and ML Prediction service.
"""

import requests
import logging
from typing import List, Dict, Optional
from .config import settings

logger = logging.getLogger(__name__)


class AlertServiceClient:
    """
    Client for Alert & Maintenance service.
    
    Fetches active alerts, maintenance tasks, and statistics.
    """
    
    def __init__(self, base_url: str = settings.ALERT_SERVICE_URL):
        """
        Initialize alert service client.
        
        Args:
            base_url: Base URL of alert service (default from settings)
        """
        self.base_url = base_url
        self.timeout = settings.API_TIMEOUT
    
    def get_active_alerts(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Fetch active alerts from alert service.
        
        Args:
            limit: Maximum number of alerts to fetch (default from settings)
        
        Returns:
            List of alert dictionaries or empty list on error
        """
        if limit is None:
            limit = settings.MAX_ALERTS_DISPLAY
        
        try:
            logger.info(f"Fetching active alerts from {self.base_url}")
            
            response = requests.get(
                f"{self.base_url}/api/v1/alerts/active",
                timeout=self.timeout,
                params={"limit": limit}
            )
            
            if response.status_code == 200:
                alerts = response.json()
                logger.info(f"✓ Fetched {len(alerts)} active alerts")
                return alerts
            else:
                logger.warning(
                    f"Alert service returned status {response.status_code}: {response.text}"
                )
                return []
                
        except requests.Timeout:
            logger.error(f"Alert service timeout after {self.timeout}s")
            return []
        except requests.ConnectionError:
            logger.error(f"Cannot connect to alert service at {self.base_url}")
            return []
        except requests.RequestException as e:
            logger.error(f"Alert service request error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching alerts: {e}", exc_info=True)
            return []
    
    def get_alerts_by_severity(self, severity: str) -> List[Dict]:
        """
        Get alerts filtered by severity level.
        
        Args:
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        
        Returns:
            List of alert dictionaries or empty list on error
        """
        try:
            logger.info(f"Fetching {severity} alerts")
            
            response = requests.get(
                f"{self.base_url}/api/v1/alerts/active",
                timeout=self.timeout,
                params={"severity": severity, "limit": settings.MAX_ALERTS_DISPLAY}
            )
            
            if response.status_code == 200:
                alerts = response.json()
                logger.info(f"✓ Fetched {len(alerts)} {severity} alerts")
                return alerts
            else:
                logger.warning(f"Failed to fetch {severity} alerts")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching {severity} alerts: {e}")
            return []
    
    def health_check(self) -> bool:
        """
        Check if alert service is available.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception:
            return False


class MLServiceClient:
    """
    Client for ML Prediction service.
    
    Fetches predictions and model information.
    """
    
    def __init__(self, base_url: str = settings.ML_SERVICE_URL):
        """
        Initialize ML service client.
        
        Args:
            base_url: Base URL of ML service (default from settings)
        """
        self.base_url = base_url
        self.timeout = settings.API_TIMEOUT
    
    def health_check(self) -> bool:
        """
        Check if ML service is available.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception:
            return False
