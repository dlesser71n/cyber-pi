# cyber-pi Collection Schedule

## 🔄 Recommended Collection Cycles

### **Current Performance**
- **Collection Time**: 22 seconds (61 sources)
- **Classification Time**: 40 seconds (BART GPU)
- **Report Generation**: 5 seconds
- **Total Cycle**: ~70 seconds (just over 1 minute!)

---

## 📅 Recommended Schedules

### **Option 1: Continuous (Real-Time)** ⚡
```bash
# Run every 5 minutes
*/5 * * * * cd /home/david/projects/cyber-pi && python3 src/collectors/parallel_master.py
```

**Pros:**
- Near real-time intelligence
- Catch breaking threats immediately
- 288 collections per day
- ~440,000 items/day potential

**Cons:**
- High system load
- May hit rate limits on some sources
- Lots of duplicate data

**Best for:** Critical infrastructure, high-security environments

---

### **Option 2: Hourly (Recommended)** ✅
```bash
# Run every hour
0 * * * * cd /home/david/projects/cyber-pi && python3 src/collectors/parallel_master.py
```

**Pros:**
- Good balance of freshness and efficiency
- 24 collections per day
- ~36,000 items/day
- Respects source rate limits
- Manageable data volume

**Cons:**
- Up to 1 hour delay for breaking news

**Best for:** Most organizations, Nexum clients

---

### **Option 3: Every 4 Hours** 🕐
```bash
# Run at 12am, 4am, 8am, 12pm, 4pm, 8pm
0 */4 * * * cd /home/david/projects/cyber-pi && python3 src/collectors/parallel_master.py
```

**Pros:**
- 6 collections per day
- ~9,000 items/day
- Low system impact
- Good for reporting cycles

**Cons:**
- Up to 4 hour delay

**Best for:** Weekly/daily reports, lower priority monitoring

---

### **Option 4: Daily (Morning Brief)** 📰
```bash
# Run once daily at 6am
0 6 * * * cd /home/david/projects/cyber-pi && python3 src/collectors/parallel_master.py
```

**Pros:**
- 1 collection per day
- ~1,500 items/day
- Perfect for daily newsletter
- Minimal system impact

**Cons:**
- Not real-time
- Miss time-sensitive threats

**Best for:** Daily briefings, executive summaries

---

## 🎯 Recommended: Hourly Collection

### **Why Hourly is Best:**

1. **Fresh Intelligence**: 1-hour old max
2. **Manageable Volume**: ~1,500 items/hour
3. **Respects Rate Limits**: Doesn't overwhelm sources
4. **Good for Reports**: Can generate reports on any schedule
5. **System Friendly**: Only 70 seconds/hour of processing

### **Data Volume:**
- **Per Collection**: ~1,500 items
- **Per Day**: ~36,000 items (24 collections)
- **Per Week**: ~252,000 items
- **Per Month**: ~1,080,000 items

### **Storage:**
- **Per Collection**: ~5MB JSON
- **Per Day**: ~120MB
- **Per Month**: ~3.6GB
- **With 30TB storage**: Can store 8,000+ months of data!

---

## 🔧 Implementation

### **Setup Cron Job (Hourly)**

```bash
# Edit crontab
crontab -e

# Add this line:
0 * * * * cd /home/david/projects/cyber-pi && /usr/bin/python3 src/collectors/parallel_master.py >> /var/log/cyber-pi.log 2>&1
```

### **Or Use Systemd Timer (Better)**

Create `/etc/systemd/system/cyber-pi.service`:
```ini
[Unit]
Description=Cyber-PI Intelligence Collection
After=network.target

[Service]
Type=oneshot
User=david
WorkingDirectory=/home/david/projects/cyber-pi
ExecStart=/usr/bin/python3 src/collectors/parallel_master.py
StandardOutput=append:/var/log/cyber-pi.log
StandardError=append:/var/log/cyber-pi-error.log
```

Create `/etc/systemd/system/cyber-pi.timer`:
```ini
[Unit]
Description=Cyber-PI Collection Timer
Requires=cyber-pi.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable cyber-pi.timer
sudo systemctl start cyber-pi.timer
```

---

## 📊 Report Generation Schedule

### **Separate from Collection**

Reports can be generated on different schedule:

**Daily Reports** (Morning Brief):
```bash
# Generate report at 7am daily
0 7 * * * cd /home/david/projects/cyber-pi && python3 src/newsletter/generator.py
```

**Weekly Reports** (Monday Morning):
```bash
# Generate weekly report Monday 8am
0 8 * * 1 cd /home/david/projects/cyber-pi && python3 src/newsletter/generator.py
```

**Real-Time Alerts** (High Priority Only):
```bash
# Check for critical threats every 15 minutes
*/15 * * * * cd /home/david/projects/cyber-pi && python3 scripts/check_critical.py
```

---

## 🎯 Recommended Setup for Nexum

### **Collection**: Every Hour
- Runs 24/7
- Collects ~36,000 items/day
- Always fresh intelligence

### **Reports**: 
- **Daily Brief**: 7am (yesterday's threats)
- **Weekly Summary**: Monday 8am (last week)
- **Monthly Report**: 1st of month, 9am
- **Critical Alerts**: Real-time (as detected)

### **Client Delivery**:
- **Airlines**: Daily + real-time critical
- **Power Companies**: Daily + real-time critical
- **Hospitals**: Daily + real-time critical
- **Government**: Daily
- **Universities**: Weekly

---

## 💡 Advanced: Multi-Tier Collection

### **Tier 1: Critical Sources (Every 15 min)**
```bash
# Government, ICS-CERT, critical vendors
*/15 * * * * python3 src/collectors/parallel_master.py --categories=government,industrial_ot
```

### **Tier 2: Important Sources (Hourly)**
```bash
# Vendor advisories, major news
0 * * * * python3 src/collectors/parallel_master.py --categories=nexum_vendors,news_research
```

### **Tier 3: General Sources (Every 4 hours)**
```bash
# Technical feeds, social media
0 */4 * * * python3 src/collectors/parallel_master.py --categories=technical,threat_intelligence
```

---

## 📈 Scaling Considerations

### **Current Capacity**
- **Collection**: 69 items/sec = 248,400 items/hour
- **Classification**: 40 items/sec = 144,000 items/hour
- **Bottleneck**: None! System can handle much more

### **Can Scale To**
- **150+ sources**: Still under 2 minutes/collection
- **10,000+ items/hour**: No problem
- **Real-time processing**: Easily achievable

---

## 🎯 Bottom Line

**Recommended for Nexum:**

```
Collection: Every hour (24/7)
Reports: Daily at 7am
Alerts: Real-time for critical
Storage: Keep 90 days, archive rest
```

**This gives you:**
- ✅ Fresh intelligence (max 1 hour old)
- ✅ Manageable data volume
- ✅ Daily client reports
- ✅ Real-time critical alerts
- ✅ Minimal system impact (70 sec/hour)

**Total system usage: 28 minutes/day (2% of time!)**

---

## 🚀 Quick Start

**Start hourly collection now:**
```bash
# Add to crontab
echo "0 * * * * cd /home/david/projects/cyber-pi && /usr/bin/python3 src/collectors/parallel_master.py" | crontab -
```

**Verify it's scheduled:**
```bash
crontab -l
```

**Done!** cyber-pi will now run every hour automatically! 🎉
