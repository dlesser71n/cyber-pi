#!/usr/bin/env python3
"""
Parallel Worker Orchestrator
Runs multiple workers in parallel to process Redis queues
"""

import asyncio
import subprocess
import sys
from pathlib import Path
import time
import signal


class WorkerOrchestrator:
    """Manages multiple parallel workers"""
    
    def __init__(self):
        self.workers_dir = Path(__file__).parent / "workers"
        self.processes = []
        
    def start_workers(self, weaviate_count=3, neo4j_count=2, stix_count=1):
        """Start worker processes"""
        print("="*60)
        print("🚀 PARALLEL WORKER ORCHESTRATOR")
        print("="*60)
        print()
        
        # Weaviate workers
        print(f"Starting {weaviate_count} Weaviate workers...")
        for i in range(1, weaviate_count + 1):
            proc = subprocess.Popen(
                [sys.executable, str(self.workers_dir / "weaviate_worker.py"), str(i)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.processes.append(("Weaviate", i, proc))
            print(f"  ✓ Weaviate worker {i} started (PID: {proc.pid})")
        
        # Neo4j workers
        print(f"\nStarting {neo4j_count} Neo4j workers...")
        for i in range(1, neo4j_count + 1):
            proc = subprocess.Popen(
                [sys.executable, str(self.workers_dir / "neo4j_worker.py"), str(i)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.processes.append(("Neo4j", i, proc))
            print(f"  ✓ Neo4j worker {i} started (PID: {proc.pid})")
        
        # STIX workers
        print(f"\nStarting {stix_count} STIX workers...")
        for i in range(1, stix_count + 1):
            proc = subprocess.Popen(
                [sys.executable, str(self.workers_dir / "stix_worker.py"), str(i)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.processes.append(("STIX", i, proc))
            print(f"  ✓ STIX worker {i} started (PID: {proc.pid})")
        
        print()
        print(f"📊 Total workers: {len(self.processes)}")
        print()
        
    def monitor_workers(self):
        """Monitor worker progress"""
        print("📈 Monitoring workers (Ctrl+C to stop)...")
        print()
        
        try:
            while True:
                active = 0
                for worker_type, worker_id, proc in self.processes:
                    if proc.poll() is None:
                        active += 1
                
                if active == 0:
                    print("\n✅ All workers completed!")
                    break
                
                print(f"\r  Active workers: {active}/{len(self.processes)}", end="", flush=True)
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupt received, shutting down workers...")
            self.stop_workers()
    
    def stop_workers(self):
        """Stop all workers"""
        for worker_type, worker_id, proc in self.processes:
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
    
    def show_results(self):
        """Show final results"""
        print("\n" + "="*60)
        print("📊 WORKER RESULTS")
        print("="*60)
        print()
        
        for worker_type, worker_id, proc in self.processes:
            status = "✅ Completed" if proc.returncode == 0 else f"❌ Failed (code: {proc.returncode})"
            print(f"{worker_type} Worker {worker_id}: {status}")
        
        print()


def main():
    """Run parallel workers"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run parallel workers")
    parser.add_argument("--weaviate", type=int, default=3, help="Number of Weaviate workers")
    parser.add_argument("--neo4j", type=int, default=2, help="Number of Neo4j workers")
    parser.add_argument("--stix", type=int, default=1, help="Number of STIX workers")
    
    args = parser.parse_args()
    
    orchestrator = WorkerOrchestrator()
    
    try:
        orchestrator.start_workers(
            weaviate_count=args.weaviate,
            neo4j_count=args.neo4j,
            stix_count=args.stix
        )
        
        orchestrator.monitor_workers()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        orchestrator.stop_workers()
        return 1
    finally:
        orchestrator.show_results()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
