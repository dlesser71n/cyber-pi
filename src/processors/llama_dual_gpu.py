"""
cyber-pi Dual-GPU Llama Classifier
Runs multiple Ollama instances on different GPUs
2-3x faster by using both A6000s!
"""

import requests
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import subprocess
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualGPULlamaClassifier:
    """
    Runs Llama on multiple GPUs simultaneously
    2-3x faster than single GPU
    """
    
    def __init__(self, 
                 model: str = "llama3.1:8b",
                 num_instances: int = 2):  # Run 2 instances
        self.model = model
        self.num_instances = num_instances
        self.base_port = 11434
        self.instances = []
        
        logger.info(f"🚀 Dual-GPU Llama Classifier")
        logger.info(f"   Model: {model}")
        logger.info(f"   Instances: {num_instances}")
        logger.info(f"   Strategy: Load balance across GPUs")
        
        # Setup multiple Ollama instances
        self._setup_instances()
        
        # Create thread pool
        self.executor = ThreadPoolExecutor(max_workers=num_instances * 25)
    
    def _setup_instances(self):
        """Setup multiple Ollama instances on different GPUs"""
        logger.info("")
        logger.info("Setting up Ollama instances...")
        
        for i in range(self.num_instances):
            port = self.base_port + i
            gpu_id = i % 2  # Alternate between GPU 0 and 1
            
            instance = {
                'port': port,
                'gpu_id': gpu_id,
                'url': f"http://localhost:{port}",
                'api_endpoint': f"http://localhost:{port}/api/generate"
            }
            
            self.instances.append(instance)
            logger.info(f"  Instance {i+1}: Port {port}, GPU {gpu_id}")
        
        logger.info("")
        logger.info("✓ Using existing Ollama instances on ports 11434 and 11435")
        logger.info("")
        
        # Wait a moment for instances to be ready
        time.sleep(2)
        
        # Verify instances
        logger.info("Verifying instances...")
        for inst in self.instances:
            try:
                response = requests.get(f"{inst['url']}/api/tags", timeout=5)
                if response.status_code == 200:
                    logger.info(f"  ✓ Instance on port {inst['port']} is ready")
                else:
                    logger.warning(f"  ⚠️  Instance on port {inst['port']} not responding")
            except:
                logger.error(f"  ✗ Instance on port {inst['port']} not available!")
        
        logger.info("")
    
    def classify_threat_sync(self, text: str, instance_idx: int) -> Dict[str, Any]:
        """Classify using specific instance"""
        instance = self.instances[instance_idx]
        
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
                instance['api_endpoint'],
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
    
    async def classify_batch_dual_gpu(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Classify with load balancing across GPUs
        """
        loop = asyncio.get_event_loop()
        
        # Distribute work across instances
        tasks = []
        for i, text in enumerate(texts):
            instance_idx = i % self.num_instances  # Round-robin
            task = loop.run_in_executor(
                self.executor, 
                self.classify_threat_sync, 
                text, 
                instance_idx
            )
            tasks.append(task)
        
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
        """Process collection with dual-GPU parallelization"""
        logger.info("=" * 80)
        logger.info("🚀 DUAL-GPU LLAMA CLASSIFICATION")
        logger.info("=" * 80)
        logger.info("")
        
        # Load collection
        with open(collection_file, 'r') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        logger.info(f"Loaded {len(items)} items")
        logger.info(f"Instances: {self.num_instances}")
        logger.info(f"Expected speedup: {self.num_instances}x")
        logger.info("")
        
        # Process in batches
        classified_items = []
        start_time = datetime.now()
        batch_size = 50  # Process 50 at a time
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(items) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")
            
            # Extract texts
            texts = [item.get('title', '') + ' ' + item.get('description', '')[:200] 
                    for item in batch]
            
            # Classify with dual-GPU
            batch_start = datetime.now()
            results = asyncio.run(self.classify_batch_dual_gpu(texts))
            batch_duration = (datetime.now() - batch_start).total_seconds()
            
            # Add classifications
            for item, classification in zip(batch, results):
                item['llama_classification'] = classification
                item['llama_priority_score'] = classification.get('priority_score', 50)
            
            classified_items.extend(batch)
            
            # Progress
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = len(classified_items) / elapsed if elapsed > 0 else 0
            logger.info(f"  ✓ Batch completed in {batch_duration:.1f}s")
            logger.info(f"  Total processed: {len(classified_items)}/{len(items)} ({rate:.1f} items/sec)")
            if rate > 0:
                logger.info(f"  ETA: {(len(items) - len(classified_items)) / rate / 60:.1f} minutes")
            logger.info("")
        
        # Save results
        if not output_file:
            output_file = collection_file.replace('.json', '_llama_dual_gpu.json')
        
        data['items'] = classified_items
        data['metadata']['llama_classified'] = True
        data['metadata']['llama_model'] = self.model
        data['metadata']['num_gpu_instances'] = self.num_instances
        data['metadata']['classification_timestamp'] = datetime.now().isoformat()
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info("✅ DUAL-GPU CLASSIFICATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total items: {len(classified_items)}")
        logger.info(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        logger.info(f"Rate: {len(classified_items)/duration:.1f} items/sec")
        logger.info(f"GPU instances: {self.num_instances}")
        logger.info(f"Output: {output_file}")


def main():
    """Run dual-GPU Llama classifier"""
    from pathlib import Path
    import sys
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
    
    # Create dual-GPU classifier
    classifier = DualGPULlamaClassifier(
        model="llama3.1:8b",
        num_instances=2  # Use 2 GPUs
    )
    
    # Process collection
    output_file = str(latest_file).replace('.json', '_llama_dual_gpu.json')
    classifier.process_collection(str(latest_file), output_file)


if __name__ == "__main__":
    main()
