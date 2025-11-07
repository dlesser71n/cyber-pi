"""
cyber-pi Llama 3.1 Classifier
Uses local Ollama for superior cybersecurity classification
Much better than generic BART model
"""

import requests
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import asyncio
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LlamaClassifier:
    """
    Uses Llama 3.1 via Ollama for cybersecurity classification
    Better accuracy than generic models
    """
    
    def __init__(self, model: str = "llama3.1:8b", ollama_url: str = "http://localhost:11434"):
        self.model = model
        self.ollama_url = ollama_url
        self.api_endpoint = f"{ollama_url}/api/generate"
        
        logger.info(f"🦙 Initializing Llama Classifier")
        logger.info(f"   Model: {model}")
        logger.info(f"   Ollama: {ollama_url}")
        
        # Check if model is available
        self._check_model()
    
    def _check_model(self):
        """Check if Ollama model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            
            if self.model in model_names or self.model.split(':')[0] in [m.split(':')[0] for m in model_names]:
                logger.info(f"✓ Model {self.model} is available")
            else:
                logger.warning(f"⚠️  Model {self.model} not found. Available: {model_names}")
                logger.warning(f"   Run: ollama pull {self.model}")
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {e}")
    
    def classify_threat(self, text: str) -> Dict[str, Any]:
        """
        Classify a single threat using Llama
        
        Args:
            text: Threat title/description
            
        Returns:
            Classification results
        """
        prompt = f"""You are a cybersecurity threat intelligence analyst. Analyze this threat and provide classifications.

Threat: {text}

Provide your analysis in JSON format with these fields:
1. threat_types: List of applicable threat types from [Critical Vulnerability, Ransomware Attack, Data Breach, Nation-State APT, Supply Chain Attack, Zero-Day Exploit, Phishing Campaign, DDoS Attack, Malware Distribution, Insider Threat]
2. industries: List of most relevant industries from [Aviation/Airline Security, Power Grid/Energy Sector, Healthcare/Hospital Systems, Government/Public Sector, Education/University Networks, Nuclear Power Security, Industrial Control Systems, Financial Services]
3. severity: One of [Critical, High, Medium, Low]
4. priority_score: Number from 0-100
5. reasoning: Brief explanation

Respond ONLY with valid JSON, no other text."""

        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            
            result = response.json()
            response_text = result.get('response', '{}')
            
            # Parse JSON response
            classification = json.loads(response_text)
            
            return classification
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                "threat_types": ["Unknown"],
                "industries": ["Unknown"],
                "severity": "Medium",
                "priority_score": 50,
                "reasoning": f"Error: {str(e)}"
            }
    
    async def classify_batch_async(self, texts: List[str], max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """
        Classify multiple threats concurrently
        
        Args:
            texts: List of threat texts
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of classifications
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def classify_one(text: str) -> Dict[str, Any]:
            async with semaphore:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, self.classify_threat, text)
        
        tasks = [classify_one(text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        return results
    
    def process_collection(self, collection_file: str, output_file: str = None, batch_size: int = 5):
        """
        Process entire collection with Llama classification
        
        Args:
            collection_file: Input JSON file
            output_file: Output JSON file
            batch_size: Concurrent requests
        """
        logger.info("=" * 80)
        logger.info("🦙 LLAMA 3.1 THREAT CLASSIFICATION")
        logger.info("=" * 80)
        logger.info("")
        
        # Load collection
        with open(collection_file, 'r') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        logger.info(f"Loaded {len(items)} items")
        logger.info(f"Concurrent requests: {batch_size}")
        logger.info("")
        
        # Process in batches
        classified_items = []
        start_time = datetime.now()
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(items) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches}...")
            
            # Extract texts
            texts = [item.get('title', '') + ' ' + item.get('description', '')[:200] 
                    for item in batch]
            
            # Classify batch
            results = asyncio.run(self.classify_batch_async(texts, max_concurrent=batch_size))
            
            # Add classifications to items
            for item, classification in zip(batch, results):
                item['llama_classification'] = classification
                item['llama_priority_score'] = classification.get('priority_score', 50)
            
            classified_items.extend(batch)
            
            # Progress
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = len(classified_items) / elapsed if elapsed > 0 else 0
            logger.info(f"  Processed {len(classified_items)}/{len(items)} ({rate:.1f} items/sec)")
        
        # Save results
        if not output_file:
            output_file = collection_file.replace('.json', '_llama_classified.json')
        
        data['items'] = classified_items
        data['metadata']['llama_classified'] = True
        data['metadata']['llama_model'] = self.model
        data['metadata']['classification_timestamp'] = datetime.now().isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ LLAMA CLASSIFICATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total items: {len(classified_items)}")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info(f"Rate: {len(classified_items)/duration:.1f} items/sec")
        logger.info(f"Output: {output_file}")
        logger.info("")
        
        # Show samples
        logger.info("📊 SAMPLE CLASSIFICATIONS:")
        logger.info("-" * 80)
        for item in classified_items[:3]:
            llama = item['llama_classification']
            logger.info(f"\nTitle: {item['title'][:70]}")
            logger.info(f"Threat Types: {', '.join(llama.get('threat_types', []))}")
            logger.info(f"Industries: {', '.join(llama.get('industries', []))}")
            logger.info(f"Severity: {llama.get('severity', 'Unknown')}")
            logger.info(f"Priority: {llama.get('priority_score', 0)}/100")
            logger.info(f"Reasoning: {llama.get('reasoning', 'N/A')[:100]}")


def main():
    """Test Llama classifier"""
    from pathlib import Path
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from config.settings import settings
    
    # Find latest collection
    data_dir = Path(settings.raw_data_dir)
    collection_files = sorted(data_dir.glob("master_collection_*.json"), reverse=True)
    
    if not collection_files:
        logger.error("No collection files found!")
        return
    
    latest_file = collection_files[0]
    logger.info(f"Processing: {latest_file}")
    logger.info("")
    
    # Create classifier
    classifier = LlamaClassifier(model="llama3.1:8b")
    
    # Process collection (small batch for testing)
    output_file = str(latest_file).replace('.json', '_llama_classified.json')
    classifier.process_collection(str(latest_file), output_file, batch_size=5)


if __name__ == "__main__":
    main()
