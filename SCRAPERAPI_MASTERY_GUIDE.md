# 🚀 ScraperAPI Mastery Guide for Dark Web Intelligence

## 📖 **Table of Contents**
1. [ScraperAPI Overview](#scraperapi-overview)
2. [Core Features](#core-features)
3. [Dark Web Integration](#dark-web-integration)
4. [Advanced Configuration](#advanced-configuration)
5. [Best Practices](#best-practices)
6. [Cost Optimization](#cost-optimization)
7. [Troubleshooting](#troubleshooting)

---

## 🌐 **ScraperAPI Overview**

ScraperAPI is a professional web scraping service that handles:
- **Automatic proxy rotation** (millions of IPs)
- **CAPTCHA solving** (automated)
- **JavaScript rendering** (headless browsers)
- **Geographic targeting** (195+ countries)
- **Anti-bot bypass** (machine learning)
- **Rate limiting** (intelligent throttling)

### **Why ScraperAPI for Dark Web Intelligence?**

✅ **Reliability**: 99.9% uptime guarantee  
✅ **Scalability**: Millions of requests per month  
✅ **Stealth**: Residential, datacenter, and mobile proxies  
✅ **Compliance**: GDPR and CCPA compliant  
✅ **Support**: 24/7 technical support  
✅ **Integration**: Simple REST API integration  

---

## ⚡ **Core Features**

### **1. Proxy Rotation**
```python
# Automatic proxy rotation
params = {
    'api_key': 'YOUR_KEY',
    'url': 'https://target-site.com',
    'country_code': 'us',  # Geographic targeting
    'premium': True        # High-quality proxies
}
```

### **2. JavaScript Rendering**
```python
# Enable JavaScript for dynamic content
params = {
    'api_key': 'YOUR_KEY',
    'url': 'https://javascript-site.com',
    'render': True,                    # Enable JS rendering
    'wait_for_selector': '.content',   # Wait for specific element
    'device_type': 'desktop'           # Device emulation
}
```

### **3. Geographic Targeting**
```python
# Route requests through specific countries
countries = ['us', 'de', 'gb', 'nl', 'fr', 'ca', 'ch']
for country in countries:
    params = {
        'api_key': 'YOUR_KEY',
        'url': 'https://target.com',
        'country_code': country
    }
```

### **4. Session Management**
```python
# Maintain same IP across requests
params = {
    'api_key': 'YOUR_KEY',
    'url': 'https://target.com',
    'session_number': 123,  # Session ID
    'session_duration': 300  # Seconds
}
```

---

## 🌑 **Dark Web Integration**

### **Enhanced Dark Web Collector Architecture**

```python
class ScraperAPIDarkWebCollector:
    """
    Professional dark web intelligence collector
    Powered by ScraperAPI with advanced proxy rotation
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = ScraperAPIClient(api_key)
        
        # Optimized source configurations
        self.sources = {
            'hackernews': {
                'url': 'https://hackernews.io/',
                'scraperapi': {
                    'country_code': 'us',
                    'render': False,
                    'premium': True
                }
            },
            'nulled_to': {
                'url': 'https://nulled.to/',
                'scraperapi': {
                    'country_code': 'de',
                    'render': True,
                    'premium': True,
                    'wait_for_selector': '.topic_title'
                }
            }
        }
```

### **Smart Retry Strategy**
```python
async def get_with_smart_retry(self, url: str, max_retries: int = 5):
    """Intelligent retry with different configurations"""
    
    retry_configs = [
        # Try different countries
        {'country_code': 'us', 'render': False, 'premium': True},
        {'country_code': 'de', 'render': False, 'premium': True},
        {'country_code': 'gb', 'render': False, 'premium': True},
        
        # Try with JavaScript rendering
        {'country_code': 'us', 'render': True, 'premium': True},
        
        # Try ultra-premium for difficult targets
        {'country_code': 'us', 'render': True, 'ultra_premium': True}
    ]
    
    for attempt, config in enumerate(retry_configs[:max_retries]):
        try:
            content = await self.client.get(url, **config)
            if content:
                return content
        except Exception as e:
            logger.warning(f"Retry {attempt + 1} failed: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    return None
```

---

## 🔧 **Advanced Configuration**

### **1. Premium Proxy Configuration**
```python
# Premium proxy settings
scraperapi_config = {
    'api_key': 'YOUR_KEY',
    'premium': True,          # Use premium proxies
    'ultra_premium': False,   # For difficult targets
    'residential': False,     # Residential proxies (add-on)
    'mobile': False          # Mobile proxies (add-on)
}
```

### **2. JavaScript Rendering Optimization**
```python
# Advanced rendering settings
render_config = {
    'render': True,
    'wait_for_selector': '.main-content',
    'wait_time': 5000,           # milliseconds
    'device_type': 'desktop',
    'viewport_width': 1920,
    'viewport_height': 1080
}
```

### **3. Rate Limiting & Throttling**
```python
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
        
        # Make request through ScraperAPI
        return await self.scraperapi.get(url)
```

### **4. Geographic Proxy Rotation**
```python
# Smart country rotation
country_rotation = {
    'primary': ['us', 'de', 'gb'],     # Main countries
    'backup': ['nl', 'fr', 'ca'],      # Backup countries
    'special': ['ch', 'se', 'no']      # Special cases
}

def get_optimal_country(source_type: str) -> str:
    """Select best country based on source type"""
    if source_type == 'forum':
        return random.choice(['de', 'gb', 'nl'])
    elif source_type == 'marketplace':
        return random.choice(['nl', 'se', 'ch'])
    else:
        return random.choice(['us', 'de', 'gb'])
```

---

## 🎯 **Best Practices**

### **1. Request Optimization**
```python
# Optimize requests for dark web sources
def optimize_for_dark_web(url: str, source_type: str) -> dict:
    """Optimize ScraperAPI config for dark web sources"""
    
    base_config = {
        'api_key': 'YOUR_KEY',
        'url': url,
        'premium': True,
        'timeout': 30
    }
    
    if source_type == 'forum':
        base_config.update({
            'country_code': 'de',
            'render': True,
            'device_type': 'desktop'
        })
    elif source_type == 'paste':
        base_config.update({
            'country_code': 'us',
            'render': False,
            'keep_headers': True
        })
    elif source_type == 'marketplace':
        base_config.update({
            'country_code': 'nl',
            'render': True,
            'ultra_premium': True
        })
    
    return base_config
```

### **2. Error Handling & Resilience**
```python
async def resilient_request(self, url: str, config: dict) -> Optional[str]:
    """Make resilient requests with comprehensive error handling"""
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = await self.session.get(
                'https://api.scraperapi.com',
                params=config,
                timeout=aiohttp.ClientTimeout(total=60)
            )
            
            if response.status == 200:
                return await response.text()
            elif response.status == 429:
                # Rate limited - longer delay
                await asyncio.sleep(retry_delay * 2)
            elif response.status in [500, 502, 503, 504]:
                # Server error - retry
                await asyncio.sleep(retry_delay)
            else:
                logger.warning(f"HTTP {response.status}: {url}")
                
        except asyncio.TimeoutError:
            logger.warning(f"Timeout for {url}")
            await asyncio.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Request error: {e}")
            await asyncio.sleep(retry_delay)
        
        # Exponential backoff
        retry_delay *= 2
    
    return None
```

### **3. Content Quality Assessment**
```python
def assess_content_quality(content: str, url: str) -> float:
    """Assess quality of scraped content"""
    
    quality_score = 0.0
    
    # Length check
    if len(content) > 1000:
        quality_score += 0.3
    elif len(content) > 500:
        quality_score += 0.2
    
    # Content indicators
    if any(indicator in content.lower() for indicator in 
           ['ransomware', 'exploit', 'breach', 'leak']):
        quality_score += 0.3
    
    # Structure check
    if '<html' in content.lower() and '</html>' in content.lower():
        quality_score += 0.2
    
    # No error pages
    if not any(error in content.lower() for error in 
               ['404 not found', 'access denied', 'blocked']):
        quality_score += 0.2
    
    return min(quality_score, 1.0)
```

---

## 💰 **Cost Optimization**

### **1. Credit Management**
```python
class CreditManager:
    def __init__(self, daily_limit: int = 10000):
        self.daily_limit = daily_limit
        self.credits_used = 0
        self.start_time = time.time()
    
    def can_make_request(self) -> bool:
        """Check if we can make another request"""
        return self.credits_used < self.daily_limit
    
    def track_request(self, success: bool):
        """Track credit usage"""
        if success:
            self.credits_used += 1
    
    def get_usage_stats(self) -> dict:
        """Get current usage statistics"""
        return {
            'credits_used': self.credits_used,
            'credits_remaining': self.daily_limit - self.credits_used,
            'usage_percentage': (self.credits_used / self.daily_limit) * 100
        }
```

### **2. Smart Source Prioritization**
```python
# Prioritize high-value sources
source_priorities = {
    'high': ['hackernews', 'nulled', 'cracked', 'reddit_darknet'],
    'medium': ['exploit_in', 'pastebin', 'malware_traffic'],
    'low': ['reddit_netsec', 'packet_storm', 'justpaste']
}

def get_priority_sources(max_sources: int = 10) -> list:
    """Get prioritized list of sources"""
    sources = []
    
    # Add high priority first
    sources.extend(source_priorities['high'])
    
    # Add medium priority if space allows
    if len(sources) < max_sources:
        sources.extend(source_priorities['medium'][:max_sources - len(sources)])
    
    # Add low priority if space allows
    if len(sources) < max_sources:
        sources.extend(source_priorities['low'][:max_sources - len(sources)])
    
    return sources[:max_sources]
```

### **3. Efficient Caching**
```python
class IntelligentCache:
    def __init__(self, ttl: int = 300):  # 5 minutes TTL
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[str]:
        """Get cached content if valid"""
        if key in self.cache:
            content, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return content
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, content: str):
        """Cache content with timestamp"""
        self.cache[key] = (content, time.time())
    
    def generate_key(self, url: str, config: dict) -> str:
        """Generate cache key from URL and config"""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(f"{url}{config_str}".encode()).hexdigest()
```

---

## 🔍 **Troubleshooting**

### **Common Issues & Solutions**

#### **1. High Failure Rates**
```python
# Symptom: Many requests failing
# Solution: Implement smart retry with different configs

def diagnose_failure_rate(response_codes: dict) -> str:
    """Diagnose issues based on response codes"""
    
    total_requests = sum(response_codes.values())
    failure_rate = (response_codes.get('4xx', 0) + response_codes.get('5xx', 0)) / total_requests
    
    if failure_rate > 0.5:
        if response_codes.get('403', 0) > response_codes.get('404', 0):
            return "Access denied - try different countries or ultra-premium proxies"
        elif response_codes.get('429', 0) > 0:
            return "Rate limited - reduce request frequency"
        else:
            return "General failures - check source availability and configuration"
    
    return "Success rate acceptable"
```

#### **2. Credit Consumption**
```python
# Symptom: Using too many credits
# Solution: Optimize request patterns

def optimize_credit_usage(current_usage: dict) -> dict:
    """Optimize based on current usage patterns"""
    
    recommendations = []
    
    if current_usage['render_requests'] > current_usage['total_requests'] * 0.5:
        recommendations.append("Disable JavaScript rendering for sources that don't need it")
    
    if current_usage['ultra_premium_requests'] > current_usage['total_requests'] * 0.3:
        recommendations.append("Reserve ultra-premium for most difficult targets")
    
    if current_usage['success_rate'] < 0.7:
        recommendations.append("Improve source targeting and retry logic")
    
    return {
        'recommendations': recommendations,
        'potential_savings': calculate_potential_savings(current_usage)
    }
```

#### **3. Performance Issues**
```python
# Symptom: Slow collection times
# Solution: Optimize concurrency and connection pooling

async def optimize_performance():
    """Optimize collector performance"""
    
    # Increase concurrency for I/O bound operations
    semaphore = asyncio.Semaphore(20)
    
    # Use connection pooling
    connector = aiohttp.TCPConnector(
        limit=50,
        limit_per_host=10,
        ttl_dns_cache=300,
        use_dns_cache=True
    )
    
    # Implement request batching
    batch_size = 10
    sources = get_all_sources()
    
    for i in range(0, len(sources), batch_size):
        batch = sources[i:i + batch_size]
        tasks = [collect_source(source) for source in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
```

---

## 📊 **Performance Monitoring**

### **Real-time Metrics**
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'requests_per_second': 0,
            'success_rate': 0.0,
            'average_response_time': 0.0,
            'credits_per_hour': 0,
            'countries_used': {},
            'error_types': {}
        }
    
    def track_request(self, duration: float, success: bool, country: str, error: str = None):
        """Track individual request metrics"""
        
        # Update response time
        self.metrics['average_response_time'] = (
            (self.metrics['average_response_time'] + duration) / 2
        )
        
        # Update success rate
        total_requests = self.metrics.get('total_requests', 0) + 1
        successful_requests = self.metrics.get('successful_requests', 0) + (1 if success else 0)
        self.metrics['success_rate'] = successful_requests / total_requests
        
        # Track country usage
        self.metrics['countries_used'][country] = (
            self.metrics['countries_used'].get(country, 0) + 1
        )
        
        # Track errors
        if error:
            self.metrics['error_types'][error] = (
                self.metrics['error_types'].get(error, 0) + 1
            )
    
    def get_performance_report(self) -> dict:
        """Generate comprehensive performance report"""
        
        return {
            'performance_metrics': self.metrics,
            'recommendations': self.generate_recommendations(),
            'health_score': self.calculate_health_score()
        }
```

---

## 🚀 **Quick Start Commands**

### **1. Setup ScraperAPI**
```bash
# Set your API key
export SCRAPERAPI_KEY='your_api_key_here'

# Test connection
python3 setup_scraperapi.py

# Run dark web collector
python3 src/collectors/scraperapi_dark_web_collector.py
```

### **2. Custom Collection**
```bash
# Collect from specific sources only
python3 -c "
import asyncio
from src.collectors.scraperapi_dark_web_collector import ScraperAPIDarkWebCollector

async def custom_collection():
    async with ScraperAPIDarkWebCollector('YOUR_KEY') as collector:
        # Customize sources
        collector.dark_web_sources = {
            'hackernews': {'url': 'https://hackernews.io/', 'type': 'forum'}
        }
        items = await collector.collect_all_dark_web_intelligence()
        print(f'Collected {len(items)} items')

asyncio.run(custom_collection())
"
```

### **3. Monitor Usage**
```bash
# Check ScraperAPI dashboard
echo "Visit: https://dashboard.scraperapi.com"

# Monitor credit usage
python3 -c "
import os
from src.collectors.scraperapi_dark_web_collector import ScraperAPIClient

async def check_usage():
    client = ScraperAPIClient(os.getenv('SCRAPERAPI_KEY'))
    stats = client.get_stats()
    print(f'Credits used: {stats[\"scraperapi_stats\"][\"credits_used\"]}')
    print(f'Success rate: {stats[\"success_rate\"]:.1%}')

import asyncio
asyncio.run(check_usage())
"
```

---

## 🎯 **Advanced Use Cases**

### **1. Multi-Region Intelligence**
```python
# Collect same intelligence from multiple regions
async def multi_region_collection(url: str):
    countries = ['us', 'de', 'gb', 'nl', 'fr']
    results = {}
    
    async with ScraperAPIClient(API_KEY) as client:
        tasks = []
        for country in countries:
            task = client.get(url, country_code=country)
            tasks.append((country, task))
        
        for country, task in tasks:
            content = await task
            if content:
                results[country] = content
        
        return results
```

### **2. Real-time Threat Monitoring**
```python
# Continuous monitoring with alerts
async def continuous_monitoring():
    while True:
        # Collect latest intelligence
        items = await collector.collect_all_dark_web_intelligence()
        
        # Check for high-priority threats
        high_urgency = [item for item in items if item.urgency_level == 'high']
        
        if high_urgency:
            await send_alert(high_urgency)
        
        # Wait before next collection
        await asyncio.sleep(300)  # 5 minutes
```

### **3. Historical Analysis**
```python
# Track threat trends over time
async def trend_analysis():
    collector = ScraperAPIDarkWebCollector(API_KEY)
    
    # Collect data over time period
    historical_data = []
    for day in range(30):
        items = await collector.collect_all_dark_web_intelligence()
        historical_data.append({
            'date': datetime.now().isoformat(),
            'total_items': len(items),
            'threat_types': analyze_threat_types(items)
        })
        await asyncio.sleep(86400)  # 24 hours
    
    return historical_data
```

---

## 📈 **Success Metrics**

### **Key Performance Indicators**
- **Collection Success Rate**: >85%
- **Credit Efficiency**: <1 credit per successful item
- **Response Time**: <5 seconds average
- **Geographic Diversity**: 5+ countries used
- **Threat Coverage**: 10+ threat types detected
- **IOC Extraction Rate**: >2 IOCs per item

### **Quality Metrics**
- **Data Accuracy**: >90% relevant intelligence
- **Credibility Scoring**: >0.7 average confidence
- **False Positive Rate**: <5%
- **Completeness**: >80% of sources successful

---

## 🏆 **Conclusion**

ScraperAPI provides the **professional foundation** for dark web intelligence collection with:

✅ **Reliable proxy rotation** across 195+ countries  
✅ **Advanced JavaScript rendering** for dynamic content  
✅ **Intelligent retry logic** with multiple configurations  
✅ **Cost optimization** through smart credit management  
✅ **Comprehensive error handling** and resilience  
✅ **Real-time monitoring** and performance analytics  

The **ScraperAPI Dark Web Collector** leverages these capabilities to deliver enterprise-grade threat intelligence from underground sources while maintaining operational security and cost efficiency.

**Status: SCRAPERAPI MASTERY ACHIEVED 🚀**
