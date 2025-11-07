#!/bin/bash
# cyber-pi Monitoring Script

echo "================================================================================"
echo "🔍 CYBER-PI MONITORING DASHBOARD"
echo "================================================================================"
echo ""

# Check if cron jobs are scheduled
echo "📅 SCHEDULED JOBS:"
echo "--------------------------------------------------------------------------------"
crontab -l | grep cyber-pi
echo ""

# Check latest collection
echo "📊 LATEST COLLECTION:"
echo "--------------------------------------------------------------------------------"
latest_collection=$(ls -t data/raw/master_collection_*.json 2>/dev/null | head -1)
if [ -n "$latest_collection" ]; then
    echo "File: $latest_collection"
    echo "Size: $(du -h "$latest_collection" | cut -f1)"
    echo "Modified: $(stat -c %y "$latest_collection" | cut -d'.' -f1)"
    
    # Count items
    items=$(python3 -c "import json; data=json.load(open('$latest_collection')); print(len(data.get('items', [])))")
    echo "Items: $items"
else
    echo "No collections found"
fi
echo ""

# Check latest reports
echo "📄 LATEST REPORTS:"
echo "--------------------------------------------------------------------------------"
report_count=$(ls data/reports/*.txt 2>/dev/null | wc -l)
echo "Total reports: $report_count"
if [ $report_count -gt 0 ]; then
    echo "Latest:"
    ls -lht data/reports/*.txt | head -3 | awk '{print "  " $9 " (" $5 ", " $6 " " $7 ")"}'
fi
echo ""

# Check logs (if they exist)
echo "📝 RECENT ACTIVITY:"
echo "--------------------------------------------------------------------------------"
if [ -f /var/log/cyber-pi-collection.log ]; then
    echo "Collection log (last 5 lines):"
    tail -5 /var/log/cyber-pi-collection.log 2>/dev/null | sed 's/^/  /'
else
    echo "Collection log: Not yet created (will be created on first run)"
fi
echo ""

# Next scheduled run
echo "⏰ NEXT SCHEDULED RUNS:"
echo "--------------------------------------------------------------------------------"
current_hour=$(date +%H)
current_min=$(date +%M)
next_collection_min=$((60 - current_min))
echo "Next collection: In $next_collection_min minutes (top of the hour)"

current_time=$(date +%H:%M)
if [ "$current_hour" -lt 7 ]; then
    echo "Next report: Today at 07:00"
else
    echo "Next report: Tomorrow at 07:00"
fi
echo ""

# System status
echo "💻 SYSTEM STATUS:"
echo "--------------------------------------------------------------------------------"
echo "Disk usage (cyber-pi):"
du -sh /home/david/projects/cyber-pi 2>/dev/null | sed 's/^/  /'
echo ""
echo "Python processes:"
ps aux | grep -E "(parallel_master|generator)" | grep -v grep | wc -l | xargs -I {} echo "  {} cyber-pi processes running"
echo ""

echo "================================================================================"
echo "✅ Monitoring complete"
echo "================================================================================"
echo ""
echo "Commands:"
echo "  View collection log: tail -f /var/log/cyber-pi-collection.log"
echo "  View report log: tail -f /var/log/cyber-pi-reports.log"
echo "  Run collection now: cd /home/david/projects/cyber-pi && python3 src/collectors/parallel_master.py"
echo "  Generate report now: cd /home/david/projects/cyber-pi && python3 src/newsletter/generator.py"
