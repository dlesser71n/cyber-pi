"""
Automatic Failover Mechanism for Redis-First Architecture
Handles service failures gracefully with fallback strategies
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)

class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ServiceHealth:
    """Health status for a service"""
    name: str
    status: ServiceStatus
    last_check: float
    consecutive_failures: int = 0
    error_rate: float = 0.0
    latency_ms: float = 0.0
    circuit_breaker_open: bool = False
    circuit_breaker_until: float = 0.0

@dataclass
class FailoverConfig:
    """Failover configuration"""
    health_check_interval: int = 5  # seconds
    failure_threshold: int = 3  # consecutive failures to mark unhealthy
    recovery_threshold: int = 2  # consecutive successes to mark healthy
    circuit_breaker_timeout: int = 30  # seconds
    error_rate_threshold: float = 0.5  # 50% error rate
    latency_threshold_ms: float = 1000  # 1 second
    
class FailoverManager:
    """
    Manages automatic failover between Redis and Kafka
    Implements circuit breaker pattern for resilience
    """
    
    def __init__(self, 
                 redis_client,
                 kafka_producer,
                 config: Optional[FailoverConfig] = None):
        self.redis = redis_client
        self.kafka = kafka_producer
        self.config = config or FailoverConfig()
        
        # Service health tracking
        self.services: Dict[str, ServiceHealth] = {
            "redis": ServiceHealth("redis", ServiceStatus.UNKNOWN, time.time()),
            "kafka": ServiceHealth("kafka", ServiceStatus.UNKNOWN, time.time())
        }
        
        # Metrics tracking
        self.metrics = {
            "redis": {"total": 0, "failures": 0, "latencies": []},
            "kafka": {"total": 0, "failures": 0, "latencies": []}
        }
        
        # Failover state
        self.primary_service = "redis"  # Redis-first by default
        self.failover_active = False
        self.failover_history: List[Dict] = []
        
        # Callbacks for failover events
        self.failover_callbacks: List[Callable] = []
    
    async def check_redis_health(self) -> ServiceHealth:
        """Check Redis health status"""
        start = time.time()
        health = self.services["redis"]
        
        try:
            # Ping Redis
            await asyncio.wait_for(self.redis.ping(), timeout=2.0)
            
            # Test write/read
            test_key = "_health_check"
            test_value = str(time.time())
            await self.redis.set(test_key, test_value)
            result = await self.redis.get(test_key)
            
            if result != test_value:
                raise ValueError("Read/write test failed")
            
            # Success
            latency = (time.time() - start) * 1000
            health.latency_ms = latency
            health.consecutive_failures = 0
            
            # Check latency threshold
            if latency > self.config.latency_threshold_ms:
                health.status = ServiceStatus.DEGRADED
                logger.warning(f"Redis degraded: high latency {latency:.2f}ms")
            else:
                health.status = ServiceStatus.HEALTHY
            
        except asyncio.TimeoutError:
            health.consecutive_failures += 1
            health.status = ServiceStatus.UNHEALTHY
            logger.error("Redis health check timeout")
            
        except Exception as e:
            health.consecutive_failures += 1
            health.status = ServiceStatus.UNHEALTHY
            logger.error(f"Redis health check failed: {e}")
        
        health.last_check = time.time()
        
        # Check circuit breaker
        if health.consecutive_failures >= self.config.failure_threshold:
            self._open_circuit_breaker("redis")
        elif health.consecutive_failures == 0 and health.circuit_breaker_open:
            if time.time() > health.circuit_breaker_until:
                self._close_circuit_breaker("redis")
        
        return health
    
    async def check_kafka_health(self) -> ServiceHealth:
        """Check Kafka health status"""
        start = time.time()
        health = self.services["kafka"]
        
        try:
            # Check producer connection
            metadata = await asyncio.wait_for(
                self.kafka.client._metadata.fetch(),
                timeout=2.0
            )
            
            if not metadata.brokers:
                raise ValueError("No Kafka brokers available")
            
            # Test produce (to a test topic)
            test_topic = "_health_check"
            test_message = {"timestamp": time.time()}
            
            await self.kafka.send(
                test_topic,
                value=json.dumps(test_message).encode()
            )
            
            # Success
            latency = (time.time() - start) * 1000
            health.latency_ms = latency
            health.consecutive_failures = 0
            
            # Check latency threshold
            if latency > self.config.latency_threshold_ms * 2:  # Higher threshold for Kafka
                health.status = ServiceStatus.DEGRADED
                logger.warning(f"Kafka degraded: high latency {latency:.2f}ms")
            else:
                health.status = ServiceStatus.HEALTHY
            
        except asyncio.TimeoutError:
            health.consecutive_failures += 1
            health.status = ServiceStatus.UNHEALTHY
            logger.error("Kafka health check timeout")
            
        except Exception as e:
            health.consecutive_failures += 1
            health.status = ServiceStatus.UNHEALTHY
            logger.error(f"Kafka health check failed: {e}")
        
        health.last_check = time.time()
        
        # Check circuit breaker
        if health.consecutive_failures >= self.config.failure_threshold:
            self._open_circuit_breaker("kafka")
        elif health.consecutive_failures == 0 and health.circuit_breaker_open:
            if time.time() > health.circuit_breaker_until:
                self._close_circuit_breaker("kafka")
        
        return health
    
    def _open_circuit_breaker(self, service: str):
        """Open circuit breaker for a service"""
        health = self.services[service]
        
        if not health.circuit_breaker_open:
            health.circuit_breaker_open = True
            health.circuit_breaker_until = time.time() + self.config.circuit_breaker_timeout
            
            logger.warning(f"Circuit breaker OPENED for {service}",
                          failures=health.consecutive_failures)
            
            # Trigger failover if this was primary
            if service == self.primary_service:
                asyncio.create_task(self._handle_failover(service))
    
    def _close_circuit_breaker(self, service: str):
        """Close circuit breaker for a service"""
        health = self.services[service]
        health.circuit_breaker_open = False
        health.circuit_breaker_until = 0
        
        logger.info(f"Circuit breaker CLOSED for {service} - service recovered")
        
        # Consider failback if this was original primary
        if service == "redis" and self.primary_service == "kafka":
            asyncio.create_task(self._handle_failback())
    
    async def _handle_failover(self, failed_service: str):
        """Handle failover from failed service"""
        if failed_service == "redis":
            # Failover to Kafka
            if self.services["kafka"].status == ServiceStatus.HEALTHY:
                self.primary_service = "kafka"
                self.failover_active = True
                
                event = {
                    "timestamp": time.time(),
                    "from": "redis",
                    "to": "kafka",
                    "reason": f"Redis unhealthy: {self.services['redis'].consecutive_failures} failures"
                }
                
                self.failover_history.append(event)
                logger.warning("FAILOVER: Redis -> Kafka", event=event)
                
                # Notify callbacks
                for callback in self.failover_callbacks:
                    await callback(event)
            else:
                logger.error("Cannot failover: Kafka also unhealthy")
        
        elif failed_service == "kafka":
            # Already on Redis (primary), just log
            logger.warning("Kafka failed but Redis still primary")
    
    async def _handle_failback(self):
        """Handle failback to original primary (Redis)"""
        if self.failover_active and self.services["redis"].status == ServiceStatus.HEALTHY:
            self.primary_service = "redis"
            self.failover_active = False
            
            event = {
                "timestamp": time.time(),
                "from": "kafka",
                "to": "redis",
                "reason": "Redis recovered and healthy"
            }
            
            self.failover_history.append(event)
            logger.info("FAILBACK: Kafka -> Redis", event=event)
            
            # Notify callbacks
            for callback in self.failover_callbacks:
                await callback(event)
    
    async def monitor_health(self):
        """Background task to monitor service health"""
        while True:
            try:
                # Check both services
                await asyncio.gather(
                    self.check_redis_health(),
                    self.check_kafka_health(),
                    return_exceptions=True
                )
                
                # Update error rates
                for service in ["redis", "kafka"]:
                    metrics = self.metrics[service]
                    if metrics["total"] > 0:
                        self.services[service].error_rate = (
                            metrics["failures"] / metrics["total"]
                        )
                
                # Log health status
                logger.debug("Health check completed",
                            redis=self.services["redis"].status.value,
                            kafka=self.services["kafka"].status.value,
                            primary=self.primary_service)
                
                await asyncio.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(self.config.health_check_interval)
    
    def record_operation(self, service: str, success: bool, latency_ms: float):
        """Record operation metrics for health tracking"""
        metrics = self.metrics[service]
        metrics["total"] += 1
        
        if not success:
            metrics["failures"] += 1
        
        # Keep last 100 latencies
        metrics["latencies"].append(latency_ms)
        if len(metrics["latencies"]) > 100:
            metrics["latencies"].pop(0)
        
        # Update error rate
        if metrics["total"] > 0:
            self.services[service].error_rate = metrics["failures"] / metrics["total"]
    
    def get_routing_decision(self) -> Dict[str, Any]:
        """
        Get current routing decision based on health
        
        Returns which service to use and fallback strategy
        """
        redis_health = self.services["redis"]
        kafka_health = self.services["kafka"]
        
        # Circuit breaker check
        if redis_health.circuit_breaker_open:
            if kafka_health.status == ServiceStatus.HEALTHY:
                return {
                    "primary": "kafka",
                    "fallback": None,
                    "reason": "Redis circuit breaker open"
                }
            else:
                return {
                    "primary": None,
                    "fallback": None,
                    "reason": "Both services unavailable"
                }
        
        # Normal routing (Redis-first)
        if redis_health.status == ServiceStatus.HEALTHY:
            return {
                "primary": "redis",
                "fallback": "kafka" if kafka_health.status == ServiceStatus.HEALTHY else None,
                "reason": "Redis healthy (primary)"
            }
        
        # Redis degraded
        if redis_health.status == ServiceStatus.DEGRADED:
            if kafka_health.status == ServiceStatus.HEALTHY:
                return {
                    "primary": "redis",  # Still try Redis first
                    "fallback": "kafka",
                    "reason": "Redis degraded, Kafka available as fallback"
                }
        
        # Redis unhealthy
        if kafka_health.status == ServiceStatus.HEALTHY:
            return {
                "primary": "kafka",
                "fallback": None,
                "reason": "Redis unhealthy, using Kafka"
            }
        
        # Both unhealthy - try Redis anyway (it's faster to fail)
        return {
            "primary": "redis",
            "fallback": None,
            "reason": "Both services unhealthy, attempting Redis"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get complete failover status"""
        return {
            "primary_service": self.primary_service,
            "failover_active": self.failover_active,
            "services": {
                name: {
                    "status": health.status.value,
                    "consecutive_failures": health.consecutive_failures,
                    "error_rate": f"{health.error_rate * 100:.1f}%",
                    "latency_ms": health.latency_ms,
                    "circuit_breaker": "OPEN" if health.circuit_breaker_open else "CLOSED",
                    "last_check": time.time() - health.last_check
                }
                for name, health in self.services.items()
            },
            "routing_decision": self.get_routing_decision(),
            "failover_history": self.failover_history[-10:]  # Last 10 events
        }
    
    def register_failover_callback(self, callback: Callable):
        """Register callback for failover events"""
        self.failover_callbacks.append(callback)

import json  # Add at top of file for JSON operations

# Example usage and integration
async def create_resilient_router(redis_client, kafka_producer):
    """Create router with automatic failover"""
    
    # Create failover manager
    failover_config = FailoverConfig(
        health_check_interval=5,
        failure_threshold=3,
        circuit_breaker_timeout=30
    )
    
    failover_manager = FailoverManager(
        redis_client,
        kafka_producer,
        failover_config
    )
    
    # Start health monitoring
    asyncio.create_task(failover_manager.monitor_health())
    
    # Register failover callback
    async def on_failover(event):
        logger.warning(f"Failover occurred: {event}")
        # Could send alerts, update metrics, etc.
    
    failover_manager.register_failover_callback(on_failover)
    
    return failover_manager