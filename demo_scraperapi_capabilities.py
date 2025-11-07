#!/usr/bin/env python3
"""
ScraperAPI Capabilities Demonstration
Shows all features and integration patterns for dark web intelligence
"""

import asyncio
import aiohttp
import json
import logging
import time
import hashlib
import random
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ScraperAPICapability:
    """Demonstration of ScraperAPI capabilities"""
    name: str
    description: str
    example_code: str
    use_case: str
    benefits: List[str]

class ScraperAPIMaster:
    """
    Master class demonstrating complete ScraperAPI capabilities
    for dark web intelligence collection
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "demo_key_placeholder"
        self.base_url = "https://api.scraperapi.com"
        self.capabilities = self._define_capabilities()
        
    def _define_capabilities(self) -> List[ScraperAPICapability]:
        """Define all ScraperAPI capabilities"""
        return [
            ScraperAPICapability(
                name="Proxy Rotation",
                description="Automatic rotation through millions of IPs worldwide",
                example_code="""
params = {
    'api_key': 'YOUR_KEY',
    'url': 'https://target-site.com',
    'country_code': 'us',  # Geographic targeting
    'premium': True        # High-quality proxies
}
response = await session.get('https://api.scraperapi.com', params=params)
                """,
                use_case="Circumvent IP blocks and access geo-restricted content",
                benefits=["99.9% uptime", "Automatic failover", "Geographic diversity"]
            ),
            
            ScraperAPICapability(
                name="JavaScript Rendering",
                description="Headless browser rendering for dynamic content",
                example_code="""
params = {
    'api_key': 'YOUR_KEY',
    'url': 'https://javascript-site.com',
    'render': True,                    # Enable JS rendering
    'wait_for_selector': '.content',   # Wait for specific element
    'device_type': 'desktop'           # Device emulation
}
                """,
                use_case="Access modern web applications and SPAs",
                benefits=["Dynamic content", "AJAX support", "Modern site compatibility"]
            ),
            
            ScraperAPICapability(
                name="Geographic Targeting",
                description="Route requests through 195+ countries",
                example_code="""
countries = ['us', 'de', 'gb', 'nl', 'fr', 'ca', 'ch']
for country in countries:
    params = {
        'api_key': 'YOUR_KEY',
        'url': 'https://target.com',
        'country_code': country
    }
    content = await scraperapi.get(params)
                """,
                use_case="Access region-specific content and bypass geo-blocking",
                benefits=["195+ countries", "Residential IPs", "Local content access"]
            ),
            
            ScraperAPICapability(
                name="CAPTCHA Solving",
                description="Automatic CAPTCHA detection and solving",
                example_code="""
# ScraperAPI handles CAPTCHAs automatically
# No additional configuration needed
params = {
    'api_key': 'YOUR_KEY',
    'url': 'https://protected-site.com',
    'premium': True  # Recommended for CAPTCHA-heavy sites
}
                """,
                use_case="Access protected sites without manual intervention",
                benefits=["Automatic solving", "Multiple CAPTCHA types", "No manual work"]
            ),
            
            ScraperAPICapability(
                name="Session Management",
                description="Maintain same IP across multiple requests",
                example_code="""
params = {
    'api_key': 'YOUR_KEY',
    'url': 'https://target.com',
    'session_number': 123,    # Session ID
    'session_duration': 300   # Seconds
}
# Same IP will be used for all requests with session_number 123
                """,
                use_case="Maintain login sessions and shopping carts",
                benefits=["Persistent IP", "Login support", "Form completion"]
            ),
            
            ScraperAPICapability(
                name="Device Emulation",
                description="Emulate different devices and browsers",
                example_code="""
params = {
    'api_key': 'YOUR_KEY',
    'url': 'https://target.com',
    'device_type': 'mobile',     # desktop | mobile
    'country_code': 'us',
    'render': True
}
                """,
                use_case="Access mobile-specific content and layouts",
                benefits=["Mobile/desktop", "Different viewports", "User-agent rotation"]
            )
        ]
    
    def demonstrate_capabilities(self):
        """Demonstrate all ScraperAPI capabilities"""
        print("🚀 ScraperAPI Capabilities Demonstration")
        print("=" * 80)
        print("Professional-grade web scraping for dark web intelligence")
        print()
        
        for i, capability in enumerate(self.capabilities, 1):
            print(f"{i}. 🎯 {capability.name}")
            print(f"   📖 {capability.description}")
            print(f"   💡 Use Case: {capability.use_case}")
            print(f"   ✅ Benefits:")
            for benefit in capability.benefits:
                print(f"      • {benefit}")
            print(f"   💻 Example Code:")
            for line in capability.example_code.strip().split('\n'):
                print(f"      {line}")
            print()
    
    def demonstrate_dark_web_integration(self):
        """Demonstrate dark web intelligence collection patterns"""
        print("🌑 Dark Web Intelligence Integration Patterns")
        print("=" * 80)
        
        integration_patterns = {
            "Forum Intelligence": {
                "sources": ["hackernews.io", "nulled.to", "cracked.io"],
                "config": {
                    "country_code": "de",
                    "render": True,
                    "premium": True,
                    "wait_for_selector": ".topic_title"
                },
                "extraction": ["Thread titles", "Post content", "User mentions", "IOCs"]
            },
            
            "Marketplace Monitoring": {
                "sources": ["empire-market.org", "white-house.market"],
                "config": {
                    "country_code": "nl",
                    "render": True,
                    "ultra_premium": True,
                    "device_type": "desktop"
                },
                "extraction": ["Product listings", "Prices", "Vendor info", "Crypto addresses"]
            },
            
            "Paste Site Analysis": {
                "sources": ["pastebin.com", "justpaste.it", "paste.ee"],
                "config": {
                    "country_code": "us",
                    "render": False,
                    "premium": True,
                    "keep_headers": True
                },
                "extraction": ["Paste titles", "Leaked data", "Credentials", "Database dumps"]
            },
            
            "Reddit Communities": {
                "sources": ["reddit.com/r/netsec", "reddit.com/r/darknet"],
                "config": {
                    "country_code": "us",
                    "render": True,
                    "premium": True,
                    "wait_for_selector": "._3xX726aBn29LDbsDtzr_6E"
                },
                "extraction": ["Post titles", "Discussions", "Threat actor mentions", "TTPs"]
            }
        }
        
        for pattern_name, pattern_config in integration_patterns.items():
            print(f"\n📊 {pattern_name}")
            print(f"   🌐 Sources: {', '.join(pattern_config['sources'])}")
            print(f"   ⚙️  Configuration:")
            for key, value in pattern_config['config'].items():
                print(f"      • {key}: {value}")
            print(f"   🔍 Extraction: {', '.join(pattern_config['extraction'])}")
    
    def demonstrate_advanced_features(self):
        """Demonstrate advanced ScraperAPI features"""
        print("\n🔧 Advanced ScraperAPI Features")
        print("=" * 80)
        
        advanced_features = {
            "Smart Retry Logic": {
                "description": "Intelligent retry with different configurations",
                "implementation": """
# Retry with different countries and settings
retry_configs = [
    {'country_code': 'us', 'render': False, 'premium': True},
    {'country_code': 'de', 'render': False, 'premium': True},
    {'country_code': 'gb', 'render': True, 'premium': True},
    {'country_code': 'us', 'render': True, 'ultra_premium': True}
]

for config in retry_configs:
    content = await scraperapi.get(url, **config)
    if content:
        break
                """
            },
            
            "Rate Limiting": {
                "description": "Intelligent throttling to avoid detection",
                "implementation": """
class RateLimitedScraper:
    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        self.last_request_time = 0
    
    async def make_request(self, url: str):
        # Implement rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.requests_per_second
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        return await self.scraperapi.get(url)
                """
            },
            
            "Credit Optimization": {
                "description": "Minimize credit usage while maximizing success",
                "implementation": """
# Prioritize sources and optimize configurations
high_value_sources = ['hackernews', 'nulled', 'cracked']
for source in high_value_sources:
    # Use premium for high-value sources
    config = {'premium': True, 'render': False}
    
# Use standard config for lower-priority sources
standard_sources = ['reddit_netsec', 'packet_storm']
for source in standard_sources:
    config = {'premium': False, 'render': False}
                """
            },
            
            "Geographic Rotation": {
                "description": "Rotate through countries for optimal access",
                "implementation": """
# Smart country selection based on source type
def get_optimal_country(source_type: str) -> str:
    if source_type == 'forum':
        return random.choice(['de', 'gb', 'nl'])
    elif source_type == 'marketplace':
        return random.choice(['nl', 'se', 'ch'])
    else:
        return random.choice(['us', 'de', 'gb'])

countries_used = set()
for source in sources:
    country = get_optimal_country(source.type)
    countries_used.add(country)
    content = await scraperapi.get(source.url, country_code=country)
                """
            }
        }
        
        for feature_name, feature_config in advanced_features.items():
            print(f"\n🎯 {feature_name}")
            print(f"   📖 {feature_config['description']}")
            print(f"   💻 Implementation:")
            for line in feature_config['implementation'].strip().split('\n'):
                print(f"      {line}")
    
    def demonstrate_performance_optimization(self):
        """Demonstrate performance optimization techniques"""
        print("\n⚡ Performance Optimization Techniques")
        print("=" * 80)
        
        optimizations = {
            "Connection Pooling": {
                "benefit": "Reduce connection overhead",
                "implementation": "connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)"
            },
            
            "Concurrent Processing": {
                "benefit": "Process multiple sources simultaneously",
                "implementation": "tasks = [collect_source(source) for source in sources]; await asyncio.gather(*tasks)"
            },
            
            "Intelligent Caching": {
                "benefit": "Avoid duplicate requests",
                "implementation": "cache_key = hashlib.md5(f'{url}{config}'.encode()).hexdigest()"
            },
            
            "Batch Processing": {
                "benefit": "Process items in batches for efficiency",
                "implementation": "for batch in chunk_items(items, batch_size=10): process_batch(batch)"
            },
            
            "Memory Management": {
                "benefit": "Handle large datasets efficiently",
                "implementation": "process_item(item); del item; gc.collect()"
            }
        }
        
        for opt_name, opt_config in optimizations.items():
            print(f"\n🚀 {opt_name}")
            print(f"   💡 Benefit: {opt_config['benefit']}")
            print(f"   💻 Code: {opt_config['implementation']}")
    
    def demonstrate_monitoring_analytics(self):
        """Demonstrate monitoring and analytics capabilities"""
        print("\n📊 Monitoring & Analytics Dashboard")
        print("=" * 80)
        
        metrics = {
            "Collection Metrics": {
                "total_requests": "Total API requests made",
                "successful_requests": "Successful data retrievals",
                "success_rate": "Percentage of successful requests",
                "average_response_time": "Mean response time in seconds",
                "credits_used": "Total credits consumed"
            },
            
            "Geographic Analytics": {
                "countries_used": "List of countries for proxy routing",
                "most_used_country": "Country with highest usage",
                "regional_success_rates": "Success rates by country",
                "optimal_countries": "Best performing countries"
            },
            
            "Content Analytics": {
                "items_collected": "Total intelligence items gathered",
                "threat_types_detected": "Types of threats identified",
                "iocs_extracted": "Total indicators of compromise",
                "credibility_scores": "Average credibility of collected data",
                "high_urgency_items": "Items requiring immediate attention"
            },
            
            "Performance Analytics": {
                "requests_per_second": "Collection throughput",
                "credits_per_item": "Efficiency metric",
                "error_rates": "Types and frequency of errors",
                "retry_success_rate": "Success after retry attempts"
            }
        }
        
        for category, category_metrics in metrics.items():
            print(f"\n📈 {category}")
            for metric_name, metric_desc in category_metrics.items():
                print(f"   • {metric_name}: {metric_desc}")
    
    def demonstrate_cost_management(self):
        """Demonstrate cost management strategies"""
        print("\n💰 Cost Management Strategies")
        print("=" * 80)
        
        strategies = {
            "Source Prioritization": {
                "strategy": "Focus on high-value sources",
                "implementation": "Prioritize forums and marketplaces over general sites",
                "savings": "30-50% credit reduction"
            },
            
            "Smart Configuration": {
                "strategy": "Optimize ScraperAPI settings",
                "implementation": "Disable JS rendering when not needed, use premium vs ultra-premium strategically",
                "savings": "20-40% credit reduction"
            },
            
            "Intelligent Caching": {
                "strategy": "Cache results to avoid duplicate requests",
                "implementation": "5-minute TTL for dynamic content, 1-hour for static content",
                "savings": "15-25% credit reduction"
            },
            
            "Rate Limiting": {
                "strategy": "Optimize request frequency",
                "implementation": "10 requests/second for forums, 5 requests/second for marketplaces",
                "savings": "10-20% credit reduction"
            },
            
            "Failure Analysis": {
                "strategy": "Identify and remove failing sources",
                "implementation": "Monitor success rates, disable consistently failing sources",
                "savings": "5-15% credit reduction"
            }
        }
        
        for strategy_name, strategy_config in strategies.items():
            print(f"\n🎯 {strategy_name}")
            print(f"   📋 Strategy: {strategy_config['strategy']}")
            print(f"   💻 Implementation: {strategy_config['implementation']}")
            print(f"   💵 Savings: {strategy_config['savings']}")
    
    def generate_integration_examples(self):
        """Generate practical integration examples"""
        print("\n🔗 Integration Examples")
        print("=" * 80)
        
        examples = {
            "Basic Integration": """
# Simple integration with existing pipeline
from src.collectors.scraperapi_dark_web_collector import ScraperAPIDarkWebCollector

async def collect_dark_web_intelligence():
    async with ScraperAPIDarkWebCollector(API_KEY) as collector:
        items = await collector.collect_all_dark_web_intelligence()
        return items

# Use in your main collector
dark_web_items = await collect_dark_web_intelligence()
all_intelligence.extend(dark_web_items)
            """,
            
            "Custom Source Integration": """
# Add your own sources
custom_sources = {
    'my_target_forum': {
        'url': 'https://target-forum.com/',
        'type': 'forum',
        'scraperapi_config': {
            'country_code': 'de',
            'render': True,
            'premium': True
        }
    }
}

collector.dark_web_sources.update(custom_sources)
            """,
            
            "Real-time Monitoring": """
# Continuous monitoring with alerts
async def monitor_threats():
    while True:
        items = await collector.collect_all_dark_web_intelligence()
        high_urgency = [i for i in items if i.urgency_level == 'high']
        
        if high_urgency:
            await send_security_alert(high_urgency)
        
        await asyncio.sleep(300)  # Check every 5 minutes
            """,
            
            "Scheduled Collection": """
# Schedule regular collection
import schedule

def scheduled_collection():
    asyncio.run(collector.collect_all_dark_web_intelligence())

# Schedule every hour
schedule.every().hour.do(scheduled_collection)

while True:
    schedule.run_pending()
    time.sleep(60)
            """
        }
        
        for example_name, example_code in examples.items():
            print(f"\n📝 {example_name}")
            print(f"   💻 Code:")
            for line in example_code.strip().split('\n'):
                print(f"      {line}")
    
    def show_best_practices(self):
        """Show comprehensive best practices"""
        print("\n🎯 Comprehensive Best Practices")
        print("=" * 80)
        
        best_practices = {
            "Configuration": [
                "Use premium proxies for better success rates",
                "Enable JavaScript rendering only when needed",
                "Rotate countries to avoid geographic blocking",
                "Set appropriate rate limits (10 req/sec recommended)",
                "Use ultra-premium for difficult targets only"
            ],
            
            "Performance": [
                "Implement connection pooling for efficiency",
                "Use concurrent processing for multiple sources",
                "Cache results to avoid duplicate requests",
                "Monitor memory usage with large datasets",
                "Implement exponential backoff for retries"
            ],
            
            "Security": [
                "Rotate user agents randomly",
                "Use realistic headers and cookies",
                "Implement delays between requests",
                "Monitor for anti-scraping measures",
                "Respect robots.txt when appropriate"
            ],
            
            "Cost Management": [
                "Monitor daily credit usage closely",
                "Prioritize high-value sources",
                "Use smart retry to avoid wasted credits",
                "Set usage alerts in dashboard",
                "Optimize configurations based on success rates"
            ],
            
            "Data Quality": [
                "Implement content validation",
                "Assess credibility of sources",
                "Extract comprehensive IOCs",
                "Generate meaningful metadata",
                "Filter out noise and false positives"
            ]
        }
        
        for category, practices in best_practices.items():
            print(f"\n📋 {category}")
            for practice in practices:
                print(f"   ✅ {practice}")
    
    def generate_success_metrics(self):
        """Generate success metrics and KPIs"""
        print("\n📈 Success Metrics & KPIs")
        print("=" * 80)
        
        metrics = {
            "Operational Metrics": {
                "Collection Success Rate": "> 85%",
                "Credit Efficiency": "< 1 credit per successful item",
                "Average Response Time": "< 5 seconds",
                "Geographic Diversity": "5+ countries used",
                "Source Coverage": "> 80% of configured sources"
            },
            
            "Intelligence Metrics": {
                "Threat Type Coverage": "10+ threat types detected",
                "IOC Extraction Rate": "> 2 IOCs per item",
                "Credibility Score": "> 0.7 average confidence",
                "False Positive Rate": "< 5%",
                "Data Freshness": "< 1 hour from publication"
            },
            
            "Performance Metrics": {
                "Throughput": "> 50 items per minute",
                "Concurrent Processing": "20+ simultaneous sources",
                "Memory Efficiency": "< 1GB for 10,000 items",
                "Storage Optimization": "> 90% compression ratio",
                "Processing Latency": "< 30 seconds end-to-end"
            },
            
            "Cost Metrics": {
                "Daily Budget Utilization": "< 90% of allocated credits",
                "Cost per Intelligence Item": "< $0.01",
                "ROI on Premium Features": "> 200% improvement",
                "Waste Reduction": "< 10% failed requests",
                "Scaling Efficiency": "Linear cost scaling"
            }
        }
        
        for category, category_metrics in metrics.items():
            print(f"\n🎯 {category}")
            for metric_name, target_value in category_metrics.items():
                print(f"   📊 {metric_name}: {target_value}")

def main():
    """Main demonstration function"""
    print("🚀 ScraperAPI Mastery Demonstration")
    print("=" * 80)
    print("Complete guide to professional dark web intelligence collection")
    print("Powered by ScraperAPI - Enterprise-grade web scraping infrastructure")
    print()
    
    # Initialize master class
    master = ScraperAPIMaster()
    
    # Run all demonstrations
    master.demonstrate_capabilities()
    master.demonstrate_dark_web_integration()
    master.demonstrate_advanced_features()
    master.demonstrate_performance_optimization()
    master.demonstrate_monitoring_analytics()
    master.demonstrate_cost_management()
    master.generate_integration_examples()
    master.show_best_practices()
    master.generate_success_metrics()
    
    print("\n🎉 ScraperAPI Mastery Demonstration Complete!")
    print("=" * 80)
    print("✅ You now have comprehensive knowledge of ScraperAPI capabilities")
    print("🚀 Ready to implement professional dark web intelligence collection")
    print("📊 Equipped with optimization strategies and best practices")
    print("💰 Prepared for cost-effective and scalable deployment")
    
    print("\n📖 Next Steps:")
    print("1. Get your ScraperAPI key: https://www.scraperapi.com/")
    print("2. Set up environment: export SCRAPERAPI_KEY='your_key'")
    print("3. Test the collector: python3 setup_scraperapi.py")
    print("4. Run full collection: python3 src/collectors/scraperapi_dark_web_collector.py")
    print("5. Monitor usage: https://dashboard.scraperapi.com")
    
    print("\n🎯 Recommended Plans:")
    print("• Startup: $50/month - 100,000 requests (Beginners)")
    print("• Business: $150/month - 300,000 requests (Professional)")
    print("• Scale: $500/month - 1,000,000 requests (Enterprise)")
    
    print("\n🌑 Dark Web Intelligence Sources Covered:")
    print("• Hacker Forums: hackernews.io, nulled.to, cracked.io")
    print("• Reddit Communities: r/netsec, r/hacking, r/darknet")
    print("• Paste Sites: pastebin.com, justpaste.it")
    print("• Threat Blogs: malware-traffic-analysis.net")
    print("• Exploit Repos: GitHub, Exploit-DB, Packet Storm")
    print("• Marketplaces: Empire Market, White House")
    
    print("\n✨ Status: SCRAPERAPI MASTER ACHIEVED! 🚀")

if __name__ == "__main__":
    main()
