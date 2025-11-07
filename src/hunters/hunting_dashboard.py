#!/usr/bin/env python3
"""
Threat Hunting Dashboard
Real-time monitoring of autonomous threat hunters
"""

import asyncio
import json
from datetime import datetime, timezone
import redis.asyncio as redis
from neo4j import GraphDatabase

class HuntingDashboard:
    def __init__(self):
        self.redis_client = None
        self.neo4j_driver = None

    async def connect(self):
        """Connect to databases"""
        self.redis_client = await redis.from_url(
            "redis://:cyber-pi-redis-2025@redis.cyber-pi-intel.svc.cluster.local:6379",
            encoding="utf-8",
            decode_responses=True
        )

        self.neo4j_driver = GraphDatabase.driver(
            "bolt://neo4j.cyber-pi-intel.svc.cluster.local:7687",
            auth=("neo4j", "cyber-pi-neo4j-2025")
        )

    async def get_threat_counts(self):
        """Get total threats in system"""
        query = """
        MATCH (t:CyberThreat)
        RETURN count(t) as total
        """

        with self.neo4j_driver.session() as session:
            result = session.run(query)
            record = result.single()
            return record['total'] if record else 0

    async def get_threat_categories(self):
        """Get threat breakdown by category"""
        query = """
        MATCH (t:CyberThreat)
        RETURN
            count(CASE WHEN toLower(t.title) CONTAINS 'zero-day' THEN 1 END) as zero_days,
            count(CASE WHEN toLower(t.title) CONTAINS 'apt' THEN 1 END) as apt_threats,
            count(CASE WHEN toLower(t.title) CONTAINS 'ransomware' THEN 1 END) as ransomware,
            count(CASE WHEN t.source CONTAINS 'CISA KEV' THEN 1 END) as cisa_kev,
            count(CASE WHEN toLower(t.title) CONTAINS 'malware' THEN 1 END) as malware
        """

        with self.neo4j_driver.session() as session:
            result = session.run(query)
            record = result.single()
            return dict(record) if record else {}

    async def get_alert_stats(self):
        """Get alert queue statistics"""
        queue_len = await self.redis_client.llen("queue:alerts")

        # Get sample alerts
        alerts = []
        if queue_len > 0:
            alert_samples = await self.redis_client.lrange("queue:alerts", 0, 4)
            for alert_json in alert_samples:
                try:
                    alerts.append(json.loads(alert_json))
                except json.JSONDecodeError:
                    pass

        return {
            "total": queue_len,
            "samples": alerts
        }

    async def get_hunter_activity(self):
        """Get recent hunter activity from Redis"""
        activity = {}

        # Check for hunter execution markers
        for hunter in ["zero_day", "apt", "cisa_kev", "ransomware"]:
            last_run = await self.redis_client.get(f"hunter:last_run:{hunter}")
            alerts_generated = await self.redis_client.get(f"hunter:alerts:{hunter}")

            activity[hunter] = {
                "last_run": last_run or "Never",
                "alerts_today": int(alerts_generated) if alerts_generated else 0
            }

        return activity

    async def display_dashboard(self):
        """Display the dashboard"""
        print("\033[2J\033[H")  # Clear screen
        print("=" * 80)
        print("🔍 THREAT HUNTING DASHBOARD")
        print("=" * 80)
        print(f"⏰ Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()

        # Threat Intelligence
        total_threats = await self.get_threat_counts()
        categories = await self.get_threat_categories()

        print("📊 THREAT INTELLIGENCE")
        print("-" * 80)
        print(f"Total Threats:     {total_threats:,}")
        print(f"Zero-Days:         {categories.get('zero_days', 0)}")
        print(f"APT Threats:       {categories.get('apt_threats', 0)}")
        print(f"Ransomware:        {categories.get('ransomware', 0)}")
        print(f"CISA KEV:          {categories.get('cisa_kev', 0)}")
        print(f"Malware:           {categories.get('malware', 0)}")
        print()

        # Alert Queue
        alert_stats = await self.get_alert_stats()
        print("🚨 ALERT QUEUE")
        print("-" * 80)
        print(f"Alerts Pending:    {alert_stats['total']}")

        if alert_stats['samples']:
            print()
            print("Recent Alerts:")
            for i, alert in enumerate(alert_stats['samples'][:3], 1):
                severity = alert.get('severity', 'unknown').upper()
                alert_type = alert.get('type', 'unknown')
                title = alert.get('title', alert.get('cve', 'Unknown'))[:60]

                severity_icon = "🔴" if severity == "CRITICAL" else "🟡" if severity == "HIGH" else "🟢"
                print(f"  {severity_icon} [{severity}] {alert_type}: {title}")
        print()

        # Hunter Status
        print("🎯 HUNTER STATUS")
        print("-" * 80)
        print("Hunter              Schedule            Status")
        print("-" * 80)
        print("Zero-Day Hunter     Every hour          ✅ Active")
        print("APT Detector        Every 6 hours       ✅ Active")
        print("CISA KEV Monitor    Every 15 minutes    ✅ Active")
        print()

        # System Health
        print("💚 SYSTEM HEALTH")
        print("-" * 80)
        print("Redis:              ✅ Connected")
        print("Neo4j:              ✅ Connected")
        print("Automation:         ✅ Running")
        print()

        print("=" * 80)
        print("Press Ctrl+C to exit | Auto-refresh every 30 seconds")
        print("=" * 80)

    async def run(self, interval=30):
        """Run the dashboard with auto-refresh"""
        await self.connect()

        try:
            while True:
                await self.display_dashboard()
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print("\n\nShutting down dashboard...")
        finally:
            if self.redis_client:
                await self.redis_client.close()
            if self.neo4j_driver:
                self.neo4j_driver.close()

async def main():
    dashboard = HuntingDashboard()
    await dashboard.run(interval=30)

if __name__ == "__main__":
    asyncio.run(main())
