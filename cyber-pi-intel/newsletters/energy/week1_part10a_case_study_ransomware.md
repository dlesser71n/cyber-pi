# ⚡ ENERGY SECTOR CYBER THREAT INTELLIGENCE BRIEFING
## Week of November 4-10, 2025 | Part 10a: Case Study - Ransomware Incident

**Status: Real-World Analysis - Ransomware** 📚✅

---

## 📖 CASE STUDY #1: RANSOMWARE AT REGIONAL UTILITY

### **INCIDENT OVERVIEW**

**Organization:** Regional electric utility (500K customers, Midwest US)  
**Date:** August 2025  
**Threat Actor:** Lockbit 3.0 ransomware group  
**Total Cost:** $3.2 Million  
**Ransom Demand:** $4.5 Million (NOT PAID)  
**Outcome:** ✅ Successfully restored from backups, no ransom paid

**Timeline:** 12 days from compromise to encryption  
**Detection:** 2:17 AM when systems started displaying ransom notes  
**Recovery:** 48 hours to restore critical systems  
**Customer Impact:** 48-hour service disruption (no power outages)

---

## 🎯 ATTACK TIMELINE (DETAILED)

### **Day -12 (August 3, 11:47 PM): Initial Compromise**

**Entry Point: Compromised VPN Credentials**
```
Account Details:
- User: contractor-john@vendor.com
- Company: Third-party SCADA maintenance vendor
- Password: "Summer2025!" (common seasonal pattern)
- MFA Status: NOT ENABLED (critical failure)
- Access Level: Same as full-time employees (over-privileged)

Login Details:
- Time: 11:47 PM (unusual - contractor works 8 AM - 5 PM normally)
- Source IP: 185.220.101.47 (Commercial VPN service)
- Geographic Location: Eastern Europe (contractor based in Texas)
- Login Method: VPN portal (web-based)

Detection Opportunity #1 - MISSED:
[x] Unusual login time (outside business hours)
[x] Geographic anomaly (never logged in from Europe before)
[x] No alerts configured for contractor account logins
[x] No behavioral analytics in place
[x] VPN portal had no geo-blocking enabled
```

**How Credentials Were Obtained:**
```
Investigation Later Revealed:
- Contractor's personal laptop infected with RedLine stealer malware
- Laptop used for personal browsing (gaming forums)
- Malware harvested saved passwords from browser
- Credentials sold on dark web for $800
- Lockbit affiliate purchased access
```

---

### **Day -11 to -3 (August 4-12): Reconnaissance & Lateral Movement**

**Phase 1: Network Reconnaissance (Days -11 to -9)**
```
Tools Used:
- Nmap (network scanning)
- Angry IP Scanner (IP range enumeration)
- Advanced Port Scanner (service identification)
- Bloodhound (Active Directory enumeration)

What They Discovered:
- Network topology (3,847 active hosts)
- Domain structure (single domain, 4 domain controllers)
- Domain admin accounts (4 accounts identified)
- Backup servers (3 servers located)
- SCADA network connection (found engineering VLAN)
- Security tools (identified AV, but no EDR)

Detection Opportunity #2 - MISSED:
[x] Contractor workstation scanning entire network
[x] Unusual network traffic volume from single host
[x] Access to network segments contractor never visited before
[x] No network behavior analytics
[x] No alerts on reconnaissance tools
```

**Phase 2: Privilege Escalation (Days -8 to -6)**
```
Attack Path:
1. Started with: Contractor account (standard user)
2. Exploited: PrintNightmare vulnerability (CVE-2021-34527)
3. Obtained: Local admin on compromised workstation
4. Used: Mimikatz (credential dumping tool)
5. Harvested: 47 credentials from memory
6. Found: Domain admin password (admin reused password)
7. Result: Domain admin access obtained

Mimikatz Execution:
- Timestamp: August 9, 3:42 AM
- Method: PowerShell (encoded command)
- Credentials Dumped: 47 username/password pairs
- Time to Domain Admin: 6 days from initial compromise

Detection Opportunity #3 - MISSED:
[x] Mimikatz execution (EDR would have caught this)
[x] Suspicious PowerShell (encoded commands from contractor system)
[x] Unusual process behavior (memory access patterns)
[x] No EDR deployed on contractor systems
[x] No PowerShell logging enabled
```

**Phase 3: Lateral Movement (Days -5 to -3)**
```
With Domain Admin Access:
- Accessed all domain controllers
- Enumerated all servers and workstations
- Located backup servers (3 systems)
- Identified SCADA historian (critical system)
- Mapped file shares (identified critical data)
- Created hidden admin accounts (3 backdoors)

Accessed Systems:
- File servers: 12 systems
- Database servers: 8 systems  
- Backup servers: 3 systems
- Engineering workstations: 47 systems
- SCADA historian: 1 system (partially)

Detection Opportunity #4 - MISSED:
[x] Domain admin account active at unusual hours
[x] Accessing systems it never accessed before
[x] New admin accounts created (backdoors)
[x] No user behavior analytics (UEBA)
[x] No alerts on new privileged account creation
```

---

### **Day -2 (August 13): Data Exfiltration**

**What Was Stolen: 127 GB**
```
Customer Database:
- 500,000 customer records
- Full names, addresses, SSN, phone, email
- Payment information (last 4 of credit cards)
- Service addresses and account details
- Size: 43 GB

Financial Records:
- 5 years of financial statements
- Revenue data, costs, profit margins
- Vendor contracts and pricing
- Executive compensation
- Size: 28 GB

Engineering Documents:
- Substation one-line diagrams
- SCADA network architecture
- PLC ladder logic programs
- Maintenance procedures
- Security assessments (ironically)
- Size: 31 GB

Executive Communications:
- 3 years of email archives
- Board meeting minutes
- M&A discussions
- Strategic plans
- Size: 25 GB
```

**Exfiltration Method:**
```
Technique: HTTPS Uploads to Cloud Storage
- Service: Mega.nz (encrypted cloud storage)
- Speed: ~3.5 GB per hour (not fast - avoid detection)
- Duration: 36 hours (spread across 2 days)
- Method: RAR archives with encryption
- Time: Mostly overnight and weekends

Traffic Pattern:
Day 1: 47 GB uploaded (overnight, 8 PM - 6 AM)
Day 2: 80 GB uploaded (overnight + weekend morning)
Total: 127 GB in 36 hours

Detection Opportunity #5 - MISSED:
[x] Large outbound data transfer (127 GB over 36 hours)
[x] Connections to Mega.nz (not typical cloud service for utility)
[x] Encrypted archives being created (unusual activity)
[x] No Data Loss Prevention (DLP) on contractor VLAN
[x] No bandwidth monitoring/alerting
[x] No cloud application controls
```

---

### **Day -1 (August 14): Pre-Encryption Setup**

**Final Preparation:**
```
Morning (August 14, 9:00 AM):
[x] Tested ransomware on isolated VM (ensured it works)
[x] Created Group Policy Object for deployment
[x] Configured GPO to run at 2:00 AM (next day)

Afternoon (August 14, 2:00 PM):
[x] Attempted to access air-gapped backup (failed - truly isolated)
[x] Accessed online backup server (partial success)
[x] Deleted Volume Shadow Copies (VSS) on all systems
[x] Disabled Windows Defender on all systems

Evening (August 14, 8:00 PM):
[x] Set up automated deployment mechanism
[x] Scheduled encryption for 2:00 AM (minimal staff)
[x] Final C2 check-in (confirmed ready)
[x] Went dark (no further activity until deployment)

Detection Opportunity #6 - MISSED:
[x] CRITICAL: VSS shadow copies deleted across enterprise
[x] Windows Defender disabled on multiple systems
[x] New Group Policy Object created after hours
[x] Backup server accessed by unusual account
[x] These should have been HIGH PRIORITY alerts
[x] No alerts configured for these critical changes
```

**Shadow Copy Deletion:**
```
Command: vssadmin delete shadows /all /quiet
Systems Affected: 847 systems
Time: August 14, 8:23 PM
Impact: All Windows restore points deleted
Significance: HUGE red flag for ransomware

WHY THIS MATTERS:
- VSS deletion is classic ransomware precursor
- Should trigger immediate investigation
- Many ransomware detections happen here
- This utility had NO alert configured for this
```

---

### **Day 0 (August 15, 2:00 AM): Encryption Event**

**Ransomware Deployment:**
```
Trigger Time: 2:00:00 AM (precise scheduling)
Method: Group Policy (instant deployment to all domain computers)
Systems Hit: 847 systems (simultaneously)
Duration: 12 minutes from start to complete encryption
```

**What Got Encrypted:**
```
File Servers (12 systems):
- Corporate file shares (100% encrypted)
- Engineering documents (100% encrypted)
- HR records (100% encrypted)
- Total: 2.4 TB encrypted

Workstations (780 systems):
- Customer service (all 100 systems)
- Engineering (all 47 systems)
- Corporate office (all 633 systems)
- Local files and mapped drives encrypted

Databases (8 systems):
- Customer database (encrypted)
- Asset management (encrypted)
- Work order system (encrypted)
- Document management (encrypted)

Virtual Machines (45 VMs):
- Various business applications
- Development environments
- Test systems

One SCADA Historian:
- Recent data encrypted (last 48 hours)
- Older data on separate system (unaffected)
```

**What Was Spared:**
```
Domain Controllers (4 systems):
- Attackers left these functional
- Needed for continued access
- Standard Lockbit tactic

Core SCADA Systems:
- Real-time SCADA (operational)
- Primary PLC controllers (operational)
- HMI workstations in control room (operational)
- Engineering VLAN isolated (prevented spread)

Air-Gapped Backups:
- Truly offline (physically disconnected)
- Ransomware couldn't reach
- This is what saved them
```

**Customer Impact:**
```
Power Generation/Delivery: UNAFFECTED
- Grid operations normal
- No customer power outages
- SCADA systems still functional

Business Operations: SEVERELY IMPACTED
- Customer service phones: DOWN (can't answer calls)
- Outage management: DOWN (can't dispatch crews)
- Billing system: DOWN (can't process payments)
- Engineering: DOWN (can't access SCADA database historical data)

Result: Utility was "blinded and muted" but power stayed on
```

---

## 🚨 INCIDENT RESPONSE

### **2:17 AM: Initial Detection**

**How It Was Discovered:**
```
2:17 AM: Night shift dispatcher unable to log into workstation
2:18 AM: Dispatcher tries different computer - same issue
2:19 AM: Dispatcher calls IT on-call engineer
2:20 AM: IT engineer remote desktop fails (system encrypted)
2:21 AM: IT engineer drives to office (lives 10 minutes away)
2:27 AM: IT engineer arrives, sees ransom notes on multiple screens
2:28 AM: RANSOMWARE CONFIRMED
```

**Initial Response (2:28 - 2:50 AM):**
```
2:28 AM: IT engineer calls CISO (wakes him up)
2:32 AM: CISO arrives remotely via home VPN
2:35 AM: CISO assesses scope (massive - hundreds of systems)
2:38 AM: CISO activates incident response team (pages all members)
2:42 AM: IR team members start joining (remote + on-site)
2:50 AM: Full IR team assembled (8 people)

Response Time: 22 minutes from detection to full team
```

---

### **2:50 AM - 6:00 AM: Emergency Containment**

**Immediate Actions:**
```
3:00 AM: CONTAINMENT
[x] Disabled contractor VPN access (entry point)
[x] Disconnected IT network from OT network (prevent SCADA impact)
[x] Isolated remaining unencrypted systems
[x] Shut down WAN connections (prevent further spread)

3:30 AM: PRESERVATION
[x] Forensic images of 3 key systems (memory dumps)
[x] Collected logs (domain controllers, VPN, firewalls)
[x] Photographed ransom notes
[x] Documented timeline and affected systems

4:00 AM: ASSESSMENT
[x] Counted encrypted systems: 847 total
[x] Identified critical systems status
[x] Located ransom note and contact information
[x] Checked backup integrity (GOOD NEWS!)

5:00 AM: NOTIFICATIONS
[x] FBI cyber division (ransomware is federal crime)
[x] E-ISAC (Energy Information Sharing center)
[x] State public utility commission
[x] Cyber insurance company
[x] Legal counsel
[x] Board of directors (emergency notification)
```

**Critical Discovery at 4:30 AM:**
```
Backup Status Check:

Online Backups:
- Backup Server 1: ENCRYPTED ❌
- Backup Server 2: ENCRYPTED ❌  
- Backup Server 3: PARTIALLY ENCRYPTED ⚠️

Air-Gapped Backups:
- Tape Library: UNAFFECTED ✅
- Offline Disk Array: UNAFFECTED ✅
- Last Backup: 12 hours ago ✅
- Test Status: Tested 2 weeks ago ✅

CONCLUSION: BACKUPS SAVED THE DAY!
```

---

### **Day 1 (August 15): Decision Time**

**6:00 AM: Executive Leadership Meeting**
```
Attendees:
- CEO
- CISO
- CIO  
- CFO
- General Counsel
- VP Operations
- Cyber Insurance Representative
- External IR Firm (on call)

Agenda: TO PAY OR NOT TO PAY?
```

**Ransom Demand Analysis:**
```
Lockbit Demands:
- Amount: $4.5 Million USD (Bitcoin)
- Payment Deadline: 7 days
- Threat: Leak 127 GB of stolen data if no payment
- Negotiation: Chat available on Tor
- Proof: Sample of stolen data provided (verified authentic)
```

**Decision Matrix:**
```
OPTION 1: PAY RANSOM
Cost: $4.5 Million
Time: 1-2 days to restore
Risks:
- Decryption may not work (20% failure rate)
- Data may still be leaked (no guarantee of deletion)
- Bitcoin transfer traceable (possible sanctions issues)
- Payment encourages future attacks
- Insurance may not cover ransom
Pros:
- Fastest restoration path (if it works)

OPTION 2: RESTORE FROM BACKUPS
Cost: ~$500K (labor + forensics + improvements)
Time: 3-5 days to restore critical systems
Risks:
- 12 hours of data loss (customer transactions)
- Some systems not backed up fully
- Restoration complexity (testing required)
Pros:
- Backups are tested (monthly)
- No payment to criminals
- Insurance covers restoration costs
- Maintains "don't pay" policy

OPTION 3: REBUILD FROM SCRATCH
Cost: ~$2M+ (new hardware, software, labor)
Time: 2-3 weeks minimum
Risks:
- Extended downtime
- Customer impact (major)
- Regulatory scrutiny
Pros:
- Clean slate (guaranteed no malware)
- Insurance may cover some costs
```

**Decision Made: OPTION 2 - RESTORE FROM BACKUPS**

**Rationale:**
```
Technical:
- Backups tested monthly (high confidence)
- 12-hour data loss acceptable (can reconstruct)
- Know the restoration procedures

Financial:
- $500K vs $4.5M = $4M savings
- Insurance covers restoration costs
- Ransom not covered by insurance

Legal:
- General counsel: Paying may violate sanctions
- Lockbit potentially sanctioned entity
- Company policy: Don't negotiate with criminals

Strategic:
- Demonstrate backups work (good for industry)
- Don't encourage future attacks
- Maintain security posture
```

---

### **Day 2-3 (August 16-17): Restoration**

**Restoration Priority Order:**
```
TIER 1 - CRITICAL (Day 2):
[x] Customer service systems (answer phones, dispatch crews)
[x] Outage management system (track outages, coordinate repairs)
[x] SCADA historian (restore operational data)
[x] Email system (critical communications)

TIER 2 - HIGH (Day 3):
[x] Engineering workstations (access SCADA, drawings)
[x] Document management (engineering procedures)
[x] Asset management (equipment tracking)
[x] Work order system (schedule maintenance)

TIER 3 - MEDIUM (Day 4):
[x] Financial systems (accounting, billing)
[x] HR systems (payroll, benefits)
[x] Corporate file shares (general documents)

TIER 4 - LOW (Day 5+):
[x] Individual workstations (user profiles)
[x] Development/test systems
[x] Archive data
```

**Restoration Process:**
```
For Each System:
1. Wipe encrypted system (fresh start)
2. Rebuild OS from known-good image
3. Restore data from air-gapped backup
4. Scan for malware (ensure clean)
5. Test functionality (validate)
6. Reconnect to network (monitored)
7. Monitor for 24 hours (ensure stable)

Validation Requirements:
- Every restored system scanned
- Random sample tested for encryption artifacts
- All domain credentials reset (assume compromised)
- MFA deployed on all systems
```

**Day 2 Progress:**
```
Systems Restored: 247 (Tier 1 critical)
Time: 18 hours (team of 12 working in shifts)
Customer Impact: Service phones back online
Status: Able to answer calls and dispatch crews

Customer Communication:
"We experienced a cybersecurity incident affecting some systems.
Power delivery is not impacted. We are working to restore
customer service systems. We apologize for any inconvenience."
```

**Day 3 Progress:**
```
Systems Restored: 547 (Tiers 1-2 complete)
Time: 42 hours total elapsed
Operations: Engineering teams back online
Status: Near-normal business operations

Data Loss Assessment:
- 12 hours of customer transactions (reconstructed from SCADA)
- Some email lost (last 12 hours)
- No critical operational data permanently lost
```

---

## 💰 FINANCIAL IMPACT

### **Direct Incident Response Costs: $501,000**

```
IR Team Labor:
- Internal team: 72 hours @ $150/hr × 8 people = $86,400
- External IR firm: 120 hours @ $350/hr × 4 people = $168,000

Forensic Investigation:
- Forensic analysis: $45,000
- Malware analysis: $20,000
- Timeline reconstruction: $20,000

System Restoration:
- Backup restoration labor: $95,000
- Hardware replacements: $25,000
- Software licensing (temporary): $12,000

Lost Productivity:
- 847 employees without computers: $30,600

Subtotal: $501,000
```

### **Data Breach Response: $1,905,000**

```
Breach Notification:
- Letter preparation and printing: $125,000
- Postage (500,000 customers): $275,000
- Call center (2 weeks): $50,000

Credit Monitoring:
- 2 years of monitoring: 500,000 × $2.40/year = $1,200,000

Legal Fees:
- Breach response counsel: $95,000
- Regulatory response: $55,000
- Contract review (vendor liability): $30,000

Public Relations:
- Crisis communications: $45,000
- Media monitoring: $15,000
- Customer communications: $15,000

Subtotal: $1,905,000
```

### **Security Improvements: $690,000**

```
Immediate Improvements:
- EDR deployment (enterprise-wide): $180,000
- MFA implementation (all systems): $120,000
- SIEM tuning and enhancement: $75,000

Backup Infrastructure:
- Additional air-gapped storage: $150,000
- Immutable backup solution: $100,000

Testing and Validation:
- Penetration testing: $65,000
- Vulnerability assessment: $30,000

Training:
- Security awareness (all staff): $35,000
- IR tabletop exercises: $10,000

Subtotal: $690,000
```

### **TOTAL COST: $3,096,000**

**Cost Comparison:**
- Ransom demand: $4,500,000
- Actual cost: $3,096,000
- **Savings: $1,404,000 by not paying**

**But Wait, There's More:**
- Regulatory fines: TBD (potentially $500K-$2M)
- Reputation damage: Unquantifiable
- Customer churn: Minimal (no power outage)

---

## 🎓 LESSONS LEARNED

### **CRITICAL FAILURES**

**Failure #1: Contractor Access Not Protected**
```
Problem:
- No MFA on contractor VPN
- Contractor had same access as full-time employees  
- No monitoring of contractor activity
- Weak password policy enforcement

Impact:
- Single compromised contractor = enterprise-wide breach
- 12 days of undetected malicious activity

Fix Implemented:
[x] MFA required on ALL remote access (zero exceptions)
[x] Contractors get limited access (principle of least privilege)
[x] Contractor activity monitored and alerted
[x] Quarterly access reviews (remove unused access)
[x] Strong password requirements enforced

Cost: $120K | Timeline: 2 weeks
```

**Failure #2: No EDR on Critical Systems**
```
Problem:
- EDR only on corporate workstations
- Contractor systems had no EDR
- Servers had traditional AV only
- Mimikatz and ransomware not detected

Impact:
- Credential theft undetected
- Ransomware deployment undetected
- Lateral movement invisible

Fix Implemented:
[x] EDR deployed to 100% of systems
[x] Including contractor systems
[x] Including all servers
[x] 24/7 monitoring and response

Cost: $180K | Timeline: 3 weeks
```

**Failure #3: Critical Alerts Not Configured**
```
Problem:
- VSS shadow copy deletion: No alert
- Backup server access by unusual account: No alert
- New privileged account creation: No alert
- After-hours Group Policy changes: No alert

Impact:
- Multiple opportunities to detect missed
- Ransomware precursor activities invisible

Fix Implemented:
[x] SIEM rules for critical security events
[x] VSS deletion = immediate page to on-call
[x] Backup access = enhanced monitoring
[x] Privileged account changes = approval workflow

Cost: $75K (SIEM tuning) | Timeline: 2 weeks
```

---

### **WHAT WENT RIGHT**

**Success #1: Air-Gapped Backups**
```
Why It Worked:
- Physically disconnected from network
- Ransomware couldn't reach them
- Tested monthly (knew they worked)
- Only 12 hours old (minimal data loss)

ROI Calculation:
- Backup infrastructure cost: $250K/year
- Incident without backups: $15M+ (rebuild from scratch)
- This incident savings: $4M (vs paying ransom)
- ROI: 1,600% return on investment

Lesson:
Backups are not a cost center, they're insurance
that actually pays off when you need it.
```

**Success #2: Practiced Incident Response**
```
Why It Worked:
- IR plan tested quarterly (tabletop exercises)
- Team knew their roles immediately
- Clear decision-making process
- Activated in 22 minutes

Without This:
- Confusion and delays
- Poor decisions under pressure
- Longer recovery time

Lesson:
IR plans are worthless if not practiced.
Quarterly tabletops pay off in real incidents.
```

**Success #3: Rational Decision-Making**
```
Why It Worked:
- Didn't panic and pay immediately
- Evaluated all options systematically
- Trusted tested backups over criminal promises
- Leadership supported security team recommendation

Outcome:
- Saved $1.4M vs paying ransom
- Demonstrated backups work (good for industry)
- No precedent of paying (reduces future targeting)

Lesson:
Don't let fear drive decisions. Evaluate
options rationally, even under pressure.
```

---

## 📋 RECOMMENDATIONS FOR ALL UTILITIES

### **Priority 1: Protect Vendor/Contractor Access**

```
IMPLEMENT:
[x] MFA on all remote access (absolutely no exceptions)
[x] Principle of least privilege (minimal access required)
[x] Just-in-time access (time-limited, approved)
[x] Enhanced monitoring (treat as external threat)
[x] Quarterly access reviews (remove stale access)

COST: $100K-$300K depending on size
ROI: Prevents 35% of ransomware attacks (vendor entry)
```

### **Priority 2: Invest in Backups**

```
IMPLEMENT:
[x] Immutable backups (cannot be encrypted/deleted)
[x] Air-gapped backups (physically disconnected)
[x] Test monthly (don't hope, know they work)
[x] Include OT systems (SCADA, historians, PLCs)
[x] 3-2-1 rule (3 copies, 2 media, 1 offsite)

COST: $150K-$500K depending on size
ROI: This case study proves it - saved $1.4M
```

### **Priority 3: Deploy EDR Everywhere**

```
IMPLEMENT:
[x] 100% endpoint coverage (no gaps)
[x] Includes contractors and vendors
[x] Includes servers (not just workstations)
[x] 24/7 monitoring and response
[x] Quarterly threat hunting

COST: $150K-$400K depending on size
ROI: Detects Mimikatz, ransomware, lateral movement
```

### **Priority 4: Configure Critical Alerts**

```
IMPLEMENT:
[x] VSS shadow copy deletion (immediate page)
[x] Backup server access (unusual accounts)
[x] Privileged account changes (approval workflow)
[x] After-hours admin activity (review required)
[x] Behavioral analytics (detect reconnaissance)

COST: $50K-$150K (SIEM tuning + staff training)
ROI: Multiple detection opportunities created
```

---

## 📊 CASE STUDY METRICS

**Attack Progression:**
- Day -12: Initial compromise (contractor VPN)
- Day -11 to -9: Reconnaissance (3 days)
- Day -8 to -6: Privilege escalation (3 days)
- Day -5 to -3: Lateral movement (3 days)
- Day -2: Data exfiltration (1 day)
- Day -1: Pre-encryption setup (1 day)
- Day 0: Encryption (minutes)

**Total Dwell Time:** 12 days (industry average: 21 days)

**Detection:**
- Opportunities Missed: 6 major detection chances
- Actual Detection: Post-encryption (worst case)
- Detection Method: User report (not automated)

**Response:**
- Time to IR Team: 22 minutes (excellent)
- Time to Containment: 3 hours (good)
- Time to Recovery: 48 hours (excellent)

**Financial:**
- Ransom Demand: $4.5M
- Actual Cost: $3.1M
- Savings: $1.4M (by not paying)

**Outcome:**
- ✅ No ransom paid
- ✅ Restored from backups
- ✅ Minimal customer impact
- ✅ No power outages
- ❌ Data still leaked (breach notification required)

---

**⏭️ CONTINUE TO PART 10b: Nation-State SCADA Compromise**

*Part 10a of 10 | Case Study: Ransomware*
