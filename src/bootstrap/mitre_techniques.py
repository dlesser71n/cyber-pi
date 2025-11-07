#!/usr/bin/env python3
"""
MITRE ATT&CK Techniques Data
"""

# A selection of MITRE ATT&CK techniques
MITRE_TECHNIQUES = {
    # Initial Access
    "T1189": {"name": "Drive-by Compromise", "tactic": "TA0001"},
    "T1190": {"name": "Exploit Public-Facing Application", "tactic": "TA0001"},
    "T1133": {"name": "External Remote Services", "tactic": "TA0001"},
    "T1566": {"name": "Phishing", "tactic": "TA0001"},
    
    # Execution
    "T1059": {"name": "Command and Scripting Interpreter", "tactic": "TA0002"},
    "T1203": {"name": "Exploitation for Client Execution", "tactic": "TA0002"},
    "T1106": {"name": "Native API", "tactic": "TA0002"},
    "T1053": {"name": "Scheduled Task/Job", "tactic": "TA0002"},
    
    # Persistence
    "T1098": {"name": "Account Manipulation", "tactic": "TA0003"},
    "T1197": {"name": "BITS Jobs", "tactic": "TA0003"},
    "T1547": {"name": "Boot or Logon Autostart Execution", "tactic": "TA0003"},
    "T1176": {"name": "Browser Extensions", "tactic": "TA0003"},
    
    # Privilege Escalation
    "T1548": {"name": "Abuse Elevation Control Mechanism", "tactic": "TA0004"},
    "T1134": {"name": "Access Token Manipulation", "tactic": "TA0004"},
    "T1068": {"name": "Exploitation for Privilege Escalation", "tactic": "TA0004"},
    "T1574": {"name": "Hijack Execution Flow", "tactic": "TA0004"},
    
    # Defense Evasion
    "T1197": {"name": "BITS Jobs", "tactic": "TA0005"},
    "T1140": {"name": "Deobfuscate/Decode Files or Information", "tactic": "TA0005"},
    "T1070": {"name": "Indicator Removal", "tactic": "TA0005"},
    "T1036": {"name": "Masquerading", "tactic": "TA0005"},
    
    # Credential Access
    "T1110": {"name": "Brute Force", "tactic": "TA0006"},
    "T1555": {"name": "Credentials from Password Stores", "tactic": "TA0006"},
    "T1212": {"name": "Exploitation for Credential Access", "tactic": "TA0006"},
    "T1187": {"name": "Forced Authentication", "tactic": "TA0006"},
    
    # Discovery
    "T1087": {"name": "Account Discovery", "tactic": "TA0007"},
    "T1010": {"name": "Application Window Discovery", "tactic": "TA0007"},
    "T1217": {"name": "Browser Information Discovery", "tactic": "TA0007"},
    "T1580": {"name": "Cloud Infrastructure Discovery", "tactic": "TA0007"},
    
    # Lateral Movement
    "T1210": {"name": "Exploitation of Remote Services", "tactic": "TA0008"},
    "T1534": {"name": "Internal Spearphishing", "tactic": "TA0008"},
    "T1570": {"name": "Lateral Tool Transfer", "tactic": "TA0008"},
    "T1021": {"name": "Remote Services", "tactic": "TA0008"},
    
    # Collection
    "T1560": {"name": "Archive Collected Data", "tactic": "TA0009"},
    "T1123": {"name": "Audio Capture", "tactic": "TA0009"},
    "T1119": {"name": "Automated Collection", "tactic": "TA0009"},
    "T1115": {"name": "Clipboard Data", "tactic": "TA0009"},
    
    # Command and Control
    "T1071": {"name": "Application Layer Protocol", "tactic": "TA0011"},
    "T1092": {"name": "Communication Through Removable Media", "tactic": "TA0011"},
    "T1132": {"name": "Data Encoding", "tactic": "TA0011"},
    "T1001": {"name": "Data Obfuscation", "tactic": "TA0011"},
    
    # Exfiltration
    "T1020": {"name": "Automated Exfiltration", "tactic": "TA0010"},
    "T1030": {"name": "Data Transfer Size Limits", "tactic": "TA0010"},
    "T1048": {"name": "Exfiltration Over Alternative Protocol", "tactic": "TA0010"},
    "T1041": {"name": "Exfiltration Over C2 Channel", "tactic": "TA0010"},
    
    # Impact
    "T1485": {"name": "Data Destruction", "tactic": "TA0040"},
    "T1486": {"name": "Data Encrypted for Impact", "tactic": "TA0040"},
    "T1565": {"name": "Data Manipulation", "tactic": "TA0040"},
    "T1491": {"name": "Defacement", "tactic": "TA0040"},
}

# Common CWE to MITRE Technique mappings
CWE_TECHNIQUE_MAPPINGS = {
    "CWE-79": ["T1189", "T1059"],  # XSS -> Drive-by Compromise, Command and Scripting
    "CWE-89": ["T1190", "T1059"],  # SQL Injection -> Exploit Public-Facing App, Command and Scripting
    "CWE-119": ["T1190", "T1203"],  # Buffer Overflow -> Exploit Public-Facing App, Client Execution
    "CWE-787": ["T1190", "T1203"],  # Out-of-bounds Write -> Exploit Public-Facing App, Client Execution
    "CWE-20": ["T1190", "T1566"],  # Input Validation -> Exploit Public-Facing App, Phishing
    "CWE-200": ["T1212", "T1580"],  # Information Disclosure -> Exploit for Credential Access, Cloud Discovery
    "CWE-352": ["T1189", "T1534"],  # CSRF -> Drive-by Compromise, Internal Spearphishing
    "CWE-125": ["T1190", "T1068"],  # Out-of-bounds Read -> Exploit Public-Facing App, Privilege Escalation
    "CWE-22": ["T1083", "T1570"],  # Path Traversal -> File and Directory Discovery, Lateral Tool Transfer
    "CWE-416": ["T1068", "T1203"],  # Use After Free -> Privilege Escalation, Client Execution
}

# Common Threat Types
THREAT_TYPES = [
    "malware", "ransomware", "trojan", "backdoor", "exploit", 
    "vulnerability", "phishing", "spyware", "adware", "worm"
]

# Common Threat Sources
THREAT_SOURCES = [
    "apt29", "apt28", "lazarus", "fin7", "darkside", 
    "revil", "conti", "lockbit", "blackmatter", "hive"
]
