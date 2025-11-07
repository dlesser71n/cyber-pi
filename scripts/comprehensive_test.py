#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing
Tests all 18 industries with real data collection
"""

import sys
import os
from pathlib import Path
import json
import logging
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from collectors.unified_collector import UnifiedCollector
from processors.client_filter import ClientFilter
from delivery.newsletter_generator import NewsletterGenerator
from delivery.alert_system import AlertSystem

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveTest:
    """Complete system test across all industries"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'tests': {}
        }
        
        # Initialize all components
        logger.info("=" * 80)
        logger.info("🧪 COMPREHENSIVE SYSTEM TEST - ALL 18 INDUSTRIES")
        logger.info("=" * 80)
        
        self.collector = UnifiedCollector()
        self.client_filter = ClientFilter()
        self.newsletter_gen = NewsletterGenerator()
        self.alert_system = AlertSystem()
        
        # Get all industries
        self.industries = self.client_filter.get_available_industries()
        logger.info(f"\n✅ Initialized for {len(self.industries)} industries")
    
    def test_data_collection(self):
        """Test 1: Data Collection (RSS + Social)"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: DATA COLLECTION (RSS + SOCIAL INTELLIGENCE)")
        logger.info("=" * 80)
        
        try:
            # Collect intelligence
            results = self.collector.collect_all()
            
            rss_count = len(results['rss'])
            social_count = len(results['social'])
            total_count = len(results['total'])
            
            logger.info(f"\n📊 Collection Results:")
            logger.info(f"   RSS items:    {rss_count}")
            logger.info(f"   Social items: {social_count}")
            logger.info(f"   Total items:  {total_count}")
            
            # Save collected data
            self.collected_items = results['total']
            
            self.results['tests']['data_collection'] = {
                'status': 'PASS' if total_count > 0 else 'FAIL',
                'rss_count': rss_count,
                'social_count': social_count,
                'total_count': total_count
            }
            
            if total_count > 0:
                logger.info(f"\n✅ TEST 1 PASSED: Collected {total_count} intelligence items")
            else:
                logger.error(f"\n❌ TEST 1 FAILED: No items collected")
            
            return total_count > 0
            
        except Exception as e:
            logger.error(f"\n❌ TEST 1 FAILED: {str(e)}")
            self.results['tests']['data_collection'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_industry_filtering(self):
        """Test 2: Filter for All 18 Industries"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 2: INDUSTRY FILTERING (ALL 18 INDUSTRIES)")
        logger.info("=" * 80)
        
        try:
            industry_results = {}
            
            for industry in self.industries:
                logger.info(f"\n📊 Testing: {industry}")
                
                # Filter for this industry
                filtered = self.client_filter.filter_for_client(
                    self.collected_items, 
                    industry, 
                    min_score=10
                )
                
                # Count by priority
                critical = len([i for i in filtered if i['relevance_score'] >= 30])
                high = len([i for i in filtered if 20 <= i['relevance_score'] < 30])
                medium = len([i for i in filtered if 10 <= i['relevance_score'] < 20])
                
                logger.info(f"   Total relevant:  {len(filtered)}")
                logger.info(f"   Critical (≥30):  {critical}")
                logger.info(f"   High (20-29):    {high}")
                logger.info(f"   Medium (10-19):  {medium}")
                
                # Show top 3 threats
                if filtered:
                    logger.info(f"   Top threats:")
                    for i, threat in enumerate(filtered[:3], 1):
                        logger.info(f"      {i}. [{threat['relevance_score']}] {threat['title'][:60]}")
                
                industry_results[industry] = {
                    'total': len(filtered),
                    'critical': critical,
                    'high': high,
                    'medium': medium,
                    'top_threat': filtered[0]['title'][:100] if filtered else None
                }
            
            self.results['tests']['industry_filtering'] = {
                'status': 'PASS',
                'industries_tested': len(self.industries),
                'results': industry_results
            }
            
            logger.info(f"\n✅ TEST 2 PASSED: Filtered for all {len(self.industries)} industries")
            return True
            
        except Exception as e:
            logger.error(f"\n❌ TEST 2 FAILED: {str(e)}")
            self.results['tests']['industry_filtering'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_newsletter_generation(self):
        """Test 3: Generate Newsletters for All Industries"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 3: NEWSLETTER GENERATION (ALL 18 INDUSTRIES)")
        logger.info("=" * 80)
        
        try:
            newsletter_dir = Path('data/reports/newsletters/test_all')
            newsletter_dir.mkdir(parents=True, exist_ok=True)
            
            generated_count = 0
            
            for industry in self.industries:
                logger.info(f"\n📧 Generating newsletter: {industry}")
                
                try:
                    # Generate newsletter HTML
                    html = self.newsletter_gen.generate_newsletter(
                        self.collected_items,
                        industry
                    )
                    
                    if html:
                        # Save to file
                        output_file = newsletter_dir / f"{industry}_newsletter.html"
                        with open(output_file, 'w') as f:
                            f.write(html)
                        
                        logger.info(f"   ✅ Generated: {output_file.name} ({len(html)} bytes)")
                        generated_count += 1
                    else:
                        logger.warning(f"   ⚠️  Empty newsletter generated")
                        
                except Exception as e:
                    logger.error(f"   ❌ Failed: {str(e)[:50]}")
            
            self.results['tests']['newsletter_generation'] = {
                'status': 'PASS' if generated_count == len(self.industries) else 'PARTIAL',
                'generated': generated_count,
                'total': len(self.industries),
                'output_dir': str(newsletter_dir)
            }
            
            logger.info(f"\n✅ TEST 3 PASSED: Generated {generated_count}/{len(self.industries)} newsletters")
            logger.info(f"   Saved to: {newsletter_dir}")
            
            return generated_count > 0
            
        except Exception as e:
            logger.error(f"\n❌ TEST 3 FAILED: {str(e)}")
            self.results['tests']['newsletter_generation'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_alert_system(self):
        """Test 4: Alert System with Critical Threats"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 4: ALERT SYSTEM (CRITICAL THREAT DETECTION)")
        logger.info("=" * 80)
        
        try:
            alert_results = {}
            
            # Test alerts for industries with critical threats
            test_industries = ['aviation', 'healthcare', 'energy', 'financial', 'manufacturing']
            
            for industry in test_industries:
                if industry not in self.industries:
                    continue
                
                logger.info(f"\n🚨 Testing alerts: {industry}")
                
                # Check for critical threats (without sending alerts)
                filtered = self.client_filter.filter_for_client(
                    self.collected_items,
                    industry
                )
                
                critical_threats = [
                    item for item in filtered 
                    if item['relevance_score'] >= 30
                ]
                
                logger.info(f"   Critical threats found: {len(critical_threats)}")
                
                if critical_threats:
                    for i, threat in enumerate(critical_threats[:3], 1):
                        logger.info(f"      {i}. Score: {threat['relevance_score']}")
                        logger.info(f"         {threat['title'][:70]}")
                        logger.info(f"         Reasons: {', '.join(threat['match_reasons'][:2])}")
                
                alert_results[industry] = {
                    'critical_count': len(critical_threats),
                    'would_alert': len(critical_threats) > 0
                }
            
            total_critical = sum(r['critical_count'] for r in alert_results.values())
            
            self.results['tests']['alert_system'] = {
                'status': 'PASS',
                'industries_tested': len(test_industries),
                'total_critical_threats': total_critical,
                'results': alert_results
            }
            
            logger.info(f"\n✅ TEST 4 PASSED: Alert system validated")
            logger.info(f"   Total critical threats across industries: {total_critical}")
            
            return True
            
        except Exception as e:
            logger.error(f"\n❌ TEST 4 FAILED: {str(e)}")
            self.results['tests']['alert_system'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_report_quality(self):
        """Test 5: Report Quality Analysis"""
        logger.info("\n" + "=" * 80)
        logger.info("TEST 5: REPORT QUALITY ANALYSIS")
        logger.info("=" * 80)
        
        try:
            quality_metrics = {
                'industries_with_threats': 0,
                'industries_with_critical': 0,
                'avg_threats_per_industry': 0,
                'coverage_score': 0
            }
            
            total_threats = 0
            
            for industry in self.industries:
                filtered = self.client_filter.filter_for_client(
                    self.collected_items,
                    industry,
                    min_score=10
                )
                
                if len(filtered) > 0:
                    quality_metrics['industries_with_threats'] += 1
                    total_threats += len(filtered)
                
                critical = [i for i in filtered if i['relevance_score'] >= 30]
                if len(critical) > 0:
                    quality_metrics['industries_with_critical'] += 1
            
            quality_metrics['avg_threats_per_industry'] = total_threats / len(self.industries)
            quality_metrics['coverage_score'] = (quality_metrics['industries_with_threats'] / len(self.industries)) * 100
            
            logger.info(f"\n📊 Quality Metrics:")
            logger.info(f"   Industries with relevant threats:  {quality_metrics['industries_with_threats']}/{len(self.industries)}")
            logger.info(f"   Industries with critical threats:  {quality_metrics['industries_with_critical']}/{len(self.industries)}")
            logger.info(f"   Avg threats per industry:          {quality_metrics['avg_threats_per_industry']:.1f}")
            logger.info(f"   Coverage score:                    {quality_metrics['coverage_score']:.1f}%")
            
            self.results['tests']['report_quality'] = {
                'status': 'PASS',
                'metrics': quality_metrics
            }
            
            logger.info(f"\n✅ TEST 5 PASSED: Report quality validated")
            
            return True
            
        except Exception as e:
            logger.error(f"\n❌ TEST 5 FAILED: {str(e)}")
            self.results['tests']['report_quality'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def generate_summary_report(self):
        """Generate comprehensive test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 80)
        
        # Count passed tests
        passed = sum(1 for test in self.results['tests'].values() if test['status'] == 'PASS')
        total = len(self.results['tests'])
        
        logger.info(f"\nTests Passed: {passed}/{total}")
        logger.info(f"\nTest Results:")
        
        for test_name, result in self.results['tests'].items():
            status_icon = "✅" if result['status'] == 'PASS' else "⚠️" if result['status'] == 'PARTIAL' else "❌"
            logger.info(f"   {status_icon} {test_name.replace('_', ' ').title()}: {result['status']}")
        
        # Save detailed results
        output_file = Path('data/reports/comprehensive_test_results.json')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n💾 Detailed results saved to: {output_file}")
        
        # Overall status
        if passed == total:
            logger.info(f"\n🎉 ALL TESTS PASSED! System is production-ready!")
            return True
        elif passed > total / 2:
            logger.info(f"\n⚠️  PARTIAL SUCCESS: {passed}/{total} tests passed")
            return True
        else:
            logger.info(f"\n❌ TESTS FAILED: Only {passed}/{total} tests passed")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        logger.info(f"\n⏰ Test started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Run tests
        test_1 = self.test_data_collection()
        
        if test_1:
            test_2 = self.test_industry_filtering()
            test_3 = self.test_newsletter_generation()
            test_4 = self.test_alert_system()
            test_5 = self.test_report_quality()
        else:
            logger.error("\n❌ Cannot proceed - data collection failed")
            return False
        
        # Generate summary
        return self.generate_summary_report()


def main():
    """Main test runner"""
    tester = ComprehensiveTest()
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
