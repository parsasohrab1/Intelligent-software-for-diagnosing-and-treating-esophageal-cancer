"""
Test script for MLOps features
"""
import sys
import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8001/api/v1"


def test_health():
    """Test API health"""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("  ✅ API is healthy")
            return True
        else:
            print(f"  ❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Could not connect to API: {str(e)}")
        return False


def test_messaging_status():
    """Test messaging queue status"""
    print("\n🔍 Testing messaging queue status...")
    try:
        response = requests.get(f"{BASE_URL}/mlops/messaging/status")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Queue type: {data.get('queue_type')}")
            print(f"  ✅ Connected: {data.get('connected')}")
            return True
        else:
            print(f"  ⚠️  Messaging status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ⚠️  Could not check messaging status: {str(e)}")
        return False


def test_publish_message():
    """Test publishing a message"""
    print("\n🔍 Testing message publishing...")
    try:
        payload = {
            "topic": "patient_data",
            "message": {
                "patient_id": "TEST001",
                "event_type": "test",
                "data": {"test": True}
            }
        }
        response = requests.post(
            f"{BASE_URL}/mlops/messaging/publish",
            json=payload
        )
        if response.status_code == 200:
            print("  ✅ Message published successfully")
            return True
        else:
            print(f"  ⚠️  Message publishing failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"  ⚠️  Could not publish message: {str(e)}")
        return False


def test_monitoring_status():
    """Test model monitoring status"""
    print("\n🔍 Testing model monitoring...")
    try:
        response = requests.get(f"{BASE_URL}/mlops/monitoring")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Monitoring endpoint accessible")
            print(f"  ✅ Active models: {data.get('count', 0)}")
            return True
        else:
            print(f"  ⚠️  Monitoring check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ⚠️  Could not check monitoring: {str(e)}")
        return False


def test_ab_testing():
    """Test A/B testing endpoints"""
    print("\n🔍 Testing A/B testing endpoints...")
    try:
        response = requests.get(f"{BASE_URL}/mlops/ab-testing")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ A/B testing endpoint accessible")
            print(f"  ✅ Active tests: {data.get('count', 0)}")
            return True
        else:
            print(f"  ⚠️  A/B testing check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ⚠️  Could not check A/B testing: {str(e)}")
        return False


def test_multi_modality():
    """Test multi-modality processing"""
    print("\n🔍 Testing multi-modality processing...")
    try:
        # Test text processing
        payload = {
            "text": "CT scan shows mass in esophagus. Tumor size: 2.5 cm.",
            "report_type": "radiology"
        }
        response = requests.post(
            f"{BASE_URL}/multi-modality/process-text",
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            print("  ✅ Text processing works")
            print(f"  ✅ Extracted entities: {len(data.get('extracted_entities', {}).get('pathologies', []))}")
            return True
        else:
            print(f"  ⚠️  Text processing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ⚠️  Could not test multi-modality: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("MLOps Features Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test API health
    results.append(("API Health", test_health()))
    
    # Test messaging
    results.append(("Messaging Status", test_messaging_status()))
    results.append(("Publish Message", test_publish_message()))
    
    # Test monitoring
    results.append(("Model Monitoring", test_monitoring_status()))
    
    # Test A/B testing
    results.append(("A/B Testing", test_ab_testing()))
    
    # Test multi-modality
    results.append(("Multi-Modality", test_multi_modality()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

