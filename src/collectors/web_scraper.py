"""
TQAKB Advanced Web Scraper
Best-in-class web scraping with multiple strategies

Libraries integrated:
1. Playwright (best for modern JS-heavy sites)
2. Scrapy (best for large-scale scraping)
3. newspaper3k (best for articles)
4. trafilatura (best for content extraction)
5. BeautifulSoup (fallback/simple cases)
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class ScraperType(Enum):
    """Available scraper types"""
    PLAYWRIGHT = "playwright"  # Best for JS-heavy sites
    TRAFILATURA = "trafilatura"  # Best for clean content extraction
    NEWSPAPER = "newspaper"  # Best for news articles
    SCRAPY = "scrapy"  # Best for large-scale
    BEAUTIFULSOUP = "beautifulsoup"  # Simple fallback


@dataclass
class ScrapedContent:
    """Scraped content with metadata"""
    url: str
    title: str
    content: str
    author: Optional[str]
    publish_date: Optional[datetime]
    metadata: Dict[str, Any]
    scraper_used: str
    extraction_time: datetime
    success: bool
    
    def to_dict(self) -> dict:
        return {
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'metadata': self.metadata,
            'scraper_used': self.scraper_used,
            'extraction_time': self.extraction_time.isoformat(),
            'success': self.success,
            'content_length': len(self.content),
            'word_count': len(self.content.split())
        }


class AdvancedWebScraper:
    """
    Advanced web scraper with multiple strategies
    Automatically selects best scraper for the job
    """
    
    def __init__(self, preferred_scraper: ScraperType = ScraperType.TRAFILATURA):
        self.preferred_scraper = preferred_scraper
        self.available_scrapers = self._check_available_scrapers()
        logger.info(f"Advanced Web Scraper initialized: {len(self.available_scrapers)} scrapers available")
    
    def _check_available_scrapers(self) -> List[ScraperType]:
        """Check which scrapers are available"""
        available = []
        
        # Check Playwright
        try:
            from playwright.async_api import async_playwright
            available.append(ScraperType.PLAYWRIGHT)
            logger.info("✅ Playwright available")
        except ImportError:
            logger.warning("❌ Playwright not available: pip install playwright && playwright install")
        
        # Check Trafilatura
        try:
            import trafilatura
            available.append(ScraperType.TRAFILATURA)
            logger.info("✅ Trafilatura available")
        except ImportError:
            logger.warning("❌ Trafilatura not available: pip install trafilatura")
        
        # Check newspaper3k
        try:
            import newspaper
            available.append(ScraperType.NEWSPAPER)
            logger.info("✅ newspaper3k available")
        except ImportError:
            logger.warning("❌ newspaper3k not available: pip install newspaper3k")
        
        # BeautifulSoup (always try to have this as fallback)
        try:
            from bs4 import BeautifulSoup
            available.append(ScraperType.BEAUTIFULSOUP)
            logger.info("✅ BeautifulSoup available")
        except ImportError:
            logger.warning("❌ BeautifulSoup not available: pip install beautifulsoup4 lxml")
        
        return available
    
    async def scrape(self, url: str, scraper_type: Optional[ScraperType] = None) -> ScrapedContent:
        """
        Scrape content from URL using best available scraper
        
        Args:
            url: URL to scrape
            scraper_type: Force specific scraper (optional)
        
        Returns:
            ScrapedContent object
        """
        scraper = scraper_type or self.preferred_scraper
        
        # Fallback to available scrapers if preferred not available
        if scraper not in self.available_scrapers:
            if self.available_scrapers:
                scraper = self.available_scrapers[0]
                logger.info(f"Falling back to {scraper.value}")
            else:
                return self._create_error_result(url, "No scrapers available")
        
        try:
            if scraper == ScraperType.PLAYWRIGHT:
                return await self._scrape_with_playwright(url)
            elif scraper == ScraperType.TRAFILATURA:
                return await self._scrape_with_trafilatura(url)
            elif scraper == ScraperType.NEWSPAPER:
                return await self._scrape_with_newspaper(url)
            elif scraper == ScraperType.BEAUTIFULSOUP:
                return await self._scrape_with_beautifulsoup(url)
            else:
                return self._create_error_result(url, f"Unknown scraper: {scraper}")
                
        except Exception as e:
            logger.error(f"Scraping failed with {scraper.value}: {e}")
            # Try fallback scrapers
            return await self._try_fallback_scrapers(url, scraper)
    
    async def _scrape_with_playwright(self, url: str) -> ScrapedContent:
        """
        Scrape with Playwright (best for JS-heavy sites)
        Handles dynamic content, SPAs, etc.
        """
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate and wait for content
                await page.goto(url, wait_until="networkidle")
                
                # Extract content
                title = await page.title()
                content = await page.inner_text("body")
                
                # Try to get article-specific content
                article_selectors = [
                    "article",
                    "[role='main']",
                    ".article-content",
                    ".post-content",
                    "main"
                ]
                
                for selector in article_selectors:
                    try:
                        article_content = await page.inner_text(selector)
                        if len(article_content) > len(content) * 0.3:  # At least 30% of page
                            content = article_content
                            break
                    except:
                        continue
                
                # Try to extract metadata
                author = None
                publish_date = None
                
                try:
                    author = await page.get_attribute("meta[name='author']", "content")
                except:
                    pass
                
                try:
                    date_str = await page.get_attribute("meta[property='article:published_time']", "content")
                    if date_str:
                        publish_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    pass
                
                await browser.close()
                
                return ScrapedContent(
                    url=url,
                    title=title,
                    content=content,
                    author=author,
                    publish_date=publish_date,
                    metadata={'scraper': 'playwright'},
                    scraper_used='playwright',
                    extraction_time=datetime.now(),
                    success=True
                )
                
        except Exception as e:
            logger.error(f"Playwright scraping failed: {e}")
            raise
    
    async def _scrape_with_trafilatura(self, url: str) -> ScrapedContent:
        """
        Scrape with Trafilatura (best for clean content extraction)
        Excellent at removing boilerplate and extracting main content
        """
        try:
            import trafilatura
            from trafilatura.settings import use_config
            import aiohttp
            
            # Fetch HTML
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
            
            # Configure trafilatura for better extraction
            config = use_config()
            config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
            
            # Extract content
            content = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                include_images=False,
                output_format='txt',
                config=config
            )
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(html)
            
            title = metadata.title if metadata else "Unknown"
            author = metadata.author if metadata else None
            publish_date = None
            
            if metadata and metadata.date:
                try:
                    publish_date = datetime.fromisoformat(metadata.date)
                except:
                    pass
            
            return ScrapedContent(
                url=url,
                title=title,
                content=content or "",
                author=author,
                publish_date=publish_date,
                metadata={'scraper': 'trafilatura', 'sitename': metadata.sitename if metadata else None},
                scraper_used='trafilatura',
                extraction_time=datetime.now(),
                success=bool(content)
            )
            
        except Exception as e:
            logger.error(f"Trafilatura scraping failed: {e}")
            raise
    
    async def _scrape_with_newspaper(self, url: str) -> ScrapedContent:
        """
        Scrape with newspaper3k (best for news articles)
        Optimized for article extraction with good metadata
        """
        try:
            from newspaper import Article
            
            article = Article(url)
            
            # Download and parse
            await asyncio.to_thread(article.download)
            await asyncio.to_thread(article.parse)
            
            # Try NLP for keywords/summary (optional)
            try:
                await asyncio.to_thread(article.nlp)
            except:
                pass
            
            return ScrapedContent(
                url=url,
                title=article.title,
                content=article.text,
                author=", ".join(article.authors) if article.authors else None,
                publish_date=article.publish_date,
                metadata={
                    'scraper': 'newspaper',
                    'top_image': article.top_image,
                    'keywords': article.keywords if hasattr(article, 'keywords') else [],
                    'summary': article.summary if hasattr(article, 'summary') else None
                },
                scraper_used='newspaper',
                extraction_time=datetime.now(),
                success=bool(article.text)
            )
            
        except Exception as e:
            logger.error(f"newspaper3k scraping failed: {e}")
            raise
    
    async def _scrape_with_beautifulsoup(self, url: str) -> ScrapedContent:
        """
        Scrape with BeautifulSoup (simple fallback)
        Basic HTML parsing
        """
        try:
            from bs4 import BeautifulSoup
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract title
            title = soup.find('title')
            title = title.get_text().strip() if title else "Unknown"
            
            # Try to find main content
            content = ""
            
            # Try article tag first
            article = soup.find('article')
            if article:
                content = article.get_text(separator='\n', strip=True)
            else:
                # Try common content containers
                for selector in ['main', '.article-content', '.post-content', '.entry-content']:
                    element = soup.select_one(selector)
                    if element:
                        content = element.get_text(separator='\n', strip=True)
                        break
                
                # Fallback to body
                if not content:
                    body = soup.find('body')
                    if body:
                        content = body.get_text(separator='\n', strip=True)
            
            # Try to extract author
            author = None
            author_meta = soup.find('meta', {'name': 'author'})
            if author_meta:
                author = author_meta.get('content')
            
            return ScrapedContent(
                url=url,
                title=title,
                content=content,
                author=author,
                publish_date=None,
                metadata={'scraper': 'beautifulsoup'},
                scraper_used='beautifulsoup',
                extraction_time=datetime.now(),
                success=bool(content)
            )
            
        except Exception as e:
            logger.error(f"BeautifulSoup scraping failed: {e}")
            raise
    
    async def _try_fallback_scrapers(self, url: str, failed_scraper: ScraperType) -> ScrapedContent:
        """Try other available scrapers if primary fails"""
        for scraper in self.available_scrapers:
            if scraper != failed_scraper:
                try:
                    logger.info(f"Trying fallback scraper: {scraper.value}")
                    return await self.scrape(url, scraper)
                except:
                    continue
        
        return self._create_error_result(url, "All scrapers failed")
    
    def _create_error_result(self, url: str, error: str) -> ScrapedContent:
        """Create error result"""
        return ScrapedContent(
            url=url,
            title="Error",
            content="",
            author=None,
            publish_date=None,
            metadata={'error': error},
            scraper_used='none',
            extraction_time=datetime.now(),
            success=False
        )
    
    async def batch_scrape(self, urls: List[str], max_concurrent: int = 5) -> List[ScrapedContent]:
        """
        Scrape multiple URLs concurrently
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
        
        Returns:
            List of ScrapedContent objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_limit(url: str) -> ScrapedContent:
            async with semaphore:
                return await self.scrape(url)
        
        tasks = [scrape_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(self._create_error_result(urls[i], str(result)))
            else:
                final_results.append(result)
        
        return final_results


# Factory function
def create_scraper(scraper_type: str = "trafilatura") -> AdvancedWebScraper:
    """
    Create an advanced web scraper
    
    Available types:
    - playwright: Best for JS-heavy sites (requires: playwright install)
    - trafilatura: Best for clean content extraction (RECOMMENDED)
    - newspaper: Best for news articles
    - beautifulsoup: Simple fallback
    """
    scraper_enum = ScraperType(scraper_type)
    return AdvancedWebScraper(preferred_scraper=scraper_enum)


if __name__ == "__main__":
    print("🚀 TQAKB Advanced Web Scraper")
    print("=" * 60)
    print("✅ Best-in-Class Web Scraping:")
    print("   1. Playwright - JS-heavy sites, SPAs, dynamic content")
    print("   2. Trafilatura - Clean content extraction (RECOMMENDED)")
    print("   3. newspaper3k - News articles with metadata")
    print("   4. BeautifulSoup - Simple fallback")
    print("\n📦 Installation:")
    print("   pip install trafilatura  # Recommended")
    print("   pip install playwright && playwright install  # For JS sites")
    print("   pip install newspaper3k  # For news articles")
    print("   pip install beautifulsoup4 lxml  # Fallback")
    print("\n🎯 Trafilatura is BEST for most use cases!")
    print("   - Excellent content extraction")
    print("   - Removes boilerplate automatically")
    print("   - Fast and reliable")
    print("   - No browser overhead")
