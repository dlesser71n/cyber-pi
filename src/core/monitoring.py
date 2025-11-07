#!/usr/bin/env python3
"""
Enterprise-Grade System Monitoring
Production-ready observability and metrics collection
"""

import time
import logging
import psutil
import threading
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/enterprise_monitoring.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Single metric measurement"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class Metric:
    """Prometheus-style metric with type and help text"""
    name: str
    type: str  # counter, gauge, histogram
    help: str
    points: List[MetricPoint] = field(default_factory=list)
    
    def add(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Add a new measurement"""
        self.points.append(MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        ))
        
        # Keep only last hour of data
        cutoff = time.time() - 3600
        self.points = [p for p in self.points if p.timestamp > cutoff]

class ResourceMetrics:
    """System resource metrics collector"""
    
    def __init__(self):
        """Initialize metrics"""
        self.process = psutil.Process()
        self.metrics = {
            # Memory metrics
            'process_memory_rss': Metric(
                name='process_memory_rss',
                type='gauge',
                help='Process resident set size in bytes'
            ),
            'process_memory_vms': Metric(
                name='process_memory_vms',
                type='gauge',
                help='Process virtual memory size in bytes'
            ),
            'system_memory_available': Metric(
                name='system_memory_available',
                type='gauge',
                help='System memory available in bytes'
            ),
            'system_memory_percent': Metric(
                name='system_memory_percent',
                type='gauge',
                help='System memory usage percentage'
            ),
            
            # CPU metrics
            'process_cpu_percent': Metric(
                name='process_cpu_percent',
                type='gauge',
                help='Process CPU usage percentage'
            ),
            'system_cpu_percent': Metric(
                name='system_cpu_percent',
                type='gauge',
                help='System CPU usage percentage'
            ),
            
            # IO metrics
            'process_io_read_bytes': Metric(
                name='process_io_read_bytes',
                type='counter',
                help='Process bytes read from disk'
            ),
            'process_io_write_bytes': Metric(
                name='process_io_write_bytes',
                type='counter',
                help='Process bytes written to disk'
            ),
            
            # Neo4j metrics
            'neo4j_operations': Metric(
                name='neo4j_operations',
                type='counter',
                help='Number of Neo4j operations'
            ),
            'neo4j_operation_errors': Metric(
                name='neo4j_operation_errors',
                type='counter',
                help='Number of Neo4j operation errors'
            ),
            'neo4j_operation_duration': Metric(
                name='neo4j_operation_duration',
                type='histogram',
                help='Duration of Neo4j operations in seconds'
            ),
            
            # Redis metrics
            'redis_operations': Metric(
                name='redis_operations',
                type='counter',
                help='Number of Redis operations'
            ),
            'redis_operation_errors': Metric(
                name='redis_operation_errors',
                type='counter',
                help='Number of Redis operation errors'
            ),
            'redis_operation_duration': Metric(
                name='redis_operation_duration',
                type='histogram',
                help='Duration of Redis operations in seconds'
            )
        }
        
        # Start collection thread
        self.running = True
        self.collection_thread = threading.Thread(target=self._collect_metrics)
        self.collection_thread.daemon = True
        self.collection_thread.start()
    
    def _collect_metrics(self):
        """Continuously collect metrics"""
        while self.running:
            try:
                # Process metrics
                proc = psutil.Process()
                mem_info = proc.memory_info()
                
                self.metrics['process_memory_rss'].add(mem_info.rss)
                self.metrics['process_memory_vms'].add(mem_info.vms)
                self.metrics['process_cpu_percent'].add(proc.cpu_percent())
                
                io_counters = proc.io_counters()
                self.metrics['process_io_read_bytes'].add(io_counters.read_bytes)
                self.metrics['process_io_write_bytes'].add(io_counters.write_bytes)
                
                # System metrics
                sys_mem = psutil.virtual_memory()
                self.metrics['system_memory_available'].add(sys_mem.available)
                self.metrics['system_memory_percent'].add(sys_mem.percent)
                self.metrics['system_cpu_percent'].add(psutil.cpu_percent())
                
            except Exception as e:
                logger.exception("Failed to collect metrics")
            
            time.sleep(1)  # Collect every second
    
    def stop(self):
        """Stop metrics collection"""
        self.running = False
        self.collection_thread.join()
    
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current metric values"""
        current = {}
        for name, metric in self.metrics.items():
            if metric.points:
                current[name] = metric.points[-1].value
        return current
    
    def get_metric_history(self, name: str, minutes: int = 5) -> List[MetricPoint]:
        """Get historical metric values"""
        if name not in self.metrics:
            return []
            
        cutoff = time.time() - (minutes * 60)
        return [p for p in self.metrics[name].points if p.timestamp > cutoff]
    
    def get_resource_summary(self) -> str:
        """Get human-readable resource summary"""
        current = self.get_current_metrics()
        
        return f"""
🔍 SYSTEM RESOURCES:
Memory:
  - Process RSS: {current.get('process_memory_rss', 0) / 1024 / 1024:.1f} MB
  - Process VMS: {current.get('process_memory_vms', 0) / 1024 / 1024:.1f} MB
  - System Available: {current.get('system_memory_available', 0) / 1024 / 1024 / 1024:.1f} GB
  - System Usage: {current.get('system_memory_percent', 0):.1f}%

CPU:
  - Process: {current.get('process_cpu_percent', 0):.1f}%
  - System: {current.get('system_cpu_percent', 0):.1f}%

IO:
  - Read: {current.get('process_io_read_bytes', 0) / 1024 / 1024:.1f} MB
  - Write: {current.get('process_io_write_bytes', 0) / 1024 / 1024:.1f} MB

Database Operations:
  - Neo4j: {current.get('neo4j_operations', 0):.0f} ops ({current.get('neo4j_operation_errors', 0):.0f} errors)
  - Redis: {current.get('redis_operations', 0):.0f} ops ({current.get('redis_operation_errors', 0):.0f} errors)
"""

class OperationMetrics:
    """Operation-level metrics collector"""
    
    def __init__(self):
        """Initialize metrics"""
        self.metrics = defaultdict(lambda: {
            'count': 0,
            'errors': 0,
            'duration_total': 0.0,
            'duration_max': 0.0,
            'items_processed': 0,
            'start_time': None
        })
        self._lock = threading.Lock()
    
    def start_operation(self, name: str):
        """Start tracking an operation"""
        with self._lock:
            self.metrics[name]['start_time'] = time.time()
    
    def end_operation(self, name: str, success: bool = True, items: int = 0):
        """End tracking an operation"""
        with self._lock:
            metrics = self.metrics[name]
            
            if metrics['start_time'] is not None:
                duration = time.time() - metrics['start_time']
                metrics['count'] += 1
                metrics['duration_total'] += duration
                metrics['duration_max'] = max(metrics['duration_max'], duration)
                metrics['items_processed'] += items
                
                if not success:
                    metrics['errors'] += 1
                
                metrics['start_time'] = None
    
    def get_metrics(self, name: str) -> Dict[str, float]:
        """Get metrics for an operation"""
        with self._lock:
            metrics = self.metrics[name]
            count = metrics['count']
            
            if count == 0:
                return {
                    'count': 0,
                    'error_rate': 0.0,
                    'avg_duration': 0.0,
                    'max_duration': 0.0,
                    'items_per_second': 0.0
                }
            
            return {
                'count': count,
                'error_rate': metrics['errors'] / count,
                'avg_duration': metrics['duration_total'] / count,
                'max_duration': metrics['duration_max'],
                'items_per_second': metrics['items_processed'] / metrics['duration_total'] if metrics['duration_total'] > 0 else 0
            }
    
    def get_summary(self) -> str:
        """Get human-readable metrics summary"""
        summary = ["📊 OPERATION METRICS:"]
        
        for name, metrics in sorted(self.metrics.items()):
            if metrics['count'] > 0:
                summary.append(f"\n{name}:")
                summary.append(f"  - Count: {metrics['count']}")
                summary.append(f"  - Error Rate: {(metrics['errors'] / metrics['count']) * 100:.1f}%")
                summary.append(f"  - Avg Duration: {metrics['duration_total'] / metrics['count']:.2f}s")
                summary.append(f"  - Max Duration: {metrics['duration_max']:.2f}s")
                if metrics['duration_total'] > 0:
                    summary.append(f"  - Throughput: {metrics['items_processed'] / metrics['duration_total']:.1f} items/sec")
        
        return "\n".join(summary)

class EnterpriseMonitoring:
    """Complete enterprise monitoring system"""
    
    def __init__(self):
        """Initialize all monitoring components"""
        self.resources = ResourceMetrics()
        self.operations = OperationMetrics()
        
        # Start periodic reporting
        self.report_thread = threading.Thread(target=self._periodic_report)
        self.report_thread.daemon = True
        self.report_thread.start()
    
    def _periodic_report(self):
        """Generate periodic monitoring report"""
        while True:
            try:
                logger.info("\n" + "="*80)
                logger.info("⚡ SYSTEM STATUS REPORT")
                logger.info("="*80)
                logger.info(self.resources.get_resource_summary())
                logger.info(self.operations.get_summary())
                logger.info("="*80)
            except Exception as e:
                logger.exception("Failed to generate monitoring report")
            
            time.sleep(300)  # Report every 5 minutes
    
    def stop(self):
        """Stop all monitoring"""
        self.resources.stop()
