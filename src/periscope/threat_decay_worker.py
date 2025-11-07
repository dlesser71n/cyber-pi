#!/usr/bin/env python3
"""
TQAKB Confidence Decay Worker - Digital Truth Implementation
Runs periodically to update confidence scores and move content between cache tiers

Core Principle: FACTS DO NOT DECAY
- Facts are eternal truths that remain stable
- Context ages appropriately over time
- This embodies the "Digital Truth" philosophy

Part of Phase 2 of the Hybrid Architecture
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

from confidence_scorer import ConfidenceScorer
from temporal_wrapper import TemporalWrapper
import chromadb

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfidenceDecayWorker:
    """
    Worker that applies confidence decay and manages cache tiers
    
    Responsibilities:
    - Apply time-based confidence decay
    - Move chunks between hot/warm/cold tiers
    - Update ChromaDB metadata
    - Log tier transitions
    """
    
    def __init__(self, 
                 chroma_path: str = "./chroma_db",
                 collection_name: str = "tqakb_chunks",
                 run_interval_hours: int = 1):
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self.run_interval_hours = run_interval_hours
        
        self.scorer = ConfidenceScorer()
        self.wrapper = TemporalWrapper()
        
        self.client = None
        self.collection = None
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'facts_protected': 0,
            'context_decayed': 0,
            'tier_changes': {'hot_to_warm': 0, 'warm_to_cold': 0},
            'confidence_updates': 0,
            'errors': 0
        }
    
    def initialize(self):
        """Initialize ChromaDB connection"""
        try:
            self.client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"✅ Connected to ChromaDB: {self.collection_name}")
            logger.info(f"   Total chunks: {self.collection.count()}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB: {e}")
            return False
    
    def calculate_decay(self, 
                       initial_confidence: float,
                       decay_rate: float,
                       days_elapsed: float,
                       is_fact: bool = False) -> float:
        """
        Calculate decayed confidence score
        
        IMPORTANT: Facts do NOT decay - they remain at their initial confidence
        Only context/opinions/temporal information decays
        
        Formula (for non-facts): confidence = initial_confidence * (1 - decay_rate) ^ days_elapsed
        """
        # FACTS DO NOT DECAY
        if is_fact:
            return initial_confidence
        
        if days_elapsed <= 0:
            return initial_confidence
        
        decayed = initial_confidence * ((1 - decay_rate) ** days_elapsed)
        
        # Floor at 0.5 (don't decay below 50% confidence)
        return max(0.5, decayed)
    
    def determine_cache_tier(self, confidence: float, days_old: float) -> str:
        """
        Determine cache tier based on confidence and age
        
        Rules:
        - hot: confidence >= 0.9 AND age < 7 days
        - warm: confidence >= 0.7 OR age < 30 days
        - cold: confidence < 0.7 AND age >= 30 days
        """
        if confidence >= 0.9 and days_old < 7:
            return 'hot'
        elif confidence >= 0.7 or days_old < 30:
            return 'warm'
        else:
            return 'cold'
    
    def process_chunk(self, chunk_id: str, metadata: Dict) -> Tuple[bool, Dict]:
        """
        Process a single chunk for decay
        
        Returns: (changed, new_metadata)
        """
        try:
            # Extract temporal data
            valid_from = metadata.get('valid_from')
            initial_confidence = metadata.get('initial_confidence', 0.85)
            decay_rate = metadata.get('decay_rate', 0.02)
            current_confidence = metadata.get('confidence', initial_confidence)
            current_tier = metadata.get('cache_tier', 'warm')
            
            # Check if this is a FACT (facts do NOT decay)
            is_fact = metadata.get('is_fact', False)
            content_type = metadata.get('content_type', 'context')
            
            # Treat extractions as facts by default
            if content_type == 'extraction':
                is_fact = True
            
            if not valid_from:
                logger.debug(f"Chunk {chunk_id} has no valid_from, skipping")
                return False, metadata
            
            # Calculate days elapsed
            try:
                valid_from_dt = datetime.fromisoformat(valid_from.replace('Z', '+00:00'))
                now = datetime.now(valid_from_dt.tzinfo)
                days_elapsed = (now - valid_from_dt).total_seconds() / 86400
            except Exception as e:
                logger.warning(f"Failed to parse date for {chunk_id}: {e}")
                return False, metadata
            
            # Calculate new confidence (facts do NOT decay)
            new_confidence = self.calculate_decay(
                initial_confidence,
                decay_rate,
                days_elapsed,
                is_fact=is_fact
            )
            
            # Track fact protection
            if is_fact:
                self.stats['facts_protected'] += 1
                if days_elapsed > 0:
                    logger.debug(f"🛡️ FACT protected from decay: {chunk_id[:8]}... (confidence: {initial_confidence:.3f})")
            else:
                if confidence_changed:
                    self.stats['context_decayed'] += 1
            
            # Determine new tier
            new_tier = self.determine_cache_tier(new_confidence, days_elapsed)
            
            # Check if anything changed
            confidence_changed = abs(new_confidence - current_confidence) > 0.01
            tier_changed = new_tier != current_tier
            
            if not (confidence_changed or tier_changed):
                return False, metadata
            
            # Update metadata
            new_metadata = metadata.copy()
            new_metadata['confidence'] = round(new_confidence, 3)
            new_metadata['cache_tier'] = new_tier
            new_metadata['last_decay_update'] = datetime.now().isoformat()
            
            # Log tier changes
            if tier_changed:
                logger.info(f"🔄 Tier change: {chunk_id[:8]}... {current_tier} → {new_tier} (confidence: {new_confidence:.3f})")
                self.stats['tier_changes'][f'{current_tier}_to_{new_tier}'] = \
                    self.stats['tier_changes'].get(f'{current_tier}_to_{new_tier}', 0) + 1
            
            if confidence_changed:
                self.stats['confidence_updates'] += 1
            
            return True, new_metadata
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_id}: {e}")
            self.stats['errors'] += 1
            return False, metadata
    
    def run_decay_cycle(self) -> Dict:
        """
        Run one decay cycle on all chunks
        
        Returns: Statistics for this cycle
        """
        logger.info("🔄 Starting confidence decay cycle...")
        
        cycle_stats = {
            'start_time': datetime.now().isoformat(),
            'chunks_processed': 0,
            'chunks_updated': 0,
            'tier_changes': {},
            'confidence_updates': 0,
            'errors': 0
        }
        
        try:
            # Get all chunks (in batches to avoid memory issues)
            batch_size = 100
            offset = 0
            
            while True:
                # Get batch
                results = self.collection.get(
                    limit=batch_size,
                    offset=offset,
                    include=['metadatas']
                )
                
                if not results['ids']:
                    break
                
                # Process each chunk in batch
                updates = []
                for chunk_id, metadata in zip(results['ids'], results['metadatas']):
                    changed, new_metadata = self.process_chunk(chunk_id, metadata)
                    
                    cycle_stats['chunks_processed'] += 1
                    
                    if changed:
                        updates.append((chunk_id, new_metadata))
                        cycle_stats['chunks_updated'] += 1
                
                # Apply updates in batch
                if updates:
                    for chunk_id, new_metadata in updates:
                        self.collection.update(
                            ids=[chunk_id],
                            metadatas=[new_metadata]
                        )
                
                offset += batch_size
                
                # Log progress
                if offset % 500 == 0:
                    logger.info(f"   Processed {offset} chunks...")
            
            # Update global stats
            self.stats['total_processed'] += cycle_stats['chunks_processed']
            
            cycle_stats['end_time'] = datetime.now().isoformat()
            cycle_stats['duration_seconds'] = (
                datetime.fromisoformat(cycle_stats['end_time']) - 
                datetime.fromisoformat(cycle_stats['start_time'])
            ).total_seconds()
            
            logger.info(f"✅ Decay cycle complete:")
            logger.info(f"   Processed: {cycle_stats['chunks_processed']}")
            logger.info(f"   Updated: {cycle_stats['chunks_updated']}")
            logger.info(f"   Duration: {cycle_stats['duration_seconds']:.2f}s")
            
            return cycle_stats
            
        except Exception as e:
            logger.error(f"❌ Error in decay cycle: {e}")
            cycle_stats['error'] = str(e)
            return cycle_stats
    
    async def run_forever(self):
        """Run the decay worker continuously"""
        logger.info(f"🚀 Starting Confidence Decay Worker")
        logger.info(f"   Run interval: {self.run_interval_hours} hour(s)")
        logger.info(f"   ChromaDB: {self.chroma_path}")
        logger.info(f"   Collection: {self.collection_name}")
        
        if not self.initialize():
            logger.error("Failed to initialize, exiting")
            return
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"🔄 Decay Cycle #{cycle_count}")
                logger.info(f"{'='*60}")
                
                cycle_stats = self.run_decay_cycle()
                
                # Log cumulative stats
                logger.info(f"\n📊 Cumulative Statistics:")
                logger.info(f"   Total cycles: {cycle_count}")
                logger.info(f"   Total processed: {self.stats['total_processed']}")
                logger.info(f"   🛡️ Facts protected: {self.stats['facts_protected']}")
                logger.info(f"   📉 Context decayed: {self.stats['context_decayed']}")
                logger.info(f"   Confidence updates: {self.stats['confidence_updates']}")
                logger.info(f"   Tier changes: {self.stats['tier_changes']}")
                logger.info(f"   Errors: {self.stats['errors']}")
                
                # Wait for next cycle
                wait_seconds = self.run_interval_hours * 3600
                next_run = datetime.now() + timedelta(seconds=wait_seconds)
                logger.info(f"\n⏰ Next run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"   Sleeping for {self.run_interval_hours} hour(s)...")
                
                await asyncio.sleep(wait_seconds)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️ Received interrupt signal, shutting down gracefully...")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
        finally:
            logger.info(f"\n📊 Final Statistics:")
            logger.info(f"   Total cycles: {cycle_count}")
            logger.info(f"   Total processed: {self.stats['total_processed']}")
            logger.info(f"   Confidence updates: {self.stats['confidence_updates']}")
            logger.info(f"   Tier changes: {self.stats['tier_changes']}")
            logger.info(f"   Errors: {self.stats['errors']}")
            logger.info("👋 Confidence Decay Worker stopped")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TQAKB Confidence Decay Worker')
    parser.add_argument('--interval', type=int, default=1,
                       help='Run interval in hours (default: 1)')
    parser.add_argument('--chroma-path', type=str, default='./chroma_db',
                       help='Path to ChromaDB (default: ./chroma_db)')
    parser.add_argument('--collection', type=str, default='tqakb_chunks',
                       help='Collection name (default: tqakb_chunks)')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit (for testing)')
    
    args = parser.parse_args()
    
    worker = ConfidenceDecayWorker(
        chroma_path=args.chroma_path,
        collection_name=args.collection,
        run_interval_hours=args.interval
    )
    
    if args.once:
        # Run once for testing
        logger.info("🧪 Running in test mode (single cycle)")
        if worker.initialize():
            cycle_stats = worker.run_decay_cycle()
            print("\n" + "="*60)
            print("📊 TEST CYCLE RESULTS")
            print("="*60)
            print(f"Chunks processed: {cycle_stats['chunks_processed']}")
            print(f"Chunks updated: {cycle_stats['chunks_updated']}")
            print(f"Duration: {cycle_stats.get('duration_seconds', 0):.2f}s")
            print("="*60)
    else:
        # Run continuously
        asyncio.run(worker.run_forever())

if __name__ == "__main__":
    main()
