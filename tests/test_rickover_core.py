#!/usr/bin/env python3
"""
Rickover Standard Test Suite
Nuclear-grade testing for core components
"""

import unittest
import time
from datetime import datetime
from typing import Dict, Any

from src.core.rickover_base import RickoverBase, CircuitBreaker
from src.core.data_validator import DataValidator

class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker functionality"""
    
    def setUp(self):
        self.breaker = CircuitBreaker(failure_threshold=2, reset_timeout=1)
    
    def test_initial_state(self):
        """Test initial circuit breaker state"""
        self.assertEqual(self.breaker.state, "CLOSED")
        self.assertTrue(self.breaker.can_proceed())
    
    def test_open_on_failures(self):
        """Test circuit opens after failures"""
        self.breaker.record_failure()
        self.assertTrue(self.breaker.can_proceed())
        self.breaker.record_failure()
        self.assertEqual(self.breaker.state, "OPEN")
        self.assertFalse(self.breaker.can_proceed())
    
    def test_reset_after_timeout(self):
        """Test circuit resets after timeout"""
        self.breaker.record_failure()
        self.breaker.record_failure()
        self.assertEqual(self.breaker.state, "OPEN")
        time.sleep(1.1)  # Wait for reset timeout
        self.assertTrue(self.breaker.can_proceed())
        self.assertEqual(self.breaker.state, "HALF-OPEN")
    
    def test_close_on_success(self):
        """Test circuit closes after success in half-open state"""
        self.breaker.record_failure()
        self.breaker.record_failure()
        time.sleep(1.1)  # Wait for reset timeout
        self.assertTrue(self.breaker.can_proceed())
        self.breaker.record_success()
        self.assertEqual(self.breaker.state, "CLOSED")

class TestDataValidator(unittest.TestCase):
    """Test data validation functionality"""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_validate_cve(self):
        """Test CVE validation"""
        valid_cve = {
            'cve_id': 'CVE-2024-1234',
            'description': 'Test CVE',
            'published': '2024-01-01T00:00:00Z',
            'cvss_v3_score': 7.5,
            'severity': 'high',
            'cwes': ['CWE-79', 'CWE-89']
        }
        result = self.validator.validate_cve(valid_cve)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)
        
        invalid_cve = {
            'cve_id': 'INVALID-ID',
            'description': 'Test CVE',
            'published': 'invalid-date',
            'cvss_v3_score': 11.0,
            'severity': 'invalid',
            'cwes': ['INVALID-CWE']
        }
        result = self.validator.validate_cve(invalid_cve)
        self.assertFalse(result.valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_validate_threat_intel(self):
        """Test threat intelligence validation"""
        valid_threat = {
            'id': 'threat-0001',
            'title': 'Test Threat',
            'description': 'Test Description',
            'severity': 'high',
            'type': 'malware',
            'source': 'apt28',
            'confidence': 0.85,
            'cves': ['CVE-2024-1234'],
            'cwes': ['CWE-79']
        }
        result = self.validator.validate_threat_intel(valid_threat)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)
        
        invalid_threat = {
            'id': 'threat-0001',
            'title': 'Test Threat',
            'description': 'Test Description',
            'severity': 'invalid',
            'type': 'malware',
            'source': 'apt28',
            'confidence': 2.0,
            'cves': ['INVALID-CVE'],
            'cwes': ['INVALID-CWE']
        }
        result = self.validator.validate_threat_intel(invalid_threat)
        self.assertFalse(result.valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_validate_ioc(self):
        """Test IOC validation"""
        valid_iocs = [
            {
                'value': '192.168.1.1',
                'type': 'ip.ipv4',
                'confidence': 0.9,
                'firstSeen': '2024-01-01T00:00:00Z'
            },
            {
                'value': 'malicious.com',
                'type': 'domain.domain',
                'confidence': 0.8,
                'firstSeen': '2024-01-01T00:00:00Z'
            },
            {
                'value': 'a' * 64,
                'type': 'file.sha256',
                'confidence': 0.95,
                'firstSeen': '2024-01-01T00:00:00Z'
            }
        ]
        
        for ioc in valid_iocs:
            result = self.validator.validate_ioc(ioc)
            self.assertTrue(result.valid, f"Failed to validate {ioc['type']}")
            self.assertEqual(len(result.errors), 0)
        
        invalid_iocs = [
            {
                'value': '999.999.999.999',
                'type': 'ip.ipv4',
                'confidence': 0.9,
                'firstSeen': '2024-01-01T00:00:00Z'
            },
            {
                'value': 'not-a-domain',
                'type': 'domain.domain',
                'confidence': 0.8,
                'firstSeen': '2024-01-01T00:00:00Z'
            },
            {
                'value': 'not-a-hash',
                'type': 'file.sha256',
                'confidence': 0.95,
                'firstSeen': '2024-01-01T00:00:00Z'
            }
        ]
        
        for ioc in invalid_iocs:
            result = self.validator.validate_ioc(ioc)
            self.assertFalse(result.valid, f"Should have failed to validate {ioc['type']}")
            self.assertGreater(len(result.errors), 0)
    
    def test_validate_relationship(self):
        """Test relationship validation"""
        valid_relationships = [
            ('CVE', 'Product', 'AFFECTS'),
            ('Product', 'Vendor', 'MADE_BY'),
            ('ThreatIntel', 'CVE', 'REFERENCES'),
            ('IOC', 'ThreatIntel', 'INDICATES')
        ]
        
        for source, target, rel_type in valid_relationships:
            result = self.validator.validate_relationship(source, target, rel_type)
            self.assertTrue(result.valid)
            self.assertEqual(len(result.errors), 0)
        
        invalid_relationships = [
            ('CVE', 'Vendor', 'INVALID'),
            ('Product', 'ThreatIntel', 'INVALID'),
            ('IOC', 'CVE', 'INVALID')
        ]
        
        for source, target, rel_type in invalid_relationships:
            result = self.validator.validate_relationship(source, target, rel_type)
            self.assertFalse(result.valid)
            self.assertGreater(len(result.errors), 0)

class TestRickoverBase(unittest.TestCase):
    """Test RickoverBase functionality"""
    
    def setUp(self):
        self.base = RickoverBase()
    
    def test_operation_context(self):
        """Test operation context management"""
        with self.base.operation_context("test_operation") as op_id:
            time.sleep(0.1)  # Simulate work
        
        metrics = self.base.get_metrics("test_operation")
        self.assertIn(op_id, metrics)
        self.assertTrue(metrics[op_id].success)
        self.assertGreater(metrics[op_id].end_time - metrics[op_id].start_time, 0)
    
    def test_circuit_breaker_integration(self):
        """Test circuit breaker integration"""
        self.base.register_circuit_breaker("test_operation", failure_threshold=2)
        
        # First failure
        try:
            with self.base.operation_context("test_operation"):
                raise Exception("Test failure")
        except:
            pass
        
        # Should still work
        try:
            with self.base.operation_context("test_operation"):
                pass
        except:
            self.fail("Should not have raised")
        
        # Second failure
        try:
            with self.base.operation_context("test_operation"):
                raise Exception("Test failure")
        except:
            pass
        
        # Should be blocked
        with self.assertRaises(Exception):
            with self.base.operation_context("test_operation"):
                pass
    
    def test_resource_monitoring(self):
        """Test resource monitoring"""
        self.assertIsNotNone(self.base.should_throttle())
        
        # Test metrics collection
        with self.base.operation_context("memory_test") as op_id:
            # Allocate significant memory to ensure detection
            data = ["x" * 1000 for _ in range(100000)]
            # Force memory usage update
            self.base.metrics.update_operation(
                "memory_test",
                op_id,
                memory_peak=self.base.resource_monitor.get_memory_usage()["rss"]
            )
        
        metrics = self.base.get_metrics("memory_test")
        self.assertIn(op_id, metrics)
        self.assertGreater(metrics[op_id].memory_peak, 0)

if __name__ == '__main__':
    unittest.main()
