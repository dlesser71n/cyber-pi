#!/usr/bin/env python3
"""
Cyber-PI Stress Test Runner
Executes comprehensive stress tests and generates performance reports
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import argparse

# Import test modules
from real_data_stress_test import RealDataStressTest
from comprehensive_stress_test import ComprehensiveStressTest


class StressTestRunner:
    """Runner for Cyber-PI stress tests"""

    def __init__(self):
        self.results_dir = Path("stress_test_results")
        self.results_dir.mkdir(exist_ok=True)

    async def run_quick_test(self) -> Dict[str, Any]:
        """Run quick comprehensive test"""
        print("⚡ Running Quick Comprehensive Test")
        tester = ComprehensiveStressTest()
        return await tester.run_comprehensive_test_suite()

    async def run_real_data_test(self) -> Dict[str, Any]:
        """Run real data stress test"""
        print("🔬 Running Real Data Stress Test")
        tester = RealDataStressTest()
        return await tester.run_real_data_stress_test()

    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("🚀 Running Full Cyber-PI Stress Test Suite")

        results = {
            "test_suite": "full_stress_test",
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }

        # Run comprehensive test
        print("\n📊 Phase 1: Comprehensive System Test")
        comp_tester = ComprehensiveStressTest()
        comp_results = await comp_tester.run_comprehensive_test_suite()
        results["tests"]["comprehensive"] = comp_results

        # Run real data test
        print("\n📈 Phase 2: Real Data Stress Test")
        real_tester = RealDataStressTest()
        real_results = await real_tester.run_real_data_stress_test()
        results["tests"]["real_data"] = real_results

        # Generate combined analysis
        results["combined_analysis"] = self._generate_combined_analysis(
            comp_results, real_results
        )

        return results

    def _generate_combined_analysis(self, comp_results: Dict, real_results: Dict) -> Dict[str, Any]:
        """Generate combined analysis from both test suites"""
        analysis = {
            "overall_performance_score": 0,
            "system_recommendations": [],
            "critical_thresholds": {},
            "performance_comparison": {}
        }

        # Extract performance scores
        comp_perf = comp_results.get("performance_analysis", {})
        real_perf = real_results.get("performance_analysis", {})

        # Calculate overall score (0-100)
        comp_score = self._performance_to_score(comp_perf.get("overall_performance", "unknown"))
        real_score = self._performance_to_score(real_perf.get("overall_performance", "unknown"))
        analysis["overall_performance_score"] = int((comp_score + real_score) / 2)

        # Combine recommendations
        comp_recs = comp_results.get("recommendations", [])
        real_recs = real_results.get("recommendations", [])
        analysis["system_recommendations"] = list(set(comp_recs + real_recs))

        # Extract critical thresholds
        comp_thresholds = comp_results.get("thresholds_determined", {})
        real_thresholds = real_results.get("thresholds_determined", {})
        analysis["critical_thresholds"] = {**comp_thresholds, **real_thresholds}

        # Performance comparison
        analysis["performance_comparison"] = {
            "comprehensive_test": comp_perf,
            "real_data_test": real_perf,
            "performance_delta": self._calculate_performance_delta(comp_results, real_results)
        }

        return analysis

    def _performance_to_score(self, performance: str) -> int:
        """Convert performance rating to numeric score"""
        scores = {
            "excellent": 95,
            "good": 80,
            "acceptable": 65,
            "needs_improvement": 45,
            "poor": 25,
            "unknown": 50
        }
        return scores.get(performance, 50)

    def _calculate_performance_delta(self, comp_results: Dict, real_results: Dict) -> Dict[str, Any]:
        """Calculate performance differences between test types"""
        delta = {}

        # Compare query times
        comp_query = comp_results.get("system_metrics", {}).get("avg_query_response_times", 0)
        real_query = real_results.get("system_metrics", {}).get("avg_query_response_times", 0)

        if comp_query > 0 and real_query > 0:
            delta["query_time_difference_seconds"] = real_query - comp_query
            delta["query_time_percent_change"] = ((real_query - comp_query) / comp_query) * 100

        return delta

    def save_results(self, results: Dict[str, Any], test_name: str) -> str:
        """Save test results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{test_name}_{timestamp}.json"
        filepath = self.results_dir / filename

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        return str(filepath)

    def print_summary(self, results: Dict[str, Any], test_name: str):
        """Print test summary"""
        print(f"\n🎯 {test_name.upper()} SUMMARY")
        print("=" * 60)

        if "error" in results:
            print(f"❌ Test failed: {results['error']}")
            return

        # Print key metrics
        if "combined_analysis" in results:
            analysis = results["combined_analysis"]
            print(f"📊 Overall Performance Score: {analysis['overall_performance_score']}/100")

            thresholds = analysis.get("critical_thresholds", {})
            if "max_concurrent_users" in thresholds:
                print(f"👥 Max Concurrent Users: {thresholds['max_concurrent_users']}")

            recommendations = analysis.get("system_recommendations", [])
            if recommendations:
                print(f"💡 Top Recommendations:")
                for rec in recommendations[:3]:
                    print(f"   • {rec}")

        elif "performance_analysis" in results:
            analysis = results["performance_analysis"]
            print(f"📊 Performance: {analysis.get('overall_performance', 'unknown')}")
            print(f"🏥 System Health: {analysis.get('system_health', 'unknown')}")
            print(f"📈 Scalability: {analysis.get('scalability_rating', 'unknown')}")

        # Print test duration
        if "test_metadata" in results:
            duration = results["test_metadata"].get("duration_seconds", 0)
            print(f"⏱️  Test Duration: {duration:.1f} seconds")
        print("✅ Test completed successfully!")


async def main():
    """Main runner function"""
    parser = argparse.ArgumentParser(description="Cyber-PI Stress Test Runner")
    parser.add_argument(
        "test_type",
        choices=["quick", "real", "full"],
        help="Type of stress test to run"
    )
    parser.add_argument(
        "--output",
        help="Output filename (optional)"
    )

    args = parser.parse_args()

    runner = StressTestRunner()

    try:
        if args.test_type == "quick":
            results = await runner.run_quick_test()
            test_name = "quick_comprehensive"

        elif args.test_type == "real":
            results = await runner.run_real_data_test()
            test_name = "real_data_stress"

        elif args.test_type == "full":
            results = await runner.run_full_test_suite()
            test_name = "full_stress_suite"

        # Save results
        if args.output:
            filepath = runner.save_results(results, args.output)
        else:
            filepath = runner.save_results(results, test_name)

        print(f"📊 Results saved to: {filepath}")

        # Print summary
        runner.print_summary(results, test_name)

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
