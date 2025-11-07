#!/usr/bin/env python3
"""
Machine Learning API Endpoints
Expose ML predictions via REST API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from datetime import datetime
import logging

from backend.ml.threat_predictor import ThreatPredictor

logger = logging.getLogger(__name__)

# Create router
ml_router = APIRouter(prefix="/ml", tags=["Machine Learning"])

# Global predictor instance
predictor = None


def get_predictor():
    """Get or create predictor instance"""
    global predictor
    if predictor is None:
        predictor = ThreatPredictor(
            neo4j_uri="bolt://neo4j.cyber-pi-intel.svc.cluster.local:7687",
            neo4j_user="neo4j",
            neo4j_password="cyber-pi-neo4j-2025"
        )
    return predictor


@ml_router.get("/predictions/cves")
async def predict_next_exploited_cves(limit: int = 20):
    """
    Predict which CVEs are likely to be exploited next
    
    Args:
        limit: Number of predictions to return
        
    Returns:
        List of CVE exploitation predictions
    """
    try:
        pred = get_predictor()
        predictions = pred.predict_next_exploited_cves(limit=limit)
        
        return {
            "status": "success",
            "predictions_count": len(predictions),
            "generated_at": datetime.utcnow().isoformat() + 'Z',
            "predictions": [
                {
                    "cve_id": p.cve_id,
                    "exploitation_probability": f"{p.exploitation_probability:.2%}",
                    "predicted_exploit_date": p.predicted_exploit_date.strftime("%Y-%m-%d"),
                    "confidence": f"{p.confidence:.1f}%",
                    "risk_factors": p.risk_factors,
                    "similar_exploited_cves": p.similar_exploited_cves
                }
                for p in predictions
            ]
        }
        
    except Exception as e:
        logger.error(f"CVE prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/predictions/actors")
async def predict_threat_actor_campaigns(actor_name: Optional[str] = None):
    """
    Predict threat actor next moves and campaigns
    
    Args:
        actor_name: Specific actor to predict (optional)
        
    Returns:
        List of threat actor predictions
    """
    try:
        pred = get_predictor()
        predictions = pred.predict_threat_actor_campaigns(actor_name=actor_name)
        
        return {
            "status": "success",
            "actor_filter": actor_name or "all",
            "predictions_count": len(predictions),
            "generated_at": datetime.utcnow().isoformat() + 'Z',
            "predictions": [
                {
                    "actor_name": p.actor_name,
                    "campaign_probability": f"{p.campaign_probability:.2%}",
                    "likely_next_targets": p.likely_next_targets,
                    "predicted_cves": p.predicted_cves,
                    "time_horizon": p.time_horizon
                }
                for p in predictions
            ]
        }
        
    except Exception as e:
        logger.error(f"Actor prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/predictions/industries")
async def predict_industry_risks():
    """
    Predict industry-specific cyber risks
    
    Returns:
        List of industry risk predictions
    """
    try:
        pred = get_predictor()
        predictions = pred.predict_industry_risks()
        
        return {
            "status": "success",
            "predictions_count": len(predictions),
            "generated_at": datetime.utcnow().isoformat() + 'Z',
            "predictions": [
                {
                    "industry": p.industry,
                    "risk_score": f"{p.risk_score:.1f}/100",
                    "top_threats": p.top_threats,
                    "emerging_cve_categories": p.emerging_cve_categories,
                    "recommended_actions": p.recommended_actions
                }
                for p in predictions
            ]
        }
        
    except Exception as e:
        logger.error(f"Industry prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/models/train")
async def train_ml_models():
    """
    Train/retrain ML models with latest data
    
    Returns:
        Training metrics and model performance
    """
    try:
        pred = get_predictor()
        metrics = pred.train_models()
        
        return {
            "status": "success",
            "trained_at": datetime.utcnow().isoformat() + 'Z',
            "model_performance": {
                "classification_accuracy": f"{metrics['classification_accuracy']:.2%}",
                "regression_mae_days": f"{metrics['regression_mae_days']:.1f}",
                "training_samples": metrics['training_samples']
            },
            "message": "ML models trained successfully"
        }
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/models/status")
async def get_model_status():
    """
    Get status of ML models
    
    Returns:
        Model training status and performance metrics
    """
    try:
        pred = get_predictor()
        
        if pred.models_trained:
            # Get training data stats
            if pred.training_data is not None:
                training_stats = {
                    "models_trained": True,
                    "training_samples": len(pred.training_data),
                    "last_trained": datetime.utcnow().isoformat() + 'Z',
                    "feature_count": len(pred.training_data.columns) if not pred.training_data.empty else 0
                }
            else:
                training_stats = {"models_trained": True, "training_samples": 0}
        else:
            training_stats = {"models_trained": False}
        
        return {
            "status": "success",
            "model_status": training_stats,
            "available_predictions": [
                "CVE exploitation likelihood",
                "Threat actor campaign patterns", 
                "Industry risk forecasting"
            ]
        }
        
    except Exception as e:
        logger.error(f"Model status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/report/comprehensive")
async def get_comprehensive_report():
    """
    Generate comprehensive ML predictions report
    
    Returns:
        Complete predictions report with all ML insights
    """
    try:
        pred = get_predictor()
        report = pred.generate_predictions_report()
        
        return {
            "status": "success",
            "report": report,
            "message": "Comprehensive ML predictions report generated"
        }
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/features/importance")
async def get_feature_importance():
    """
    Get feature importance from trained models
    
    Returns:
        Feature importance rankings
    """
    try:
        pred = get_predictor()
        
        if not pred.models_trained:
            raise HTTPException(status_code=400, detail="Models not trained yet")
        
        # Get feature importance from classifier
        feature_names = [
            'cvss_score', 'exploitation_count', 'actor_count', 'industry_count',
            'days_since_publish', 'days_since_last_exploit', 'description_length',
            'has_remote_code', 'has_privilege_escalation', 'has_memory_corruption',
            'has_apt_actor', 'has_ransomware_actor', 'targets_critical_infra'
        ]
        
        importance = pred.cve_classifier.feature_importances_
        
        # Sort by importance
        feature_importance = sorted(
            zip(feature_names, importance),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "status": "success",
            "feature_importance": [
                {
                    "feature": name,
                    "importance": f"{score:.3f}",
                    "percentage": f"{score * 100:.1f}%"
                }
                for name, score in feature_importance
            ]
        }
        
    except Exception as e:
        logger.error(f"Feature importance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
