#!/usr/bin/env python3
"""
Cyber-PI Stress Test Performance Dashboard
Visualize test results and provide performance insights
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import statistics
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np


class PerformanceDashboard:
    """Performance dashboard for stress test results"""

    def __init__(self, results_file: str):
        self.results_file = Path(results_file)
        self.results = self._load_results()

    def _load_results(self) -> Dict[str, Any]:
        """Load test results from file"""
        if not self.results_file.exists():
            print(f"❌ Results file not found: {self.results_file}")
            sys.exit(1)

        with open(self.results_file, 'r') as f:
            return json.load(f)

    def print_executive_summary(self):
        """Print executive summary dashboard"""
        print("🚀 CYBER-PI STRESS TEST PERFORMANCE DASHBOARD")
        print("=" * 80)

        if "error" in self.results:
            print(f"❌ Test Failed: {self.results['error']}")
            return

        # Test metadata
        metadata = self.results.get("test_metadata", {})
        if metadata:
            print(f"📅 Test Date: {metadata.get('start_time', 'Unknown')[:19]}")
            print(".1f"
        print()

        # Overall performance score
        if "combined_analysis" in self.results:
            analysis = self.results["combined_analysis"]
            score = analysis.get("overall_performance_score", 0)
            self._print_score_gauge(score)
            print()

        # Key metrics table
        self._print_key_metrics_table()

        # Performance analysis
        self._print_performance_analysis()

        # Thresholds and limits
        self._print_thresholds_and_limits()

        # Recommendations
        self._print_recommendations()

    def _print_score_gauge(self, score: int):
        """Print ASCII art performance gauge"""
        print("📊 OVERALL PERFORMANCE SCORE")
        print(f"   Score: {score}/100")

        # Simple gauge visualization
        filled = int(score / 5)  # 20 bars total
        empty = 20 - filled
        gauge = "█" * filled + "░" * empty
        print(f"   [{gauge}]")

        # Performance level
        if score >= 90:
            level = "🏆 EXCEPTIONAL"
        elif score >= 80:
            level = "✅ EXCELLENT"
        elif score >= 70:
            level = "👍 GOOD"
        elif score >= 60:
            level = "⚠️  ACCEPTABLE"
        elif score >= 50:
            level = "🔶 NEEDS IMPROVEMENT"
        else:
            level = "❌ POOR"

        print(f"   Level: {level}")

    def _print_key_metrics_table(self):
        """Print key metrics in a formatted table"""
        print("📈 KEY PERFORMANCE METRICS")
        print("-" * 80)

        metrics = self.results.get("system_metrics", {})

        # Define metrics to display
        metric_display = [
            ("Query Response Time", "avg_query_response_times", "s", ".3f"),
            ("Memory Usage", "avg_memory_usage", "%", ".1f"),
            ("CPU Usage", "avg_cpu_usage", "%", ".1f"),
            ("Database Size", "final_db_size", "MB", ".1f"),
            ("API Response Time", "avg_api_response_times", "s", ".3f"),
        ]

        print("<30")
        print("-" * 80)

        for name, key, unit, fmt in metric_display:
            value = metrics.get(key, 0)
            if value > 0:
                print("<30")
            else:
                print("<30"
        print()

    def _print_performance_analysis(self):
        """Print performance analysis section"""
        print("🔍 PERFORMANCE ANALYSIS")
        print("-" * 80)

        analysis = None
        if "combined_analysis" in self.results:
            analysis = self.results["combined_analysis"].get("performance_comparison", {})
        elif "performance_analysis" in self.results:
            analysis = self.results["performance_analysis"]

        if analysis:
            print(f"Overall Performance:    {analysis.get('overall_performance', 'Unknown')}")
            print(f"System Health:         {analysis.get('system_health', 'Unknown')}")
            print(f"Scalability Rating:    {analysis.get('scalability_rating', 'Unknown')}")

            bottlenecks = analysis.get('bottlenecks_identified', [])
            if bottlenecks:
                print(f"Bottlenecks Identified: {', '.join(bottlenecks)}")
            else:
                print("Bottlenecks Identified: None")

        print()

    def _print_thresholds_and_limits(self):
        """Print system thresholds and limits"""
        print("🎯 SYSTEM THRESHOLDS & LIMITS")
        print("-" * 80)

        thresholds = {}
        if "combined_analysis" in self.results:
            thresholds = self.results["combined_analysis"].get("critical_thresholds", {})
        elif "thresholds_determined" in self.results:
            thresholds = self.results["thresholds_determined"]

        if thresholds:
            print(f"Max Concurrent Users:     {thresholds.get('max_concurrent_users', 'Unknown')}")
            print(f"Memory Threshold:         {thresholds.get('memory_threshold_gb', 'Unknown')} GB")
            print(f"CPU Threshold:           {thresholds.get('cpu_threshold_percent', 'Unknown')} %")
            print(f"Max Data Volume:         {thresholds.get('max_cve_records', 'Unknown')} CVE records")
        else:
            print("No threshold data available")

        print()

    def _print_recommendations(self):
        """Print system recommendations"""
        print("💡 SYSTEM RECOMMENDATIONS")
        print("-" * 80)

        recommendations = []
        if "combined_analysis" in self.results:
            recommendations = self.results["combined_analysis"].get("system_recommendations", [])
        elif "recommendations" in self.results:
            recommendations = self.results["recommendations"]

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print("2d")
        else:
            print("No specific recommendations available")

        print()

    def print_detailed_metrics(self):
        """Print detailed metrics for each test component"""
        print("📊 DETAILED TEST RESULTS")
        print("=" * 80)

        # CVE Stress Test Results
        self._print_test_section("real_cve_stress", "CVE Loading Stress Test")

        # MITRE Loading Results
        self._print_test_section("real_mitre_loading", "MITRE ATT&CK Loading")

        # RSS Collection Results
        self._print_test_section("real_rss_stress", "RSS Feed Collection Stress")

        # Query Performance Results
        self._print_test_section("real_query_performance", "Query Performance Under Load")

        # Data Growth Impact
        self._print_test_section("data_growth_impact", "Database Growth Impact")

        # API Endpoint Stress
        self._print_test_section("api_endpoints_stress", "API Endpoint Stress")

    def _print_test_section(self, section_key: str, title: str):
        """Print a specific test section"""
        section = self.results.get(section_key, {})
        if not section:
            return

        print(f"\n🔬 {title}")
        print("-" * 60)

        # Handle different result formats
        if isinstance(section, dict) and "error" not in section:
            for key, value in section.items():
                if isinstance(value, dict) and "error" not in value:
                    print(f"{key}:")
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, float):
                            print(".3f")
                        else:
                            print(f"  {sub_key}: {sub_value}")
                elif isinstance(value, (int, float)):
                    if isinstance(value, float):
                        print(".3f")
                    else:
                        print(f"{key}: {value}")
                else:
                    print(f"{key}: {value}")
        else:
            print("No data available")

    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report"""
        report = []
        report.append("# Cyber-PI Stress Test Performance Report")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Executive Summary
        report.append("## Executive Summary")
        if "combined_analysis" in self.results:
            analysis = self.results["combined_analysis"]
            score = analysis.get("overall_performance_score", 0)
            report.append(f"**Overall Performance Score:** {score}/100")

            if score >= 80:
                report.append("**Assessment:** System performing well under stress")
            elif score >= 60:
                report.append("**Assessment:** System acceptable but has room for improvement")
            else:
                report.append("**Assessment:** System needs optimization")

        report.append("")

        # Key Findings
        report.append("## Key Findings")
        metrics = self.results.get("system_metrics", {})

        if "avg_query_response_times" in metrics:
            avg_query = metrics["avg_query_response_times"]
            report.append(f"- **Average Query Time:** {avg_query:.3f} seconds")
            if avg_query < 0.5:
                report.append("  - Excellent query performance")
            elif avg_query < 2.0:
                report.append("  - Acceptable query performance")
            else:
                report.append("  - Query performance needs optimization")

        if "peak_memory_usage" in metrics:
            peak_mem = metrics["peak_memory_usage"]
            report.append(f"- **Peak Memory Usage:** {peak_mem:.1f}%")
            if peak_mem < 80:
                report.append("  - Memory usage within acceptable limits")
            else:
                report.append("  - High memory usage detected")

        if "peak_cpu_usage" in metrics:
            peak_cpu = metrics["peak_cpu_usage"]
            report.append(f"- **Peak CPU Usage:** {peak_cpu:.1f}%")
            if peak_cpu < 80:
                report.append("  - CPU usage within acceptable limits")
            else:
                report.append("  - High CPU usage detected")

        report.append("")

        # Recommendations
        report.append("## Recommendations")
        recommendations = []
        if "combined_analysis" in self.results:
            recommendations = self.results["combined_analysis"].get("system_recommendations", [])
        elif "recommendations" in self.results:
            recommendations = self.results["recommendations"]

        if recommendations:
            for rec in recommendations:
                report.append(f"- {rec}")
        else:
            report.append("No specific recommendations available")

        report.append("")

        # Raw Data
        report.append("## Raw Test Data")
        report.append("```json")
        report.append(json.dumps(self.results, indent=2, default=str))
        report.append("```")

        return "\n".join(report)

    def save_performance_report(self, filename: str = None):
        """Save performance report to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"performance_report_{timestamp}.md"

        report = self.generate_performance_report()

        with open(filename, 'w') as f:
            f.write(report)

        print(f"📄 Performance report saved to: {filename}")


def main():
    """Main dashboard function"""
    if len(sys.argv) != 2:
        print("Usage: python performance_dashboard.py <results_file.json>")
        sys.exit(1)

    results_file = sys.argv[1]
    dashboard = PerformanceDashboard(results_file)

    # Print executive summary
    dashboard.print_executive_summary()

    # Print detailed metrics
    dashboard.print_detailed_metrics()

    # Generate and save report
    dashboard.save_performance_report()


if __name__ == "__main__":
    main()
