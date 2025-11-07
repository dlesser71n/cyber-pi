#!/usr/bin/env python3
"""
Alert Processor
Processes alerts from queue:alerts and sends notifications
"""

import asyncio
import json
from datetime import datetime, timezone
import redis.asyncio as redis

# Alert configuration
ALERT_CONFIG = {
    "critical": {
        "channels": ["console", "file"],  # Add "slack", "email" when configured
        "prefix": "🚨 CRITICAL"
    },
    "high": {
        "channels": ["console", "file"],
        "prefix": "⚠️  HIGH"
    },
    "medium": {
        "channels": ["console", "file"],
        "prefix": "📢 MEDIUM"
    }
}

async def process_alerts():
    """Process alerts from queue"""
    print("="*60)
    print("📢 ALERT PROCESSOR")
    print("="*60)
    print()

    # Connect to Redis
    redis_client = await redis.from_url(
        "redis://:cyber-pi-redis-2025@redis.cyber-pi-intel.svc.cluster.local:6379",
        encoding="utf-8",
        decode_responses=True
    )

    print("✅ Connected to Redis")
    print()

    # Check queue length
    queue_len = await redis_client.llen("queue:alerts")
    print(f"📊 Alerts in queue: {queue_len}")
    print()

    if queue_len == 0:
        print("✅ No alerts to process")
        await redis_client.aclose()
        return

    # Process all alerts
    processed = 0
    alerts_by_severity = {"critical": [], "high": [], "medium": []}

    while True:
        # Pop alert from queue
        alert_json = await redis_client.rpop("queue:alerts")
        if not alert_json:
            break

        try:
            alert = json.loads(alert_json)
            severity = alert.get('severity', 'medium')

            # Store in severity bucket
            if severity in alerts_by_severity:
                alerts_by_severity[severity].append(alert)

            # Log to file
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "alert": alert
            }

            # Append to alert log
            with open('/tmp/threat_alerts.log', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            processed += 1

        except json.JSONDecodeError as e:
            print(f"❌ Invalid alert JSON: {e}")

    # Display alerts by severity
    print(f"Processed {processed} alerts:\n")

    for severity in ['critical', 'high', 'medium']:
        alerts = alerts_by_severity[severity]
        if not alerts:
            continue

        config = ALERT_CONFIG[severity]
        print(f"{config['prefix']} - {len(alerts)} alerts")
        print("-" * 60)

        for alert in alerts:
            print(f"Type: {alert.get('type', 'unknown')}")
            print(f"Title: {alert.get('title', 'Unknown')[:70]}")
            print(f"Source: {alert.get('source', 'Unknown')}")

            if 'cve' in alert:
                print(f"CVE: {alert['cve']}")

            if 'recommendations' in alert:
                print("Actions:")
                for rec in alert['recommendations'][:3]:
                    print(f"  • {rec}")

            print()

    # Summary
    print("="*60)
    print(f"📊 Alert Processing Summary:")
    print(f"   Total processed: {processed}")
    print(f"   Critical: {len(alerts_by_severity['critical'])}")
    print(f"   High: {len(alerts_by_severity['high'])}")
    print(f"   Medium: {len(alerts_by_severity['medium'])}")
    print(f"   Log file: /tmp/threat_alerts.log")
    print("="*60)

    await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(process_alerts())
