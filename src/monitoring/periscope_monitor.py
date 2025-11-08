#!/usr/bin/env python3
"""
Production-Grade Monitoring for Periscope Integration
Provides metrics, health checks, circuit breakers, and error tracking
"""

import time
import asyncio
import logging
import psutil
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import json
import subprocess
import redis.asyncio as redis
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


class HealthStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class Metrics:
    """Comprehensive metrics tracking"""
    # Counters
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    retried_requests: int = 0
    
    # Threats
    threats_ingested: int = 0
    threats_failed: int = 0
    threats_converted: int = 0
    threats_skipped: int = 0
    
    # Performance
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    
    # Errors
    error_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Health
    circuit_breaker_trips: int = 0
    consecutive_failures: int = 0
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    
    def avg_duration_ms(self) -> float:
        """Calculate average duration"""
        if self.total_requests == 0:
            return 0.0
        return self.total_duration_ms / self.total_requests
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'counters': {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'retried_requests': self.retried_requests,
            },
            'threats': {
                'ingested': self.threats_ingested,
                'failed': self.threats_failed,
                'converted': self.threats_converted,
                'skipped': self.threats_skipped,
            },
            'performance': {
                'avg_duration_ms': round(self.avg_duration_ms(), 2),
                'min_duration_ms': round(self.min_duration_ms, 2) if self.min_duration_ms != float('inf') else 0,
                'max_duration_ms': round(self.max_duration_ms, 2),
                'total_duration_ms': round(self.total_duration_ms, 2),
            },
            'health': {
                'success_rate': round(self.success_rate(), 2),
                'circuit_breaker_trips': self.circuit_breaker_trips,
                'consecutive_failures': self.consecutive_failures,
                'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
                'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            },
            'errors': dict(self.error_counts),
            'timestamp': datetime.utcnow().isoformat()
        }


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    half_open_max_calls: int = 3
    
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    half_open_calls: int = 0
    
    def record_success(self):
        """Record successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                logger.info("🔓 Circuit breaker CLOSED - System recovered")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.half_open_calls = 0
        else:
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning("⚠️  Circuit breaker OPEN - Recovery failed")
            self.state = CircuitState.OPEN
            self.success_count = 0
            self.half_open_calls = 0
        elif self.failure_count >= self.failure_threshold:
            logger.error(f"🔥 Circuit breaker OPEN - {self.failure_count} consecutive failures")
            self.state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout elapsed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    logger.info("🔄 Circuit breaker HALF_OPEN - Testing recovery")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return False


class PeriscopeMonitor:
    """
    Production monitoring for Periscope integration
    
    Features:
    - Real-time metrics collection
    - Circuit breaker pattern
    - Automatic retry with exponential backoff
    - Dead letter queue for failed items
    - Health check endpoint
    - Alert generation
    - Performance tracking
    - Redis metrics storage
    - GPU monitoring
    - System resource tracking
    """
    
    async def initialize(self):
        """Initialize async components"""
        if not self._initialized:
            self.redis = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                max_connections=10
            )
            await self.redis.ping()
            self._initialized = True
            console.print("✅ Periscope monitoring connected to Redis")
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 32379,
        enable_circuit_breaker: bool = True,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
        dead_letter_queue_size: int = 1000
    ):
        """Initialize monitoring system"""
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis: Optional[redis.Redis] = None
        self._initialized = False
        
        self.metrics = Metrics()
        self.circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay
        
        # Dead letter queue for failed items
        self.dead_letter_queue: deque = deque(maxlen=dead_letter_queue_size)
        
        # Recent errors for analysis
        self.recent_errors: deque = deque(maxlen=100)
        
        # Alert thresholds
        self.alert_thresholds = {
            'error_rate': 10.0,  # %
            'consecutive_failures': 3,
            'avg_duration_ms': 5000.0,
            'dead_letter_queue_size': 100
        }
        
        # System monitoring
        self.process = psutil.Process()
        
        console.print("✅ Periscope monitoring initialized")
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        operation_name: str = "operation",
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic and circuit breaker
        
        Args:
            func: Async function to execute
            *args: Function arguments
            operation_name: Operation name for logging
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Exception if all retries fail
        """
        # Check circuit breaker
        if self.circuit_breaker and not self.circuit_breaker.can_execute():
            error_msg = f"Circuit breaker OPEN - {operation_name} blocked"
            logger.error(f"🚫 {error_msg}")
            self.metrics.failed_requests += 1
            raise RuntimeError(error_msg)
        
        start_time = time.time()
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.metrics.total_requests += 1
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Record success
                duration_ms = (time.time() - start_time) * 1000
                self._record_success(duration_ms, operation_name)
                
                return result
                
            except Exception as e:
                last_exception = e
                duration_ms = (time.time() - start_time) * 1000
                
                # Record failure
                self._record_failure(e, duration_ms, operation_name)
                
                # Check if we should retry
                if attempt < self.max_retries:
                    retry_delay = min(
                        self.initial_retry_delay * (2 ** attempt),
                        self.max_retry_delay
                    )
                    
                    logger.warning(
                        f"⚠️  {operation_name} failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}. "
                        f"Retrying in {retry_delay:.1f}s..."
                    )
                    
                    self.metrics.retried_requests += 1
                    await asyncio.sleep(retry_delay)
                else:
                    # All retries exhausted
                    logger.error(
                        f"🔥 {operation_name} failed after {self.max_retries + 1} attempts: {e}"
                    )
                    break
        
        # All retries failed
        self.metrics.failed_requests += 1
        if self.circuit_breaker:
            self.metrics.circuit_breaker_trips += 1
        
        raise last_exception
    
    def _record_success(self, duration_ms: float, operation_name: str):
        """Record successful operation"""
        self.metrics.successful_requests += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = datetime.utcnow()
        
        # Update duration stats
        self.metrics.total_duration_ms += duration_ms
        self.metrics.min_duration_ms = min(self.metrics.min_duration_ms, duration_ms)
        self.metrics.max_duration_ms = max(self.metrics.max_duration_ms, duration_ms)
        
        # Circuit breaker
        if self.circuit_breaker:
            self.circuit_breaker.record_success()
        
        # Store metrics in Redis
        if self._initialized:
            asyncio.create_task(self._store_operation_metric(operation_name, duration_ms, True))
        
        console.print(f"✅ {operation_name} | {duration_ms:.2f}ms", style="green")
    
    def _record_failure(self, error: Exception, duration_ms: float, operation_name: str):
        """Record failed operation"""
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.last_failure_time = datetime.utcnow()
        
        # Track error types
        error_type = type(error).__name__
        self.metrics.error_counts[error_type] += 1
        
        # Store recent error
        self.recent_errors.append({
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation_name,
            'error_type': error_type,
            'error_message': str(error),
            'duration_ms': duration_ms
        })
        
        # Circuit breaker
        if self.circuit_breaker:
            self.circuit_breaker.record_failure()
    
    def record_threat_ingested(self):
        """Record threat successfully ingested"""
        self.metrics.threats_ingested += 1
    
    def record_threat_failed(self, item: Dict, error: Exception):
        """Record threat ingestion failure"""
        self.metrics.threats_failed += 1
        
        # Add to dead letter queue
        self.dead_letter_queue.append({
            'timestamp': datetime.utcnow().isoformat(),
            'item': item,
            'error_type': type(error).__name__,
            'error_message': str(error)
        })
    
    def record_threat_converted(self):
        """Record threat successfully converted"""
        self.metrics.threats_converted += 1
    
    def record_threat_skipped(self, reason: str = "unknown"):
        """Record threat skipped"""
        self.metrics.threats_skipped += 1
        self.metrics.error_counts[f'skipped_{reason}'] += 1
    
    def get_health_status(self) -> Dict:
        """
        Get comprehensive health status
        
        Returns:
            Health status with metrics and alerts
        """
        # Determine overall health
        health = HealthStatus.HEALTHY
        alerts = []
        
        # Check error rate
        error_rate = 100 - self.metrics.success_rate()
        if error_rate > self.alert_thresholds['error_rate']:
            health = HealthStatus.DEGRADED
            alerts.append(f"High error rate: {error_rate:.1f}%")
        
        # Check consecutive failures
        if self.metrics.consecutive_failures >= self.alert_thresholds['consecutive_failures']:
            health = HealthStatus.UNHEALTHY
            alerts.append(f"Consecutive failures: {self.metrics.consecutive_failures}")
        
        # Check circuit breaker
        if self.circuit_breaker and self.circuit_breaker.state == CircuitState.OPEN:
            health = HealthStatus.CRITICAL
            alerts.append("Circuit breaker OPEN - System failing")
        
        # Check average duration
        avg_duration = self.metrics.avg_duration_ms()
        if avg_duration > self.alert_thresholds['avg_duration_ms']:
            health = HealthStatus.DEGRADED
            alerts.append(f"Slow performance: {avg_duration:.0f}ms avg")
        
        # Check dead letter queue
        dlq_size = len(self.dead_letter_queue)
        if dlq_size > self.alert_thresholds['dead_letter_queue_size']:
            health = HealthStatus.DEGRADED
            alerts.append(f"Dead letter queue size: {dlq_size}")
        
        return {
            'status': health.value,
            'alerts': alerts,
            'metrics': self.metrics.to_dict(),
            'circuit_breaker': {
                'state': self.circuit_breaker.state.value if self.circuit_breaker else 'disabled',
                'failure_count': self.circuit_breaker.failure_count if self.circuit_breaker else 0
            },
            'dead_letter_queue_size': dlq_size,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_metrics_summary(self) -> Dict:
        """Get metrics summary for dashboards"""
        return {
            'requests': {
                'total': self.metrics.total_requests,
                'successful': self.metrics.successful_requests,
                'failed': self.metrics.failed_requests,
                'success_rate': round(self.metrics.success_rate(), 2)
            },
            'threats': {
                'ingested': self.metrics.threats_ingested,
                'failed': self.metrics.threats_failed,
                'converted': self.metrics.threats_converted,
                'skipped': self.metrics.threats_skipped
            },
            'performance': {
                'avg_ms': round(self.metrics.avg_duration_ms(), 2),
                'min_ms': round(self.metrics.min_duration_ms, 2) if self.metrics.min_duration_ms != float('inf') else 0,
                'max_ms': round(self.metrics.max_duration_ms, 2)
            },
            'errors': {
                'top_errors': sorted(
                    self.metrics.error_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            }
        }
    
    def get_dead_letter_queue(self, limit: int = 100) -> List[Dict]:
        """Get failed items from dead letter queue"""
        return list(self.dead_letter_queue)[-limit:]
    
    def get_recent_errors(self, limit: int = 20) -> List[Dict]:
        """Get recent errors for debugging"""
        return list(self.recent_errors)[-limit:]
    
    def reset_metrics(self):
        """Reset all metrics (for testing or periodic reset)"""
        logger.info("🔄 Resetting metrics")
        self.metrics = Metrics()
        if self.circuit_breaker:
            self.circuit_breaker = CircuitBreaker()
    
    def export_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format
        
        Returns:
            Prometheus-formatted metrics
        """
        lines = [
            "# HELP periscope_requests_total Total number of requests",
            f"periscope_requests_total {self.metrics.total_requests}",
            "",
            "# HELP periscope_requests_success Successful requests",
            f"periscope_requests_success {self.metrics.successful_requests}",
            "",
            "# HELP periscope_requests_failed Failed requests",
            f"periscope_requests_failed {self.metrics.failed_requests}",
            "",
            "# HELP periscope_threats_ingested Threats ingested",
            f"periscope_threats_ingested {self.metrics.threats_ingested}",
            "",
            "# HELP periscope_threats_failed Threats failed",
            f"periscope_threats_failed {self.metrics.threats_failed}",
            "",
            "# HELP periscope_avg_duration_ms Average duration in milliseconds",
            f"periscope_avg_duration_ms {self.metrics.avg_duration_ms():.2f}",
            "",
            "# HELP periscope_success_rate Success rate percentage",
            f"periscope_success_rate {self.metrics.success_rate():.2f}",
            ""
        ]
        
        return "\n".join(lines)
    
    async def _store_operation_metric(self, operation: str, duration_ms: float, success: bool):
        """Store operation metrics in Redis"""
        try:
            # Increment operation counter
            await self.redis.incr(f"metrics:periscope:operations:{operation}")
            
            # Store latency
            await self.redis.lpush(f"metrics:periscope:latency:{operation}", duration_ms)
            await self.redis.ltrim(f"metrics:periscope:latency:{operation}", 0, 999)
            
            # Store success/failure
            status = "success" if success else "failure"
            await self.redis.incr(f"metrics:periscope:status:{status}")
        except Exception as e:
            logger.warning(f"Failed to store metrics in Redis: {e}")
    
    async def get_gpu_stats(self) -> Dict[str, Any]:
        """Get GPU utilization stats using nvidia-smi"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,memory.used,memory.total,utilization.gpu,temperature.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            gpus = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) == 5:
                        gpus.append({
                            'index': int(parts[0]),
                            'memory_used_mb': int(parts[1]),
                            'memory_total_mb': int(parts[2]),
                            'utilization': int(parts[3]),
                            'temperature_c': int(parts[4])
                        })
            
            return {
                'gpu_count': len(gpus),
                'gpus': gpus,
                'total_memory_used_mb': sum(g['memory_used_mb'] for g in gpus),
                'avg_utilization': sum(g['utilization'] for g in gpus) / len(gpus) if gpus else 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system resource statistics"""
        try:
            mem_info = self.process.memory_info()
            sys_mem = psutil.virtual_memory()
            
            return {
                'process_memory_mb': mem_info.rss / 1024 / 1024,
                'process_cpu_percent': self.process.cpu_percent(),
                'system_memory_available_gb': sys_mem.available / 1024 / 1024 / 1024,
                'system_memory_percent': sys_mem.percent,
                'system_cpu_percent': psutil.cpu_percent()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def log_metrics(self):
        """Log current metrics with rich formatting"""
        summary = self.get_metrics_summary()
        
        console.print("\n" + "=" * 80, style="bold blue")
        console.print("📊 PERISCOPE METRICS SUMMARY", style="bold blue")
        console.print("=" * 80, style="bold blue")
        
        console.print(f"\n📈 Requests: {summary['requests']['total']} total | "
                     f"{summary['requests']['success_rate']}% success", style="cyan")
        console.print(f"🎯 Threats: {summary['threats']['ingested']} ingested | "
                     f"{summary['threats']['failed']} failed", style="cyan")
        console.print(f"⚡ Performance: {summary['performance']['avg_ms']}ms avg | "
                     f"{summary['performance']['min_ms']}-{summary['performance']['max_ms']}ms range", style="cyan")
        
        if self.metrics.error_counts:
            console.print(f"\n⚠️  Top Errors:", style="yellow")
            for error, count in summary['errors']['top_errors'][:3]:
                console.print(f"   - {error}: {count}", style="yellow")
        
        # System stats
        sys_stats = self.get_system_stats()
        console.print(f"\n💻 System: {sys_stats.get('process_memory_mb', 0):.1f}MB RAM | "
                     f"{sys_stats.get('process_cpu_percent', 0):.1f}% CPU", style="magenta")
        
        console.print("=" * 80 + "\n", style="bold blue")


# Global monitor instance
_global_monitor: Optional[PeriscopeMonitor] = None


def get_monitor() -> PeriscopeMonitor:
    """Get global monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PeriscopeMonitor()
    return _global_monitor


def reset_monitor():
    """Reset global monitor"""
    global _global_monitor
    _global_monitor = None
