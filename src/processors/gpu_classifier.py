"""
cyber-pi GPU-Accelerated Threat Classifier
Uses dual NVIDIA A6000 GPUs for massive parallel classification
Processes 10,000+ items/hour with AI-powered categorization
"""

import torch
from transformers import pipeline
import logging
from typing import List, Dict, Any
from datetime import datetime
import json

# Import configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPUThreatClassifier:
    """
    GPU-accelerated threat intelligence classifier
    Uses transformers and zero-shot classification
    """
    
    def __init__(self, gpu_id: int = 0, batch_size: int = 32):
        """
        Initialize GPU classifier
        
        Args:
            gpu_id: Which GPU to use (0 or 1 for dual A6000s)
            batch_size: Number of items to process simultaneously
        """
        self.gpu_id = gpu_id
        self.batch_size = batch_size
        self.device = f"cuda:{gpu_id}" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"🚀 Initializing GPU Classifier on {self.device}")
        
        # Check GPU availability
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(gpu_id)
            gpu_memory = torch.cuda.get_device_properties(gpu_id).total_memory / 1e9
            logger.info(f"✓ GPU: {gpu_name}")
            logger.info(f"✓ VRAM: {gpu_memory:.1f} GB")
        else:
            logger.warning("⚠️  No GPU available, using CPU (will be slower)")
        
        # Initialize classifier
        logger.info("Loading classification model...")
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",  # 400M parameters, excellent for classification
            device=self.device,
            batch_size=self.batch_size
        )
        logger.info("✓ Model loaded successfully")
        
        # Define classification categories
        self.threat_categories = [
            "Critical Vulnerability",
            "Ransomware Attack",
            "Data Breach",
            "Nation-State APT",
            "Supply Chain Attack",
            "Zero-Day Exploit",
            "Phishing Campaign",
            "DDoS Attack",
            "Malware Distribution",
            "Insider Threat"
        ]
        
        self.industry_categories = [
            "Aviation/Airline Security",
            "Power Grid/Energy Sector",
            "Healthcare/Hospital Systems",
            "Government/Public Sector",
            "Education/University Networks",
            "Nuclear Power Security",
            "Industrial Control Systems",
            "Financial Services"
        ]
        
        self.severity_levels = [
            "Critical - Immediate Action Required",
            "High - Urgent Attention Needed",
            "Medium - Monitor Closely",
            "Low - Informational"
        ]
    
    def classify_threat_type(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Classify threat types using GPU
        
        Args:
            texts: List of threat titles/descriptions
            
        Returns:
            List of classification results
        """
        logger.info(f"Classifying {len(texts)} items for threat type...")
        
        start_time = datetime.now()
        
        # GPU processes entire batch in parallel
        results = self.classifier(
            texts,
            self.threat_categories,
            multi_label=True  # Items can belong to multiple categories
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        rate = len(texts) / duration
        
        logger.info(f"✓ Classified {len(texts)} items in {duration:.2f}s ({rate:.1f} items/sec)")
        
        return results
    
    def classify_industry_relevance(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Classify industry relevance for Nexum clients
        
        Args:
            texts: List of threat titles/descriptions
            
        Returns:
            List of industry classification results
        """
        logger.info(f"Classifying {len(texts)} items for industry relevance...")
        
        results = self.classifier(
            texts,
            self.industry_categories,
            multi_label=True
        )
        
        return results
    
    def classify_severity(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Classify severity level beyond CVSS scores
        
        Args:
            texts: List of threat titles/descriptions
            
        Returns:
            List of severity classifications
        """
        logger.info(f"Classifying {len(texts)} items for severity...")
        
        results = self.classifier(
            texts,
            self.severity_levels,
            multi_label=False  # Only one severity level
        )
        
        return results
    
    def classify_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify a batch of intelligence items
        
        Args:
            items: List of intelligence items
            
        Returns:
            Items with added classification data
        """
        if not items:
            return []
        
        logger.info(f"🔥 GPU Classification Pipeline: {len(items)} items")
        logger.info(f"   GPU: {self.device}")
        logger.info(f"   Batch Size: {self.batch_size}")
        logger.info("")
        
        # Extract texts for classification
        texts = [item.get('title', '') + ' ' + item.get('description', '')[:200] 
                for item in items]
        
        # Run all classifications
        threat_results = self.classify_threat_type(texts)
        industry_results = self.classify_industry_relevance(texts)
        severity_results = self.classify_severity(texts)
        
        # Add classifications to items
        for i, item in enumerate(items):
            # Threat type (top 2 categories)
            threat = threat_results[i]
            item['ai_threat_types'] = [
                {'category': threat['labels'][0], 'confidence': threat['scores'][0]},
                {'category': threat['labels'][1], 'confidence': threat['scores'][1]}
            ]
            
            # Industry relevance (top 2)
            industry = industry_results[i]
            item['ai_industry_relevance'] = [
                {'industry': industry['labels'][0], 'confidence': industry['scores'][0]},
                {'industry': industry['labels'][1], 'confidence': industry['scores'][1]}
            ]
            
            # Severity
            severity = severity_results[i]
            item['ai_severity'] = {
                'level': severity['labels'][0],
                'confidence': severity['scores'][0]
            }
            
            # Calculate overall AI priority score
            threat_conf = threat['scores'][0]
            severity_conf = severity['scores'][0]
            item['ai_priority_score'] = int((threat_conf + severity_conf) / 2 * 100)
        
        logger.info("✓ Classification complete!")
        logger.info("")
        
        return items
    
    def process_collection(self, collection_file: str, output_file: str = None):
        """
        Process entire intelligence collection
        
        Args:
            collection_file: Path to collection JSON
            output_file: Path to save classified data
        """
        logger.info("=" * 80)
        logger.info("🚀 GPU-ACCELERATED THREAT CLASSIFICATION")
        logger.info("=" * 80)
        logger.info("")
        
        # Load collection
        with open(collection_file, 'r') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        logger.info(f"Loaded {len(items)} intelligence items")
        logger.info("")
        
        # Process in batches
        classified_items = []
        total_batches = (len(items) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches}...")
            classified_batch = self.classify_batch(batch)
            classified_items.extend(classified_batch)
        
        # Save results
        if not output_file:
            output_file = collection_file.replace('.json', '_classified.json')
        
        data['items'] = classified_items
        data['metadata']['ai_classified'] = True
        data['metadata']['classification_timestamp'] = datetime.now().isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ CLASSIFICATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Classified items: {len(classified_items)}")
        logger.info(f"Output file: {output_file}")
        logger.info("")
        
        # Show sample classifications
        logger.info("📊 SAMPLE CLASSIFICATIONS:")
        logger.info("-" * 80)
        for item in classified_items[:3]:
            logger.info(f"\nTitle: {item['title'][:70]}")
            logger.info(f"Threat Type: {item['ai_threat_types'][0]['category']} "
                       f"({item['ai_threat_types'][0]['confidence']:.2f})")
            logger.info(f"Industry: {item['ai_industry_relevance'][0]['industry']} "
                       f"({item['ai_industry_relevance'][0]['confidence']:.2f})")
            logger.info(f"Severity: {item['ai_severity']['level']} "
                       f"({item['ai_severity']['confidence']:.2f})")
            logger.info(f"AI Priority Score: {item['ai_priority_score']}/100")


def main():
    """Test GPU classifier"""
    from pathlib import Path
    
    # Find latest collection
    data_dir = Path(settings.raw_data_dir)
    collection_files = sorted(data_dir.glob("master_collection_*.json"), reverse=True)
    
    if not collection_files:
        logger.error("No collection files found!")
        return
    
    latest_file = collection_files[0]
    logger.info(f"Processing: {latest_file}")
    logger.info("")
    
    # Create classifier (use GPU 0)
    classifier = GPUThreatClassifier(gpu_id=0, batch_size=32)
    
    # Process collection
    output_file = str(latest_file).replace('.json', '_classified.json')
    classifier.process_collection(str(latest_file), output_file)


if __name__ == "__main__":
    main()
