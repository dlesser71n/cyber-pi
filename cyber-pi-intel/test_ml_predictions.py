#!/usr/bin/env python3
"""
Test ML Predictions
Test the machine learning threat predictor
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_ml_endpoints():
    """Test all ML endpoints"""
    print("🧠 TESTING ML PREDICTIONS")
    print("="*60)
    
    # Test 1: Model Status
    print("\n1. Checking ML Model Status...")
    try:
        response = requests.get(f"{BASE_URL}/ml/models/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Models trained: {data['model_status']['models_trained']}")
            print(f"✅ Training samples: {data['model_status'].get('training_samples', 'N/A')}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Train Models
    print("\n2. Training ML Models...")
    try:
        response = requests.get(f"{BASE_URL}/ml/models/train")
        if response.status_code == 200:
            data = response.json()
            perf = data['model_performance']
            print(f"✅ Classification accuracy: {perf['classification_accuracy']}")
            print(f"✅ Regression MAE: {perf['regression_mae_days']} days")
            print(f"✅ Training samples: {perf['training_samples']}")
        else:
            print(f"❌ Training failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: CVE Predictions
    print("\n3. Predicting Next Exploited CVEs...")
    try:
        response = requests.get(f"{BASE_URL}/ml/predictions/cves?limit=5")
        if response.status_code == 200:
            data = response.json()
            predictions = data['predictions']
            print(f"✅ Generated {len(predictions)} CVE predictions:")
            for i, pred in enumerate(predictions[:3], 1):
                print(f"   {i}. {pred['cve_id']}: {pred['exploitation_probability']} chance")
                print(f"      Risk factors: {', '.join(pred['risk_factors'][:2])}")
        else:
            print(f"❌ CVE prediction failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Actor Predictions
    print("\n4. Predicting Threat Actor Campaigns...")
    try:
        response = requests.get(f"{BASE_URL}/ml/predictions/actors")
        if response.status_code == 200:
            data = response.json()
            predictions = data['predictions']
            print(f"✅ Generated {len(predictions)} actor predictions:")
            for i, pred in enumerate(predictions[:3], 1):
                print(f"   {i}. {pred['actor_name']}: {pred['campaign_probability']} campaign probability")
                print(f"      Likely targets: {', '.join(pred['likely_next_targets'][:2])}")
        else:
            print(f"❌ Actor prediction failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Industry Risk Predictions
    print("\n5. Predicting Industry Risks...")
    try:
        response = requests.get(f"{BASE_URL}/ml/predictions/industries")
        if response.status_code == 200:
            data = response.json()
            predictions = data['predictions']
            print(f"✅ Generated {len(predictions)} industry risk predictions:")
            for i, pred in enumerate(predictions[:3], 1):
                print(f"   {i}. {pred['industry']}: {pred['risk_score']} risk score")
                print(f"      Top threats: {', '.join(pred['top_threats'][:2])}")
        else:
            print(f"❌ Industry prediction failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Feature Importance
    print("\n6. Getting Feature Importance...")
    try:
        response = requests.get(f"{BASE_URL}/ml/features/importance")
        if response.status_code == 200:
            data = response.json()
            importance = data['feature_importance']
            print(f"✅ Top 5 most important features:")
            for i, feat in enumerate(importance[:5], 1):
                print(f"   {i}. {feat['feature']}: {feat['percentage']}")
        else:
            print(f"❌ Feature importance failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 7: Comprehensive Report
    print("\n7. Generating Comprehensive Report...")
    try:
        response = requests.get(f"{BASE_URL}/ml/report/comprehensive")
        if response.status_code == 200:
            data = response.json()
            report = data['report']
            print(f"✅ Generated comprehensive report at {report['generated_at']}")
            print(f"   CVE predictions: {len(report['predictions']['next_exploited_cves'])}")
            print(f"   Actor predictions: {len(report['predictions']['threat_actor_campaigns'])}")
            print(f"   Industry predictions: {len(report['predictions']['industry_risks'])}")
        else:
            print(f"❌ Report generation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("🎉 ML PREDICTIONS TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_ml_endpoints()
