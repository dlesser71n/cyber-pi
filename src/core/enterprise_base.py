#!/usr/bin/env python3
"""
Enterprise Standard Base Class
Production-grade reliability and monitoring

Key Principles:
1. Complete understanding of system state
2. Thorough instrumentation and monitoring
3. Graceful degradation under load
4. Automatic recovery from failures
5. Full accountability of all operations
"""

import time
import logging
import psutil
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class OperationMetrics:
    """Metrics for a single operation"""
    start_time: float
    end_time: float = 0.0
    success: bool = False
    error: Optional[Exception] = None
    memory_start: int = 0
    memory_peak: int = 0
    memory_end: int = 0
    items_processed: int = 0
    retries: int = 0

class CircuitBreaker:
    """Circuit breaker for failing operations"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self._lock = threading.Lock()
    
    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        with self._lock:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(f"Circuit breaker opened after {self.failures} failures")
    
    def record_success(self):
        """Record a success and potentially close the circuit"""
        with self._lock:
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failures = 0
                logger.info("Circuit breaker closed after successful operation")
    
    def can_proceed(self) -> bool:
        """Check if operation can proceed"""
        with self._lock:
            if self.state == "CLOSED":
                return True
            
            if self.state == "OPEN":
                # Check if enough time has passed to try again
                if time.time() - self.last_failure_time >= self.reset_timeout:
                    self.state = "HALF-OPEN"
                    logger.info("Circuit breaker entering half-open state")
                    return True
                return False
            
            # HALF-OPEN state allows one try
            return True

class ResourceMonitor:
    """Monitor system resources"""
    
    def __init__(self):
        self.process = psutil.Process()
    
    def get_memory_usage(self) -> Dict[str, int]:
        """Get current memory usage in bytes"""
        mem = self.process.memory_info()
        return {
            "rss": mem.rss,  # Resident Set Size
            "vms": mem.vms,  # Virtual Memory Size
            "shared": mem.shared,  # Shared Memory
            "data": mem.data,  # Data Segment
            "available": psutil.virtual_memory().available
        }
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return self.process.cpu_percent(interval=0.1)
    
    def should_throttle(self, memory_threshold: float = 0.85, cpu_threshold: float = 90.0) -> bool:
        """Check if operations should be throttled"""
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        
        if mem.percent > memory_threshold * 100:
            logger.warning(f"Memory usage high: {mem.percent}%")
            return True
        
        if cpu > cpu_threshold:
            logger.warning(f"CPU usage high: {cpu}%")
            return True
        
        return False

class MetricsCollector:
    """Collect and store operation metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, Dict[str, OperationMetrics]] = {}
        self.resource_monitor = ResourceMonitor()
        self._lock = threading.Lock()
    
    def start_operation(self, operation: str, operation_id: str) -> OperationMetrics:
        """Start tracking an operation"""
        metrics = OperationMetrics(
            start_time=time.time(),
            memory_start=self.resource_monitor.get_memory_usage()["rss"]
        )
        
        with self._lock:
            if operation not in self.metrics:
                self.metrics[operation] = {}
            self.metrics[operation][operation_id] = metrics
        
        return metrics
    
    def update_operation(self, operation: str, operation_id: str, **kwargs):
        """Update operation metrics"""
        with self._lock:
            if operation in self.metrics and operation_id in self.metrics[operation]:
                metrics = self.metrics[operation][operation_id]
                for key, value in kwargs.items():
                    setattr(metrics, key, value)
                
                # Update peak memory
                current_memory = self.resource_monitor.get_memory_usage()["rss"]
                metrics.memory_peak = max(metrics.memory_peak, current_memory)
    
    def end_operation(self, operation: str, operation_id: str, success: bool = True, error: Optional[Exception] = None):
        """End tracking an operation"""
        with self._lock:
            if operation in self.metrics and operation_id in self.metrics[operation]:
                metrics = self.metrics[operation][operation_id]
                metrics.end_time = time.time()
                metrics.success = success
                metrics.error = error
                metrics.memory_end = self.resource_monitor.get_memory_usage()["rss"]

class EnterpriseBase:
    """Base class implementing enterprise standards"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.resource_monitor = ResourceMonitor()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.operation_id = 0
    
    def _get_operation_id(self) -> str:
        """Get a unique operation ID"""
        self.operation_id += 1
        return f"{int(time.time())}-{self.operation_id}"
    
    @contextmanager
    def operation_context(self, operation: str):
        """Context manager for tracking operations"""
        operation_id = self._get_operation_id()
        
        # Check circuit breaker
        if operation in self.circuit_breakers:
            breaker = self.circuit_breakers[operation]
            if not breaker.can_proceed():
                raise Exception(f"Circuit breaker open for {operation}")
        
        # Start metrics
        self.metrics.start_operation(operation, operation_id)
        
        try:
            yield operation_id
            
            # Record success
            if operation in self.circuit_breakers:
                self.circuit_breakers[operation].record_success()
            self.metrics.end_operation(operation, operation_id, success=True)
            
        except Exception as e:
            # Record failure
            if operation in self.circuit_breakers:
                self.circuit_breakers[operation].record_failure()
            self.metrics.end_operation(operation, operation_id, success=False, error=e)
            raise
    
    def register_circuit_breaker(self, operation: str, failure_threshold: int = 5, reset_timeout: int = 60):
        """Register a circuit breaker for an operation"""
        self.circuit_breakers[operation] = CircuitBreaker(
            failure_threshold=failure_threshold,
            reset_timeout=reset_timeout
        )
    
    def should_throttle(self) -> bool:
        """Check if operations should be throttled"""
        return self.resource_monitor.should_throttle()
    
    def get_metrics(self, operation: str) -> Dict[str, OperationMetrics]:
        """Get metrics for an operation"""
        return self.metrics.metrics.get(operation, {})
    
    def log_metrics(self, operation: str):
        """Log metrics for an operation"""
        metrics = self.get_metrics(operation)
        if not metrics:
            return
        
        logger.info(f"\n📊 Metrics for {operation}:")
        for op_id, m in metrics.items():
            duration = m.end_time - m.start_time if m.end_time else 0
            memory_delta = m.memory_end - m.memory_start if m.memory_end else 0
            logger.info(f"  Operation {op_id}:")
            logger.info(f"    Duration: {duration:.2f}s")
            logger.info(f"    Success: {m.success}")
            logger.info(f"    Memory Delta: {memory_delta / 1024 / 1024:.1f}MB")
            logger.info(f"    Items Processed: {m.items_processed}")
            logger.info(f"    Retries: {m.retries}")
            if m.error:
                logger.error(f"    Error: {str(m.error)}")
