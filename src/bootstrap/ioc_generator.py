#!/usr/bin/env python3
"""
IOC Generator
Creates realistic Indicators of Compromise (IOCs) for threat intelligence
"""

import random
import ipaddress
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any

# IOC Types
IOC_TYPES = {
    "ip": {
        "weight": 0.3,
        "subtypes": ["ipv4", "ipv6"],
        "subtype_weights": [0.9, 0.1]
    },
    "domain": {
        "weight": 0.25,
        "subtypes": ["domain", "subdomain", "url"],
        "subtype_weights": [0.4, 0.4, 0.2]
    },
    "file": {
        "weight": 0.35,
        "subtypes": ["md5", "sha1", "sha256", "filename"],
        "subtype_weights": [0.2, 0.2, 0.5, 0.1]
    },
    "email": {
        "weight": 0.1,
        "subtypes": ["address", "subject"],
        "subtype_weights": [0.7, 0.3]
    }
}

# Domain TLDs
TLDS = ["com", "net", "org", "io", "ru", "cn", "tk", "cc", "xyz", "info"]

# Malicious domain words
DOMAIN_WORDS = [
    "secure", "login", "account", "verify", "update", "mail", "cloud", "drive",
    "docs", "service", "support", "help", "admin", "security", "payment", "bank",
    "wallet", "crypto", "block", "chain", "web", "app", "cdn", "api", "download"
]

# Malicious URL paths
URL_PATHS = [
    "/login", "/admin", "/update", "/download", "/setup", "/install", "/verify",
    "/account", "/secure", "/payment", "/wallet", "/auth", "/oauth", "/api/v1",
    "/panel", "/control", "/gate.php", "/config.bin", "/main.php", "/index.php"
]

# File extensions
FILE_EXTENSIONS = [
    ".exe", ".dll", ".ps1", ".vbs", ".js", ".hta", ".bat", ".cmd", ".scr", 
    ".jar", ".py", ".sh", ".php", ".aspx", ".jsp", ".doc", ".xls", ".pdf", ".zip"
]

# Email domains
EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "protonmail.com",
    "mail.ru", "yandex.ru", "aol.com", "icloud.com", "zoho.com"
]

# Email subjects
EMAIL_SUBJECTS = [
    "Your account needs verification", "Payment confirmation", "Security alert",
    "Document shared with you", "Invoice attached", "Password reset", "Login attempt",
    "Your order has shipped", "Urgent: Action required", "Update your information"
]

class IOCGenerator:
    """Generate realistic IOCs for threat intelligence"""
    
    def __init__(self, seed: int = 42):
        """Initialize the generator"""
        random.seed(seed)
        
    def _generate_ipv4(self) -> str:
        """Generate a random IPv4 address"""
        # Generate more realistic malicious IPs
        # Often from specific ranges or countries
        malicious_ranges = [
            "185.0.0.0/8",    # Often used for malicious hosting
            "45.0.0.0/8",     # Common for bulletproof hosting
            "91.0.0.0/8",     # Common for malicious activities
            "103.0.0.0/8",    # APNIC range, often abused
            "194.0.0.0/8",    # RIPE range with many malicious hosts
            "5.188.0.0/16",   # Known malicious subnet
            "23.106.0.0/16",  # Known malicious subnet
        ]
        
        selected_range = random.choice(malicious_ranges)
        network = ipaddress.ip_network(selected_range)
        # Get a random IP from the range
        random_ip = str(network.network_address + random.randint(0, min(65535, network.num_addresses - 1)))
        return random_ip
    
    def _generate_ipv6(self) -> str:
        """Generate a random IPv6 address"""
        # Generate 8 groups of hexadecimal digits
        ipv6_parts = [format(random.randint(0, 65535), 'x').zfill(4) for _ in range(8)]
        return ':'.join(ipv6_parts)
    
    def _generate_domain(self) -> str:
        """Generate a random malicious-looking domain"""
        # Choose 1-3 words for the domain
        word_count = random.choices([1, 2, 3], weights=[0.5, 0.4, 0.1])[0]
        domain_words = random.sample(DOMAIN_WORDS, word_count)
        
        # Sometimes add random digits
        if random.random() < 0.3:
            domain_words.append(str(random.randint(1, 999)))
            
        # Join with hyphens or nothing
        separator = random.choices(["", "-"], weights=[0.7, 0.3])[0]
        domain_name = separator.join(domain_words)
        
        # Add TLD
        tld = random.choice(TLDS)
        
        return f"{domain_name}.{tld}"
    
    def _generate_subdomain(self) -> str:
        """Generate a random subdomain"""
        subdomain = random.choice(["secure", "login", "mail", "update", "api", "cdn", "static", "download"])
        domain = self._generate_domain()
        return f"{subdomain}.{domain}"
    
    def _generate_url(self) -> str:
        """Generate a random malicious URL"""
        # Choose between domain or subdomain
        if random.random() < 0.5:
            host = self._generate_domain()
        else:
            host = self._generate_subdomain()
            
        # Add path
        path = random.choice(URL_PATHS)
        
        # Sometimes add query parameters
        if random.random() < 0.4:
            params = random.choice(["?id=", "?user=", "?token=", "?file=", "?data="])
            param_value = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
            path = f"{path}{params}{param_value}"
            
        # Choose protocol
        protocol = random.choices(["http", "https"], weights=[0.2, 0.8])[0]
        
        return f"{protocol}://{host}{path}"
    
    def _generate_file_hash(self, hash_type: str) -> str:
        """Generate a random file hash"""
        # Create a random string to hash
        random_string = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=32))
        
        if hash_type == "md5":
            return hashlib.md5(random_string.encode(), usedforsecurity=False).hexdigest()  # nosec B324 - demo data only
        elif hash_type == "sha1":
            return hashlib.sha1(random_string.encode(), usedforsecurity=False).hexdigest()  # nosec B303 - demo data only
        elif hash_type == "sha256":
            return hashlib.sha256(random_string.encode()).hexdigest()
        else:
            return hashlib.md5(random_string.encode(), usedforsecurity=False).hexdigest()  # nosec B324 - demo data only
    
    def _generate_filename(self) -> str:
        """Generate a random malicious filename"""
        # Choose base name
        base_names = [
            "setup", "install", "update", "patch", "document", "invoice", "report",
            "scan", "backup", "config", "data", "loader", "downloader", "dropper"
        ]
        base_name = random.choice(base_names)
        
        # Sometimes add random digits
        if random.random() < 0.4:
            base_name = f"{base_name}{random.randint(1, 999)}"
            
        # Add extension
        extension = random.choice(FILE_EXTENSIONS)
        
        return f"{base_name}{extension}"
    
    def _generate_email_address(self) -> str:
        """Generate a random email address"""
        # Generate username
        name_parts = ["admin", "support", "help", "info", "security", "service", "account", "update"]
        username = random.choice(name_parts)
        
        # Sometimes add random digits
        if random.random() < 0.5:
            username = f"{username}{random.randint(1, 999)}"
            
        # Add domain
        domain = random.choice(EMAIL_DOMAINS)
        
        return f"{username}@{domain}"
    
    def _generate_email_subject(self) -> str:
        """Generate a random email subject"""
        return random.choice(EMAIL_SUBJECTS)
    
    def _generate_date(self) -> str:
        """Generate a random date in the past year"""
        days_ago = random.randint(1, 365)  # Up to 1 year ago
        date = datetime.now() - timedelta(days=days_ago)
        return date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def _generate_ioc(self, threat_id: str) -> Dict[str, Any]:
        """Generate a single IOC"""
        # Choose IOC type
        ioc_type = random.choices(
            list(IOC_TYPES.keys()),
            weights=[IOC_TYPES[t]["weight"] for t in IOC_TYPES]
        )[0]
        
        # Choose subtype
        subtype = random.choices(
            IOC_TYPES[ioc_type]["subtypes"],
            weights=IOC_TYPES[ioc_type]["subtype_weights"]
        )[0]
        
        # Generate value based on type/subtype
        value = ""
        if ioc_type == "ip":
            if subtype == "ipv4":
                value = self._generate_ipv4()
            else:
                value = self._generate_ipv6()
        elif ioc_type == "domain":
            if subtype == "domain":
                value = self._generate_domain()
            elif subtype == "subdomain":
                value = self._generate_subdomain()
            else:
                value = self._generate_url()
        elif ioc_type == "file":
            if subtype == "filename":
                value = self._generate_filename()
            else:
                value = self._generate_file_hash(subtype)
        elif ioc_type == "email":
            if subtype == "address":
                value = self._generate_email_address()
            else:
                value = self._generate_email_subject()
        
        # Generate confidence score (0.6 to 1.0)
        confidence = round(0.6 + random.random() * 0.4, 2)
        
        return {
            "value": value,
            "type": f"{ioc_type}.{subtype}",
            "confidence": confidence,
            "firstSeen": self._generate_date(),
            "threatId": threat_id
        }
    
    def generate_iocs_for_threats(self, threats: List[Dict[str, Any]], min_iocs: int = 3, max_iocs: int = 8) -> List[Dict[str, Any]]:
        """Generate IOCs for a list of threats"""
        all_iocs = []
        
        for threat in threats:
            # Generate random number of IOCs for this threat
            num_iocs = random.randint(min_iocs, max_iocs)
            
            for _ in range(num_iocs):
                ioc = self._generate_ioc(threat["id"])
                all_iocs.append(ioc)
        
        return all_iocs

def main():
    """Test the IOC generator"""
    generator = IOCGenerator()
    
    # Create a sample threat
    threat = {"id": "threat-0001", "title": "Test Threat"}
    
    # Generate IOCs
    iocs = generator.generate_iocs_for_threats([threat], min_iocs=5, max_iocs=10)
    
    # Print results
    import json
    print(json.dumps(iocs, indent=2))
    print(f"Generated {len(iocs)} IOCs")

if __name__ == "__main__":
    main()
