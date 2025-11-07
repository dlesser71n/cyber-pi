"""
cyber-pi Massively Parallel Llama Classifier
Uses ALL available resources: 768GB RAM, 36 cores
Processes 50-100 items concurrently instead of 5!
"""

import requests
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MassivelyParallelLlamaClassifier:
    """
    Uses maximum parallelization for Llama classification
    50-100 concurrent requests instead of 5
    """
    
    def __init__(self, 
                 model: str = "llama3.1:8b", 
                 ollama_url: str = "http://localhost:11434",
                 max_concurrent: int = 50):  # Increased from 5 to 50!
        self.model = model
        self.ollama_url = ollama_url
        self.api_endpoint = f"{ollama_url}/api/generate"
        self.max_concurrent = max_concurrent
        
        # Get system resources
        self.cpu_count = multiprocessing.cpu_count()
        
        logger.info(f"🚀 Massively Parallel Llama Classifier")
        logger.info(f"   Model: {model}")
        logger.info(f"   Max Concurrent: {max_concurrent}")
        logger.info(f"   CPU Cores: {self.cpu_count}")
        logger.info(f"   Ollama: {ollama_url}")
        
        # Create thread pool for parallel requests
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
    
    def classify_threat_sync(self, text: str) -> Dict[str, Any]:
        """Synchronous classification for thread pool"""
        prompt = f"""You are a cybersecurity threat intelligence analyst. Analyze this threat and provide classifications.

Threat: {text[:1000]}

Provide your analysis in JSON format with these fields:
1. threat_types: List of applicable threat types from [Critical Vulnerability, Ransomware Attack, Data Breach, Nation-State APT, Supply Chain Attack, Zero-Day Exploit, Phishing Campaign, DDoS Attack, Malware Distribution, Insider Threat]
2. industries: List of most relevant industries from [Aviation/Airline Security, Power Grid/Energy Sector, Healthcare/Hospital Systems, Government/Public Sector, Education/University Networks, Nuclear Power Security, Industrial Control Systems, Financial Services]
3. severity: One of [Critical, High, Medium, Low]
4. priority_score: Number from 0-100
5. reasoning: Brief explanation (max 100 words)

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
                timeout=60
            )
            
            result = response.json()
            response_text = result.get('response', '{}')
            classification = json.loads(response_text)
            return classification
            
        except Exception as e:
            return {
                "threat_types": ["Unknown"],
                "industries": ["Unknown"],
                "severity": "Medium",
                "priority_score": 50,
                "reasoning": f"Error: {str(e)}"
            }
    
    async def classify_batch_massive(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Classify with massive parallelization
        
        Args:
            texts: List of threat texts
            
        Returns:
            List of classifications
        """
        loop = asyncio.get_event_loop()
        
        # Create tasks for all items
        tasks = [
            loop.run_in_executor(self.executor, self.classify_threat_sync, text)
            for text in texts
        ]
        
        # Run all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append({
                    "threat_types": ["Unknown"],
                    "industries": ["Unknown"],
                    "severity": "Medium",
                    "priority_score": 50,
                    "reasoning": f"Error: {str(result)}"
                })
            else:
                final_results.append(result)
        
        return final_results
    
    def process_collection(self, collection_file: str, output_file: str = None):
        """
        Process entire collection with massive parallelization
        
        Args:
            collection_file: Input JSON file
            output_file: Output JSON file
        """
        logger.info("=" * 80)
        logger.info("🚀 MASSIVELY PARALLEL LLAMA CLASSIFICATION")
        logger.info("=" * 80)
        logger.info("")
        
        # Load collection
        with open(collection_file, 'r') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        logger.info(f"Loaded {len(items)} items")
        logger.info(f"Max concurrent requests: {self.max_concurrent}")
        logger.info(f"CPU cores: {self.cpu_count}")
        logger.info("")
        
        # Process in large batches
        classified_items = []
        start_time = datetime.now()
        batch_size = self.max_concurrent
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(items) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")
            
            # Extract texts
            texts = [item.get('title', '') + ' ' + item.get('description', '')[:200] 
                    for item in batch]
            
            # Classify batch with massive parallelization
            batch_start = datetime.now()
            results = asyncio.run(self.classify_batch_massive(texts))
            batch_duration = (datetime.now() - batch_start).total_seconds()
            
            # Add classifications to items
            for item, classification in zip(batch, results):
                item['llama_classification'] = classification
                item['llama_priority_score'] = classification.get('priority_score', 50)
            
            classified_items.extend(batch)
            
            # Progress
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = len(classified_items) / elapsed if elapsed > 0 else 0
            logger.info(f"  ✓ Batch completed in {batch_duration:.1f}s")
            logger.info(f"  Total processed: {len(classified_items)}/{len(items)} ({rate:.1f} items/sec)")
            logger.info(f"  ETA: {(len(items) - len(classified_items)) / rate / 60:.1f} minutes")
            logger.info("")
        
        # Save results
        if not output_file:
            output_file = collection_file.replace('.json', '_llama_parallel.json')
        
        data['items'] = classified_items
        data['metadata']['llama_classified'] = True
        data['metadata']['llama_model'] = self.model
        data['metadata']['max_concurrent'] = self.max_concurrent
        data['metadata']['classification_timestamp'] = datetime.now().isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info("✅ MASSIVELY PARALLEL CLASSIFICATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total items: {len(classified_items)}")
        logger.info(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        logger.info(f"Rate: {len(classified_items)/duration:.1f} items/sec")
        logger.info(f"Concurrent requests: {self.max_concurrent}")
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


def main():
    """Run massively parallel Llama classifier"""
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
    
    # Create classifier with 50 concurrent requests (10x more than before!)
    classifier = MassivelyParallelLlamaClassifier(
        model="llama3.1:8b",
        max_concurrent=50  # Use 50 concurrent requests!
    )
    
    # Process collection
    output_file = str(latest_file).replace('.json', '_llama_parallel.json')
    classifier.process_collection(str(latest_file), output_file)


if __name__ == "__main__":
    main()
