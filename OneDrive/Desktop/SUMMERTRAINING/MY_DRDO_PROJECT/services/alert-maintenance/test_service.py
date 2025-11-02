#!/usr/bin/env python
"""
Simple test script to verify Alert & Maintenance service is working.

Run this after starting the service to verify all endpoints.
"""

import sys
import json
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("❌ requests library not found. Install with: pip install requests")
    sys.exit(1)

# Configuration
BASE_URL = "http://localhost:8003"
TIMEOUT = 5

def print_test(name: str):
    """Print test name."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)

def print_success(message: str):
    """Print success message."""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message."""
    print(f"❌ {message}")

def print_result(response):
    """Pretty print response."""
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_health_check():
    """Test health check endpoint."""
    print_test("Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Service is healthy: {data.get('service')} v{data.get('version')}")
            print_result(response)
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            print_result(response)
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to connect to service: {e}")
        print("Make sure the service is running on http://localhost:8003")
        return False

def test_generate_alert():
    """Test alert generation endpoint."""
    print_test("Generate Alert (HIGH severity)")
    
    try:
        # Test with high sensor values (should create alert)
        params = {
            "equipment_id": "RADAR-TEST-001",
            "temperature": 95.5,
            "vibration": 0.85,
            "pressure": 4.2,
            "humidity": 75.0,
            "voltage": 245.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/alerts/generate",
            params=params,
            timeout=TIMEOUT
        )
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"Alert created successfully!")
            print(f"Alert ID: {data.get('id')}")
            print(f"Severity: {data.get('severity')}")
            print(f"Failure Probability: {data.get('failure_probability')}")
            print_result(response)
            return data.get('id')
        elif response.status_code == 404:
            print("ℹ️  No alert created (severity too low - this is OK for testing)")
            print_result(response)
            return None
        else:
            print_error(f"Alert generation failed with status {response.status_code}")
            print_result(response)
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to generate alert: {e}")
        return None

def test_get_active_alerts():
    """Test get active alerts endpoint."""
    print_test("Get Active Alerts")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/alerts/active",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {len(data)} active alerts")
            print_result(response)
            return True
        else:
            print_error(f"Failed to get alerts with status {response.status_code}")
            print_result(response)
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to get alerts: {e}")
        return False

def test_schedule_maintenance():
    """Test schedule maintenance endpoint."""
    print_test("Schedule Maintenance Task")
    
    try:
        # Schedule maintenance for 7 days from now
        scheduled_date = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
        
        payload = {
            "equipment_id": "RADAR-TEST-001",
            "task_type": "PREVENTIVE",
            "priority": "HIGH",
            "scheduled_date": scheduled_date,
            "title": "Test maintenance task",
            "description": "Created by test script",
            "estimated_duration_hours": 4,
            "cost_estimate": 5000.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/maintenance/schedule",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"Maintenance task scheduled successfully!")
            print(f"Task ID: {data.get('id')}")
            print(f"Type: {data.get('task_type')}")
            print(f"Priority: {data.get('priority')}")
            print_result(response)
            return True
        else:
            print_error(f"Failed to schedule maintenance with status {response.status_code}")
            print_result(response)
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Failed to schedule maintenance: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ALERT & MAINTENANCE SERVICE - TEST SUITE")
    print("="*60)
    print(f"Testing service at: {BASE_URL}")
    print("="*60)
    
    results = {
        "health_check": False,
        "generate_alert": False,
        "get_active_alerts": False,
        "schedule_maintenance": False
    }
    
    # Test 1: Health Check
    results["health_check"] = test_health_check()
    
    if not results["health_check"]:
        print("\n" + "="*60)
        print("❌ TESTS FAILED - Service is not running or not accessible")
        print("="*60)
        sys.exit(1)
    
    # Test 2: Generate Alert
    alert_id = test_generate_alert()
    results["generate_alert"] = alert_id is not None
    
    # Test 3: Get Active Alerts
    results["get_active_alerts"] = test_get_active_alerts()
    
    # Test 4: Schedule Maintenance
    results["schedule_maintenance"] = test_schedule_maintenance()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_status in results.items():
        status = "✅ PASS" if passed_status else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Service is working correctly.")
        print("\nNext steps:")
        print("1. Open http://localhost:8003/docs for interactive API documentation")
        print("2. Check ENDPOINTS_QUICK_TEST.md for more testing examples")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
