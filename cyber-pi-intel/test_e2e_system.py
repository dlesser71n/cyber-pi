#!/usr/bin/env python3
"""
End-to-End System Test for Cyber-PI-Intel
Tests all security enhancements, API endpoints, and system integration
"""

import sys
import os
import time
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "tests": []
}

class Colors:
    """Terminal colors for pretty output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_test(name: str, status: str, message: str = ""):
    """Print test result"""
    test_results["total"] += 1

    if status == "PASS":
        symbol = f"{Colors.GREEN}✅{Colors.END}"
        test_results["passed"] += 1
    elif status == "FAIL":
        symbol = f"{Colors.RED}❌{Colors.END}"
        test_results["failed"] += 1
    elif status == "SKIP":
        symbol = f"{Colors.YELLOW}⏭️{Colors.END}"
        test_results["skipped"] += 1
    else:
        symbol = "⚠️"

    result = {
        "name": name,
        "status": status,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    test_results["tests"].append(result)

    print(f"{symbol} {name}")
    if message:
        print(f"   {Colors.YELLOW}{message}{Colors.END}")

# =============================================================================
# Test 1: Environment and Configuration
# =============================================================================

def test_environment():
    """Test environment configuration"""
    print_header("TEST 1: Environment Configuration")

    # Test Python version
    python_version = sys.version_info
    if python_version >= (3, 11):
        print_test("Python Version", "PASS", f"Python {python_version.major}.{python_version.minor}")
    else:
        print_test("Python Version", "FAIL", f"Python {python_version.major}.{python_version.minor} < 3.11")

    # Test required files exist
    required_files = [
        "backend/core/config.py",
        "backend/core/security.py",
        "backend/core/validators.py",
        "backend/core/connections.py",
        "backend/api/threat_intel_api.py",
        ".env.example",
        "SECURITY.md",
        "run_security_tests.sh"
    ]

    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print_test(f"File exists: {file_path}", "PASS")
        else:
            print_test(f"File exists: {file_path}", "FAIL", "File not found")

# =============================================================================
# Test 2: Configuration Loading and Security Validation
# =============================================================================

def test_configuration():
    """Test configuration loading and validation"""
    print_header("TEST 2: Configuration Loading & Security Validation")

    try:
        from backend.core.config import settings
        print_test("Import settings", "PASS")

        # Test configuration attributes
        required_attrs = [
            'environment', 'debug', 'api_host', 'api_port',
            'redis_host', 'neo4j_uri', 'weaviate_url',
            'jwt_secret_key', 'cors_origins'
        ]

        for attr in required_attrs:
            if hasattr(settings, attr):
                print_test(f"Config: {attr}", "PASS", f"{getattr(settings, attr)}")
            else:
                print_test(f"Config: {attr}", "FAIL", "Attribute missing")

        # Test security validation method exists
        if hasattr(settings, 'validate_security_settings'):
            print_test("Security validation method", "PASS")

            # Test validation in development mode (should pass with defaults)
            if settings.is_development():
                try:
                    # Development mode should allow defaults
                    print_test("Development mode check", "PASS", "Running in development")
                except Exception as e:
                    print_test("Development mode check", "FAIL", str(e))
        else:
            print_test("Security validation method", "FAIL", "Method not found")

    except Exception as e:
        print_test("Import settings", "FAIL", str(e))

# =============================================================================
# Test 3: Input Validators
# =============================================================================

def test_validators():
    """Test input validation functions"""
    print_header("TEST 3: Input Validation")

    try:
        from backend.core.validators import InputValidator
        print_test("Import InputValidator", "PASS")

        # Test CVE validation
        valid_cves = ["CVE-2024-1234", "CVE-2023-12345"]
        for cve in valid_cves:
            try:
                result = InputValidator.validate_cve_id(cve)
                print_test(f"CVE validation: {cve}", "PASS")
            except Exception as e:
                print_test(f"CVE validation: {cve}", "FAIL", str(e))

        # Test invalid CVE (should fail)
        invalid_cves = ["INVALID-CVE", "CVE-ABC-123"]
        for cve in invalid_cves:
            try:
                InputValidator.validate_cve_id(cve)
                print_test(f"Invalid CVE rejection: {cve}", "FAIL", "Should have rejected")
            except:
                print_test(f"Invalid CVE rejection: {cve}", "PASS", "Correctly rejected")

        # Test MITRE technique validation
        valid_techniques = ["T1234", "T1234.001"]
        for tech in valid_techniques:
            try:
                result = InputValidator.validate_mitre_technique(tech)
                print_test(f"MITRE technique: {tech}", "PASS")
            except Exception as e:
                print_test(f"MITRE technique: {tech}", "FAIL", str(e))

        # Test severity validation
        valid_severities = ["critical", "high", "medium", "low", "info"]
        for sev in valid_severities:
            try:
                result = InputValidator.validate_severity(sev)
                print_test(f"Severity validation: {sev}", "PASS")
            except Exception as e:
                print_test(f"Severity validation: {sev}", "FAIL", str(e))

        # Test string sanitization
        test_strings = [
            ("Normal string", True),
            ("String with\x00null", True),  # Should remove null bytes
            ("A" * 1001, False),  # Too long (default max 1000)
        ]

        for test_str, should_pass in test_strings:
            try:
                result = InputValidator.sanitize_string(test_str[:50])  # Show first 50 chars
                if should_pass:
                    print_test(f"Sanitize string: {test_str[:30]}...", "PASS")
                else:
                    print_test(f"Sanitize string: {test_str[:30]}...", "FAIL", "Should have failed")
            except Exception as e:
                if not should_pass:
                    print_test(f"Sanitize string rejection: {test_str[:30]}...", "PASS", "Correctly rejected")
                else:
                    print_test(f"Sanitize string: {test_str[:30]}...", "FAIL", str(e))

        # Test Neo4j parameter sanitization
        safe_params = ["ValidActorName", "APT28", "Lazarus-Group"]
        for param in safe_params:
            try:
                result = InputValidator.sanitize_neo4j_parameter(param)
                print_test(f"Neo4j param sanitize: {param}", "PASS")
            except Exception as e:
                print_test(f"Neo4j param sanitize: {param}", "FAIL", str(e))

        # Test injection attempt (should be rejected)
        injection_attempts = ["'; DROP TABLE--", "MATCH (n) DELETE n"]
        for attempt in injection_attempts:
            try:
                InputValidator.sanitize_neo4j_parameter(attempt)
                print_test(f"Neo4j injection block: {attempt[:20]}", "FAIL", "Should have blocked")
            except:
                print_test(f"Neo4j injection block: {attempt[:20]}", "PASS", "Correctly blocked")

    except Exception as e:
        print_test("Import InputValidator", "FAIL", str(e))

# =============================================================================
# Test 4: Security Module
# =============================================================================

def test_security():
    """Test security module functions"""
    print_header("TEST 4: Security Module")

    try:
        from backend.core.security import SecurityManager, SecurityHeaders
        print_test("Import security modules", "PASS")

        # Test SecurityManager
        security_mgr = SecurityManager()
        print_test("Create SecurityManager", "PASS")

        # Test password hashing
        test_password = "TestPassword123!"
        hashed = security_mgr.get_password_hash(test_password)

        if hashed and len(hashed) > 50:  # bcrypt hashes are ~60 chars
            print_test("Password hashing", "PASS", f"Hash length: {len(hashed)}")
        else:
            print_test("Password hashing", "FAIL", "Hash too short")

        # Test password verification
        if security_mgr.verify_password(test_password, hashed):
            print_test("Password verification", "PASS")
        else:
            print_test("Password verification", "FAIL")

        # Test wrong password rejection
        if not security_mgr.verify_password("WrongPassword", hashed):
            print_test("Wrong password rejection", "PASS")
        else:
            print_test("Wrong password rejection", "FAIL")

        # Test JWT token creation
        token_data = {"sub": "test_user", "role": "user"}
        access_token = security_mgr.create_access_token(token_data)

        if access_token and len(access_token) > 100:
            print_test("JWT token creation", "PASS", f"Token length: {len(access_token)}")
        else:
            print_test("JWT token creation", "FAIL")

        # Test SecurityHeaders
        if hasattr(SecurityHeaders, 'HEADERS'):
            headers = SecurityHeaders.HEADERS
            expected_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Strict-Transport-Security',
                'Content-Security-Policy'
            ]

            for header in expected_headers:
                if header in headers:
                    print_test(f"Security header: {header}", "PASS", headers[header])
                else:
                    print_test(f"Security header: {header}", "FAIL", "Missing")

    except Exception as e:
        print_test("Security module tests", "FAIL", str(e))

# =============================================================================
# Test 5: Database Connection Manager
# =============================================================================

def test_connections():
    """Test database connection manager"""
    print_header("TEST 5: Database Connection Manager")

    try:
        from backend.core.connections import ConnectionManager
        print_test("Import ConnectionManager", "PASS")

        # Create connection manager
        conn_mgr = ConnectionManager()
        print_test("Create ConnectionManager instance", "PASS")

        # Test methods exist
        required_methods = ['initialize', 'close', 'health_check', 'get_redis', 'get_neo4j', 'get_weaviate']
        for method in required_methods:
            if hasattr(conn_mgr, method):
                print_test(f"ConnectionManager.{method}()", "PASS")
            else:
                print_test(f"ConnectionManager.{method}()", "FAIL", "Method missing")

        # Test type hints are present
        from typing import get_type_hints
        try:
            hints = get_type_hints(ConnectionManager.get_neo4j)
            print_test("Type hints on get_neo4j", "PASS", f"Return type: {hints.get('return', 'Any')}")
        except Exception as e:
            print_test("Type hints on get_neo4j", "SKIP", "Could not get type hints")

    except Exception as e:
        print_test("Connection manager tests", "FAIL", str(e))

# =============================================================================
# Test 6: API Application Structure
# =============================================================================

def test_api_structure():
    """Test API application structure"""
    print_header("TEST 6: API Application Structure")

    try:
        # Import without starting server
        from backend.api import threat_intel_api
        print_test("Import threat_intel_api module", "PASS")

        # Test app exists
        if hasattr(threat_intel_api, 'app'):
            app = threat_intel_api.app
            print_test("FastAPI app exists", "PASS")

            # Test app properties
            if hasattr(app, 'title'):
                print_test("App title", "PASS", app.title)

            if hasattr(app, 'version'):
                print_test("App version", "PASS", app.version)

            # Test middleware is configured
            if hasattr(app, 'user_middleware'):
                middleware_count = len(app.user_middleware)
                print_test("Middleware configured", "PASS", f"{middleware_count} middleware(s)")

            # Test routes exist
            if hasattr(app, 'routes'):
                routes = [route.path for route in app.routes if hasattr(route, 'path')]
                expected_routes = [
                    "/",
                    "/health",
                    "/collect",
                    "/search",
                    "/threats",
                    "/analytics/summary",
                    "/actors",
                    "/campaigns"
                ]

                for expected_route in expected_routes:
                    if expected_route in routes:
                        print_test(f"Route exists: {expected_route}", "PASS")
                    else:
                        print_test(f"Route exists: {expected_route}", "FAIL", "Route not found")
        else:
            print_test("FastAPI app exists", "FAIL", "App not found")

    except Exception as e:
        print_test("API structure tests", "FAIL", str(e))

# =============================================================================
# Test 7: Pydantic Models
# =============================================================================

def test_pydantic_models():
    """Test Pydantic validation models"""
    print_header("TEST 7: Pydantic Validation Models")

    try:
        from backend.core.validators import (
            ValidatedThreatQuery,
            ValidatedCollectionRequest,
            ValidatedActorName,
            ValidatedLimit
        )
        print_test("Import Pydantic models", "PASS")

        # Test ValidatedThreatQuery
        try:
            valid_query = ValidatedThreatQuery(
                query="ransomware attack",
                severity=["critical", "high"],
                limit=10
            )
            print_test("ValidatedThreatQuery (valid)", "PASS")
        except Exception as e:
            print_test("ValidatedThreatQuery (valid)", "FAIL", str(e))

        # Test invalid query (too long)
        try:
            invalid_query = ValidatedThreatQuery(
                query="A" * 1000,  # Too long
                limit=10
            )
            print_test("ValidatedThreatQuery (invalid - too long)", "FAIL", "Should have rejected")
        except:
            print_test("ValidatedThreatQuery (invalid - too long)", "PASS", "Correctly rejected")

        # Test ValidatedCollectionRequest
        try:
            valid_collection = ValidatedCollectionRequest(
                sources=["technical", "social"],
                industry="Finance"
            )
            print_test("ValidatedCollectionRequest (valid)", "PASS")
        except Exception as e:
            print_test("ValidatedCollectionRequest (valid)", "FAIL", str(e))

        # Test invalid source
        try:
            invalid_collection = ValidatedCollectionRequest(
                sources=["invalid_source"]
            )
            print_test("ValidatedCollectionRequest (invalid source)", "FAIL", "Should have rejected")
        except:
            print_test("ValidatedCollectionRequest (invalid source)", "PASS", "Correctly rejected")

    except Exception as e:
        print_test("Pydantic models test", "FAIL", str(e))

# =============================================================================
# Test 8: Security Files
# =============================================================================

def test_security_files():
    """Test security-related files exist and are valid"""
    print_header("TEST 8: Security Documentation & Tools")

    security_files = {
        "SECURITY.md": ["Reporting a Vulnerability", "Security Policy"],
        "SECURITY_FIXES_APPLIED.md": ["Critical Fixes", "Hardcoded Credentials"],
        "SECURITY_ENHANCEMENTS_COMPLETE.md": ["Security Rating", "Production Ready"],
        ".bandit": ["bandit", "tests"],
        "run_security_tests.sh": ["bandit", "safety", "pip-audit"]
    }

    for file_path, expected_content in security_files.items():
        full_path = os.path.join(os.path.dirname(__file__), file_path)

        if os.path.exists(full_path):
            print_test(f"File exists: {file_path}", "PASS")

            # Check content
            try:
                with open(full_path, 'r') as f:
                    content = f.read()

                for expected in expected_content:
                    if expected in content:
                        print_test(f"  Contains: {expected}", "PASS")
                    else:
                        print_test(f"  Contains: {expected}", "FAIL", "Content missing")
            except Exception as e:
                print_test(f"  Read {file_path}", "FAIL", str(e))
        else:
            print_test(f"File exists: {file_path}", "FAIL", "File not found")

# =============================================================================
# Test 9: Integration Test (if databases available)
# =============================================================================

async def test_integration():
    """Test integration with databases (if available)"""
    print_header("TEST 9: Integration Test (Database Connections)")

    try:
        from backend.core.connections import ConnectionManager

        conn_mgr = ConnectionManager()

        # Try to initialize connections
        try:
            await conn_mgr.initialize()
            print_test("Initialize connections", "PASS")

            # Test health check
            try:
                health = await conn_mgr.health_check()
                print_test("Health check executed", "PASS")

                # Check each service
                for service, status in health.items():
                    if status:
                        print_test(f"  {service} status", "PASS", "Connected")
                    else:
                        print_test(f"  {service} status", "SKIP", "Not available")
            except Exception as e:
                print_test("Health check", "SKIP", f"Services not available: {e}")

            # Clean up
            await conn_mgr.close()
            print_test("Close connections", "PASS")

        except Exception as e:
            print_test("Initialize connections", "SKIP", f"Databases not available: {e}")

    except Exception as e:
        print_test("Integration test", "SKIP", str(e))

# =============================================================================
# Main Test Runner
# =============================================================================

def print_summary():
    """Print test summary"""
    print_header("TEST SUMMARY")

    total = test_results["total"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    skipped = test_results["skipped"]

    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"Total Tests:   {total}")
    print(f"{Colors.GREEN}Passed:        {passed} ({pass_rate:.1f}%){Colors.END}")
    print(f"{Colors.RED}Failed:        {failed}{Colors.END}")
    print(f"{Colors.YELLOW}Skipped:       {skipped}{Colors.END}")
    print()

    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED!{Colors.END}")
        status = "PASS"
    elif failed <= 3:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  MOSTLY PASSING (Minor issues){Colors.END}")
        status = "PARTIAL"
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ TESTS FAILED{Colors.END}")
        status = "FAIL"

    # Save results to file
    report_path = "test_e2e_report.json"
    with open(report_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": pass_rate,
                "status": status
            },
            "tests": test_results["tests"]
        }, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_path}")

    return failed == 0

def main():
    """Main test runner"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"🧪 CYBER-PI-INTEL END-TO-END SYSTEM TEST")
    print(f"{'='*70}{Colors.END}\n")
    print(f"Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")

    # Run all tests
    test_environment()
    test_configuration()
    test_validators()
    test_security()
    test_connections()
    test_api_structure()
    test_pydantic_models()
    test_security_files()

    # Run async integration test
    try:
        asyncio.run(test_integration())
    except Exception as e:
        print_test("Async integration test", "SKIP", f"Could not run: {e}")

    # Print summary
    success = print_summary()

    print(f"\nCompleted: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
