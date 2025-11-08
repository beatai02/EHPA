"""
OSINT Aggregator
Automated collection of security intelligence from multiple sources
"""

import asyncio
import aiohttp
import feedparser
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class OSINTSource:
    """Configuration for an OSINT data source"""

    def __init__(
        self,
        name: str,
        url: str,
        source_type: str = "rss",
        category: str = "general",
        update_interval: int = 3600
    ):
        self.name = name
        self.url = url
        self.source_type = source_type
        self.category = category
        self.update_interval = update_interval
        self.last_update: Optional[datetime] = None
        self.last_error: Optional[str] = None


class OSINTAggregator:
    """
    OSINT Aggregation System
    Collects security news and threat intelligence from multiple sources
    """

    def __init__(self, config: Optional[Dict] = None, data_dir: Optional[Path] = None):
        """
        Initialize OSINT aggregator

        Args:
            config: Configuration dictionary
            data_dir: Directory for storing OSINT data
        """
        self.config = config or {}
        self.data_dir = data_dir or Path("data/osint_feeds")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.sources: List[OSINTSource] = []
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.session: Optional[aiohttp.ClientSession] = None

        self._initialize_sources()

    def _initialize_sources(self):
        """Initialize default OSINT sources"""

        # Security News Feeds
        self.sources.extend([
            OSINTSource(
                name="ThreatPost",
                url="https://threatpost.com/feed/",
                source_type="rss",
                category="news",
                update_interval=3600  # 1 hour
            ),
            OSINTSource(
                name="TheHackerNews",
                url="https://feeds.feedburner.com/TheHackersNews",
                source_type="rss",
                category="news",
                update_interval=3600
            ),
            OSINTSource(
                name="BleepingComputer",
                url="https://www.bleepingcomputer.com/feed/",
                source_type="rss",
                category="news",
                update_interval=3600
            ),
            OSINTSource(
                name="CybersecurityNews",
                url="https://cybersecuritynews.com/feed/",
                source_type="rss",
                category="news",
                update_interval=3600
            ),
            OSINTSource(
                name="DarkReading",
                url="https://www.darkreading.com/rss.xml",
                source_type="rss",
                category="news",
                update_interval=3600
            ),
            OSINTSource(
                name="SecurityWeek",
                url="https://www.securityweek.com/feed/",
                source_type="rss",
                category="news",
                update_interval=3600
            )
        ])

        # Vulnerability Feeds
        self.sources.extend([
            OSINTSource(
                name="NVD Recent",
                url="https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml",
                source_type="rss",
                category="vulnerabilities",
                update_interval=7200  # 2 hours
            ),
            OSINTSource(
                name="Exploit-DB",
                url="https://www.exploit-db.com/rss.xml",
                source_type="rss",
                category="exploits",
                update_interval=7200
            )
        ])

        logger.info(f"Initialized {len(self.sources)} OSINT sources")

    async def start(self):
        """Start the OSINT aggregation service"""
        if self.running:
            logger.warning("OSINT aggregator already running")
            return

        self.running = True
        self.session = aiohttp.ClientSession()

        logger.info("🔍 Starting OSINT aggregation service")

        # Initial fetch
        await self.fetch_all_sources()

        # Start background task
        self.task = asyncio.create_task(self._aggregation_loop())

    async def stop(self):
        """Stop the OSINT aggregation service"""
        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if self.session:
            await self.session.close()

        logger.info("Stopped OSINT aggregation service")

    async def _aggregation_loop(self):
        """Background loop for periodic data collection"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Fetch sources that need updating
                await self.fetch_due_sources()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in aggregation loop: {e}")

    async def fetch_due_sources(self):
        """Fetch sources that are due for update"""
        now = datetime.utcnow()
        tasks = []

        for source in self.sources:
            if self._is_due_for_update(source, now):
                tasks.append(self.fetch_source(source))

        if tasks:
            logger.info(f"Fetching {len(tasks)} OSINT sources")
            await asyncio.gather(*tasks, return_exceptions=True)

    def _is_due_for_update(self, source: OSINTSource, now: datetime) -> bool:
        """Check if source needs updating"""
        if source.last_update is None:
            return True

        time_since_update = (now - source.last_update).total_seconds()
        return time_since_update >= source.update_interval

    async def fetch_all_sources(self):
        """Fetch all OSINT sources"""
        logger.info(f"Fetching all {len(self.sources)} OSINT sources")

        tasks = [self.fetch_source(source) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"✅ Successfully fetched {success_count}/{len(self.sources)} sources")

    async def fetch_source(self, source: OSINTSource) -> Dict:
        """
        Fetch data from a single source

        Args:
            source: OSINT source to fetch

        Returns:
            Dictionary with fetched data
        """
        try:
            logger.debug(f"Fetching {source.name} from {source.url}")

            if source.source_type == "rss":
                data = await self._fetch_rss(source)
            else:
                data = await self._fetch_generic(source)

            # Update timestamp
            source.last_update = datetime.utcnow()
            source.last_error = None

            # Save to disk
            await self._save_source_data(source, data)

            return data

        except Exception as e:
            error_msg = f"Failed to fetch {source.name}: {e}"
            logger.error(error_msg)
            source.last_error = str(e)
            return {"error": str(e), "source": source.name}

    async def _fetch_rss(self, source: OSINTSource) -> Dict:
        """Fetch RSS feed"""
        async with self.session.get(
            source.url,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            content = await response.text()

            # Parse RSS feed
            feed = feedparser.parse(content)

            items = []
            for entry in feed.entries[:50]:  # Limit to 50 most recent
                item = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "description": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                    "published_parsed": entry.get("published_parsed"),
                    "tags": [tag.term for tag in entry.get("tags", [])],
                    "source": source.name,
                    "category": source.category
                }
                items.append(item)

            return {
                "source": source.name,
                "category": source.category,
                "feed_title": feed.feed.get("title", source.name),
                "feed_url": source.url,
                "items": items,
                "total_items": len(items),
                "fetched_at": datetime.utcnow().isoformat()
            }

    async def _fetch_generic(self, source: OSINTSource) -> Dict:
        """Fetch generic URL"""
        async with self.session.get(
            source.url,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            content = await response.text()

            return {
                "source": source.name,
                "category": source.category,
                "content": content,
                "fetched_at": datetime.utcnow().isoformat()
            }

    async def _save_source_data(self, source: OSINTSource, data: Dict):
        """Save source data to disk"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{source.name.lower().replace(' ', '_')}_{timestamp}.json"
        filepath = self.data_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            # Also save latest
            latest_file = self.data_dir / f"{source.name.lower().replace(' ', '_')}_latest.json"
            with open(latest_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save data for {source.name}: {e}")

    def get_recent_items(
        self,
        category: Optional[str] = None,
        hours: int = 24,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get recent OSINT items

        Args:
            category: Filter by category (news, vulnerabilities, exploits)
            hours: Items from last N hours
            limit: Maximum number of items

        Returns:
            List of recent items
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        items = []

        # Load latest data from each source
        for source in self.sources:
            if category and source.category != category:
                continue

            latest_file = self.data_dir / f"{source.name.lower().replace(' ', '_')}_latest.json"
            if not latest_file.exists():
                continue

            try:
                with open(latest_file, 'r') as f:
                    data = json.load(f)

                for item in data.get("items", []):
                    items.append(item)

            except Exception as e:
                logger.error(f"Failed to load data for {source.name}: {e}")

        # Sort by published date (newest first)
        items.sort(key=lambda x: x.get("published", ""), reverse=True)

        return items[:limit]

    def get_source_status(self) -> List[Dict]:
        """Get status of all sources"""
        status = []

        for source in self.sources:
            status.append({
                "name": source.name,
                "url": source.url,
                "category": source.category,
                "last_update": source.last_update.isoformat() if source.last_update else None,
                "last_error": source.last_error,
                "update_interval": source.update_interval,
                "is_due": self._is_due_for_update(source, datetime.utcnow())
            })

        return status

    def search_items(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search OSINT items

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Matching items
        """
        query_lower = query.lower()
        matches = []

        all_items = self.get_recent_items(hours=168, limit=1000)  # Last week

        for item in all_items:
            title = item.get("title", "").lower()
            description = item.get("description", "").lower()

            if query_lower in title or query_lower in description:
                matches.append(item)

            if len(matches) >= limit:
                break

        return matches

    def get_statistics(self) -> Dict:
        """Get aggregator statistics"""
        return {
            "total_sources": len(self.sources),
            "by_category": {
                "news": len([s for s in self.sources if s.category == "news"]),
                "vulnerabilities": len([s for s in self.sources if s.category == "vulnerabilities"]),
                "exploits": len([s for s in self.sources if s.category == "exploits"])
            },
            "running": self.running,
            "sources_with_errors": len([s for s in self.sources if s.last_error]),
            "last_fetch_times": [
                {"name": s.name, "last_update": s.last_update.isoformat() if s.last_update else None}
                for s in self.sources
            ]
        }


# Example usage
async def example_usage():
    """Example usage of OSINT aggregator"""

    aggregator = OSINTAggregator()

    try:
        # Start aggregator
        await aggregator.start()

        # Wait for initial fetch
        await asyncio.sleep(5)

        # Get recent news
        recent_news = aggregator.get_recent_items(category="news", hours=24, limit=10)
        print(f"Recent news items: {len(recent_news)}")

        # Search for specific topic
        results = aggregator.search_items("ransomware", limit=5)
        print(f"Search results: {len(results)}")

        # Get status
        status = aggregator.get_source_status()
        print(f"Source status: {len(status)} sources")

        # Run for a while
        await asyncio.sleep(10)

    finally:
        await aggregator.stop()


if __name__ == "__main__":
    asyncio.run(example_usage())
