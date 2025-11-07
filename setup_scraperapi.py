#!/usr/bin/env python3
"""
ScraperAPI Setup and Testing Script
Configure and test ScraperAPI for dark web intelligence collection
"""

import os
import sys
import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_scraperapi():
    """Setup ScraperAPI configuration"""
    print("🚀 ScraperAPI Setup for Dark Web Intelligence Collection")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('SCRAPERAPI_KEY')
    if not api_key:
        print("\n❌ ScraperAPI key not found!")
        print("Please set your ScraperAPI key:")
        print("export SCRAPERAPI_KEY='your_api_key_here'")
        print("\nOr get a free key at: https://www.scraperapi.com/")
        return False
    
    print(f"✅ ScraperAPI key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test basic ScraperAPI connection
    print("\n🔍 Testing ScraperAPI connection...")
    
    async def test_connection():
        try:
            # Test request to httpbin.org through ScraperAPI
            params = {
                'api_key': api_key,
                'url': 'https://httpbin.org/ip',
                'country_code': 'us',
                'premium': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.scraperapi.com', params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ ScraperAPI connection successful!")
                        print(f"📍 IP through ScraperAPI: {data.get('origin', 'Unknown')}")
                        return True
                    else:
                        print(f"❌ ScraperAPI connection failed: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            print(f"❌ ScraperAPI connection error: {e}")
            return False
    
    # Run test
    success = asyncio.run(test_connection())
    
    if success:
        print("\n🎯 Testing advanced features...")
        
        async def test_advanced_features():
            try:
                # Test JavaScript rendering
                params = {
                    'api_key': api_key,
                    'url': 'https://httpbin.org/headers',
                    'render': True,
                    'country_code': 'de',
                    'premium': True
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://api.scraperapi.com', params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"✅ JavaScript rendering successful!")
                            print(f"🌍 Request from Germany: {data.get('headers', {}).get('X-Forwarded-For', 'Unknown')}")
                            return True
                        else:
                            print(f"⚠️ JavaScript rendering test failed: HTTP {response.status}")
                            return False
                            
            except Exception as e:
                print(f"⚠️ Advanced features test error: {e}")
                return False
        
        asyncio.run(test_advanced_features())
        
        print("\n📊 Account information:")
        print("📈 Check your dashboard: https://dashboard.scraperapi.com")
        print("📚 Documentation: https://docs.scraperapi.com")
        print("💰 Pricing: https://www.scraperapi.com/pricing/")
        
        print("\n🎯 Recommended plans for dark web intelligence:")
        print("• Startup: $50/month - 100,000 requests")
        print("• Business: $150/month - 300,000 requests") 
        print("• Scale: $500/month - 1,000,000 requests")
        
        print("\n✅ ScraperAPI setup complete!")
        return True
    else:
        return False

def create_env_file():
    """Create .env file with ScraperAPI key"""
    env_file = ".env"
    
    if not os.path.exists(env_file):
        print(f"\n📝 Creating {env_file} file...")
        
        api_key = input("Enter your ScraperAPI key (or press Enter to skip): ").strip()
        
        if api_key:
            with open(env_file, 'w') as f:
                f.write(f"# ScraperAPI Configuration\n")
                f.write(f"SCRAPERAPI_KEY={api_key}\n")
                f.write(f"# Dark Web Intelligence Collection\n")
                f.write(f"SCRAPERAPI_RATE_LIMIT=10\n")
                f.write(f"SCRAPERAPI_PREMIUM=true\n")
            
            print(f"✅ {env_file} file created with your ScraperAPI key")
            print("🔐 Your API key is now configured for the dark web collector")
        else:
            print("⚠️ No API key provided. You can set it later with:")
            print("export SCRAPERAPI_KEY='your_api_key_here'")
    else:
        print(f"✅ {env_file} file already exists")

def test_dark_web_collector():
    """Test the ScraperAPI dark web collector"""
    print("\n🌑 Testing ScraperAPI Dark Web Intelligence Collector...")
    
    api_key = os.getenv('SCRAPERAPI_KEY')
    if not api_key:
        print("❌ ScraperAPI key required for testing")
        return False
    
    try:
        # Import and test the collector
        from src.collectors.scraperapi_dark_web_collector import ScraperAPIDarkWebCollector
        
        async def test_collector():
            async with ScraperAPIDarkWebCollector(api_key=api_key, max_workers=2) as collector:
                # Test with a few sources
                test_sources = {
                    'malware_traffic': {
                        'url': 'https://www.malware-traffic-analysis.net/',
                        'type': 'blog',
                        'priority': 'high',
                        'scraperapi_config': {
                            'country_code': 'us',
                            'render': False,
                            'premium': True
                        }
                    }
                }
                
                # Override sources for testing
                collector.dark_web_sources = test_sources
                
                print("🔍 Collecting test intelligence...")
                items = await collector.collect_all_dark_web_intelligence()
                
                print(f"✅ Test collection complete: {len(items)} items collected")
                
                if items:
                    print("\n📊 Sample intelligence:")
                    for i, item in enumerate(items[:3]):
                        print(f"\n{i+1}. {item.title[:50]}...")
                        print(f"   Source: {item.source}")
                        print(f"   Threat Type: {item.threat_type}")
                        print(f"   Urgency: {item.urgency_level}")
                        print(f"   IOCs: {len(item.iocs)}")
                        print(f"   Country: {item.proxy_country}")
                
                return len(items) > 0
        
        success = asyncio.run(test_collector())
        
        if success:
            print("\n🎯 ScraperAPI dark web collector is working perfectly!")
            print("🚀 Ready for full-scale intelligence collection")
        else:
            print("\n⚠️ Test completed but no items collected")
            print("🔍 This may be normal depending on source availability")
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing dark web collector: {e}")
        return False

def show_usage_examples():
    """Show usage examples for ScraperAPI dark web collector"""
    print("\n📚 ScraperAPI Dark Web Collector Usage Examples")
    print("=" * 60)
    
    print("\n1️⃣ Basic Collection:")
    print("export SCRAPERAPI_KEY='your_key'")
    print("python3 src/collectors/scraperapi_dark_web_collector.py")
    
    print("\n2️⃣ Custom Configuration:")
    print("python3 -c \"")
    print("import asyncio")
    print("from src.collectors.scraperapi_dark_web_collector import ScraperAPIDarkWebCollector")
    print("async def main():")
    print("    async with ScraperAPIDarkWebCollector('your_key') as collector:")
    print("        items = await collector.collect_all_dark_web_intelligence()")
    print("        print(f'Collected {len(items)} intelligence items')")
    print("asyncio.run(main())")
    print("\"")
    
    print("\n3️⃣ Integration with Existing Pipeline:")
    print("# Add to your unified collector")
    print("dark_web_items = await scraperapi_collector.collect_all_dark_web_intelligence()")
    print("all_intelligence.extend(dark_web_items)")
    
    print("\n4️⃣ Custom Source Configuration:")
    print("custom_sources = {")
    print("    'my_forum': {")
    print("        'url': 'https://example-forum.com/',")
    print("        'type': 'forum',")
    print("        'scraperapi_config': {")
    print("            'country_code': 'us',")
    print("            'render': True,")
    print("            'premium': True")
    print("        }")
    print("    }")
    print("}")
    
    print("\n5️⃣ Advanced Features:")
    print("# Enable JavaScript rendering")
    print("# Use ultra-premium proxies")
    print("# Rotate through multiple countries")
    print("# Extract comprehensive IOCs")
    print("# Generate credibility scores")

def show_best_practices():
    """Show ScraperAPI best practices for dark web intelligence"""
    print("\n🎯 ScraperAPI Best Practices for Dark Web Intelligence")
    print("=" * 60)
    
    print("\n🔧 Configuration Best Practices:")
    print("• Use premium proxies for better success rates")
    print("• Enable JavaScript rendering for modern sites")
    print("• Rotate countries to avoid geographic blocking")
    print("• Set appropriate rate limits to respect targets")
    print("• Use retry logic with different configurations")
    
    print("\n🌍 Geographic Targeting:")
    print("• US: General access, good for most sites")
    print("• DE: Excellent for European forums")
    print("• GB: Good for UK-based communities")
    print("• NL: More liberal content policies")
    print("• FR: Good for French-speaking sources")
    
    print("\n⚡ Performance Optimization:")
    print("• Limit concurrent requests to avoid overload")
    print("• Use connection pooling for efficiency")
    print("• Implement exponential backoff for retries")
    print("• Monitor credit usage to control costs")
    print("• Cache results when appropriate")
    
    print("\n🛡️ Security Considerations:")
    print("• Rotate user agents randomly")
    print("• Use realistic headers")
    print("• Implement delays between requests")
    print("• Monitor for anti-scraping measures")
    print("• Respect robots.txt when appropriate")
    
    print("\n💰 Cost Management:")
    print("• Monitor daily credit usage")
    print("• Prioritize high-value sources")
    print("• Use smart retry to avoid wasted credits")
    print("• Set usage alerts in dashboard")
    print("• Consider higher plans for scale")

def main():
    """Main setup function"""
    print("🌑 ScraperAPI Dark Web Intelligence Collection Setup")
    print("=" * 60)
    print("Professional-grade proxy rotation for underground threat intelligence")
    
    # Setup steps
    if not setup_scraperapi():
        print("\n❌ ScraperAPI setup failed. Please check your API key.")
        return
    
    create_env_file()
    
    # Test collector
    test_success = test_dark_web_collector()
    
    # Show additional information
    show_usage_examples()
    show_best_practices()
    
    print("\n🎉 Setup Complete!")
    print("=" * 60)
    
    if test_success:
        print("✅ ScraperAPI is configured and working")
        print("🚀 Ready for dark web intelligence collection")
        print("📊 Monitor usage at: https://dashboard.scraperapi.com")
    else:
        print("⚠️ Basic setup complete, but collector test failed")
        print("🔍 Check source availability and network connectivity")
    
    print("\n📖 Next Steps:")
    print("1. Run full collection: python3 src/collectors/scraperapi_dark_web_collector.py")
    print("2. Monitor results in data/raw/ directory")
    print("3. Integrate with your existing pipeline")
    print("4. Customize sources for your specific needs")
    print("5. Set up automated collection scheduling")

if __name__ == "__main__":
    main()
