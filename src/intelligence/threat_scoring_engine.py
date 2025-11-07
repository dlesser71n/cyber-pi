#!/usr/bin/env python3
"""
Threat Intelligence Scoring Engine
Industry-standard multi-factor threat prioritization following Recorded Future/CrowdStrike methodology
"""

import re
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatSeverity(Enum):
    """Threat severity levels"""
    CRITICAL = "CRITICAL"  # Score 80-100
    HIGH = "HIGH"          # Score 60-79
    MEDIUM = "MEDIUM"      # Score 40-59
    LOW = "LOW"            # Score 20-39
    INFO = "INFO"          # Score 0-19


class ThreatCategory(Enum):
    """Threat categories for classification"""
    ZERO_DAY = "zero_day"
    RANSOMWARE = "ransomware"
    APT = "apt"
    MALWARE = "malware"
    VULNERABILITY = "vulnerability"
    PHISHING = "phishing"
    DATA_BREACH = "data_breach"
    DDoS = "ddos"
    EXPLOIT = "exploit"
    IOC = "ioc"
    GENERAL = "general"


@dataclass
class ThreatScore:
    """Threat scoring result"""
    total_score: float
    severity: ThreatSeverity
    category: ThreatCategory
    factors: Dict[str, float]
    confidence: float
    reasoning: List[str]
    actionable: bool
    priority_rank: int


class ThreatScoringEngine:
    """
    Multi-factor threat intelligence scoring engine
    Implements industry best practices from Recorded Future, CrowdStrike, Mandiant
    """
    
    # CVE/CVSS patterns
    CVE_PATTERN = re.compile(r'CVE-\d{4}-\d{4,7}', re.IGNORECASE)
    CVSS_PATTERN = re.compile(r'CVSS[:\s]+(\d+\.?\d*)', re.IGNORECASE)
    
    # Critical keywords (weighted by importance)
    CRITICAL_KEYWORDS = {
        # Zero-day and active exploitation (highest priority)
        'zero-day': 40, 'zero day': 40, '0-day': 40, '0day': 40,
        'actively exploited': 35, 'in the wild': 35, 'under attack': 35,
        'exploit available': 30, 'exploit released': 30, 'poc released': 30,
        
        # Ransomware (very high priority)
        'ransomware': 30, 'lockbit': 28, 'blackcat': 28, 'alphv': 28,
        'royal': 25, 'play': 25, 'clop': 25, 'akira': 25,
        
        # APT groups (high priority)
        'apt': 25, 'lazarus': 25, 'apt28': 25, 'apt29': 25, 'apt41': 25,
        'fancy bear': 25, 'cozy bear': 25, 'sandworm': 25,
        
        # Critical vulnerabilities
        'remote code execution': 25, 'rce': 25, 'unauthenticated': 25,
        'critical vulnerability': 25, 'authentication bypass': 23,
        'privilege escalation': 20, 'sql injection': 18,
        
        # Data breaches
        'data breach': 22, 'data leak': 22, 'credentials leaked': 22,
        'database exposed': 20, 'ransomware attack': 28,
        
        # Malware
        'trojan': 15, 'backdoor': 18, 'rootkit': 20, 'botnet': 18,
        'cryptominer': 12, 'stealer': 16, 'loader': 14,
        
        # Phishing
        'phishing': 15, 'spear phishing': 18, 'business email compromise': 20,
        'bec': 20, 'credential harvesting': 18,
    }
    
    # Vendor/product importance (affects score multiplier)
    HIGH_VALUE_TARGETS = {
        'microsoft': 1.3, 'windows': 1.3, 'exchange': 1.4, 'office 365': 1.3,
        'vmware': 1.3, 'citrix': 1.3, 'fortinet': 1.3, 'palo alto': 1.3,
        'cisco': 1.3, 'juniper': 1.2, 'apache': 1.2, 'nginx': 1.2,
        'linux': 1.2, 'kubernetes': 1.2, 'docker': 1.2,
        'aws': 1.3, 'azure': 1.3, 'google cloud': 1.3,
        'salesforce': 1.2, 'oracle': 1.2, 'sap': 1.3,
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def score_threat(self, threat: Dict[str, Any]) -> ThreatScore:
        """
        Score a threat using multi-factor analysis
        
        Scoring Factors (industry standard):
        1. Severity Indicators (40%) - CVE scores, critical keywords
        2. Exploit Availability (30%) - Active exploitation, PoC available
        3. Temporal Relevance (20%) - Recency, trending
        4. Source Credibility (10%) - Source reputation
        
        Args:
            threat: Threat intelligence item
            
        Returns:
            ThreatScore with detailed scoring breakdown
        """
        factors = {}
        reasoning = []
        
        # Extract threat data
        title = threat.get('title', '').lower()
        content = threat.get('content', threat.get('description', '')).lower()
        full_text = f"{title} {content}"
        source = threat.get('source', {})
        published = threat.get('published', '')
        
        # Factor 1: Severity Indicators (40%)
        severity_score = self._score_severity(full_text, reasoning)
        factors['severity'] = severity_score * 0.4
        
        # Factor 2: Exploit Availability (30%)
        exploit_score = self._score_exploit_availability(full_text, reasoning)
        factors['exploit'] = exploit_score * 0.3
        
        # Factor 3: Temporal Relevance (20%)
        temporal_score = self._score_temporal_relevance(published, reasoning)
        factors['temporal'] = temporal_score * 0.2
        
        # Factor 4: Source Credibility (10%)
        credibility_score = self._score_source_credibility(source, reasoning)
        factors['credibility'] = credibility_score * 0.1
        
        # Calculate total score
        total_score = sum(factors.values())
        
        # Apply vendor multiplier if high-value target
        multiplier = self._get_vendor_multiplier(full_text)
        if multiplier > 1.0:
            total_score *= multiplier
            reasoning.append(f"High-value target detected (multiplier: {multiplier}x)")
        
        # Cap at 100
        total_score = min(100, total_score)
        
        # Determine severity level
        severity = self._get_severity_level(total_score)
        
        # Categorize threat
        category = self._categorize_threat(full_text)
        
        # Determine if actionable
        actionable = total_score >= 60  # High and Critical only
        
        # Calculate confidence (based on data completeness)
        confidence = self._calculate_confidence(threat, factors)
        
        # Priority rank (for sorting)
        priority_rank = self._calculate_priority_rank(total_score, category, temporal_score)
        
        return ThreatScore(
            total_score=round(total_score, 2),
            severity=severity,
            category=category,
            factors=factors,
            confidence=confidence,
            reasoning=reasoning,
            actionable=actionable,
            priority_rank=priority_rank
        )
    
    def _score_severity(self, text: str, reasoning: List[str]) -> float:
        """Score based on severity indicators (0-100)"""
        score = 0
        
        # Check for CVE and CVSS score
        cve_matches = self.CVE_PATTERN.findall(text)
        if cve_matches:
            score += 20
            reasoning.append(f"CVE identified: {', '.join(cve_matches[:3])}")
        
        cvss_matches = self.CVSS_PATTERN.findall(text)
        if cvss_matches:
            try:
                cvss = float(cvss_matches[0])
                if cvss >= 9.0:
                    score += 40
                    reasoning.append(f"Critical CVSS score: {cvss}")
                elif cvss >= 7.0:
                    score += 30
                    reasoning.append(f"High CVSS score: {cvss}")
                elif cvss >= 4.0:
                    score += 20
                    reasoning.append(f"Medium CVSS score: {cvss}")
            except ValueError:
                pass
        
        # Check for critical keywords
        keyword_score = 0
        found_keywords = []
        for keyword, weight in self.CRITICAL_KEYWORDS.items():
            if keyword in text:
                keyword_score += weight
                found_keywords.append(keyword)
        
        # Cap keyword contribution
        keyword_score = min(60, keyword_score)
        score += keyword_score
        
        if found_keywords:
            reasoning.append(f"Critical keywords: {', '.join(found_keywords[:5])}")
        
        return min(100, score)
    
    def _score_exploit_availability(self, text: str, reasoning: List[str]) -> float:
        """Score based on exploit availability (0-100)"""
        score = 0
        
        exploit_indicators = {
            'actively exploited': 100,
            'in the wild': 100,
            'under active attack': 100,
            'exploit available': 80,
            'exploit released': 80,
            'poc available': 70,
            'poc released': 70,
            'proof of concept': 70,
            'exploit code': 75,
            'metasploit module': 75,
            'weaponized': 90,
        }
        
        for indicator, points in exploit_indicators.items():
            if indicator in text:
                score = max(score, points)
                reasoning.append(f"Exploit status: {indicator}")
                break
        
        return score
    
    def _score_temporal_relevance(self, published: str, reasoning: List[str]) -> float:
        """Score based on recency (0-100)"""
        if not published:
            return 50  # Unknown date = medium score
        
        try:
            # Parse published date
            if isinstance(published, str):
                # Handle various date formats
                pub_date = None
                for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d', '%a, %d %b %Y %H:%M:%S %z']:
                    try:
                        pub_date = datetime.strptime(published[:25], fmt)
                        break
                    except:
                        continue
                
                if not pub_date:
                    return 50
            else:
                pub_date = published
            
            # Make timezone-aware if needed
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            
            # Calculate age
            now = datetime.now(timezone.utc)
            age = now - pub_date
            days_old = age.days
            
            # Score based on age
            if days_old < 1:
                score = 100
                reasoning.append("Published today (maximum urgency)")
            elif days_old < 7:
                score = 90
                reasoning.append(f"Published {days_old} days ago (very recent)")
            elif days_old < 30:
                score = 70
                reasoning.append(f"Published {days_old} days ago (recent)")
            elif days_old < 90:
                score = 50
                reasoning.append(f"Published {days_old} days ago (moderate age)")
            else:
                score = 30
                reasoning.append(f"Published {days_old} days ago (older intelligence)")
            
            return score
            
        except Exception as e:
            self.logger.debug(f"Error parsing date: {e}")
            return 50
    
    def _score_source_credibility(self, source: Dict[str, Any], reasoning: List[str]) -> float:
        """Score based on source credibility (0-100)"""
        credibility = source.get('credibility', 0.7)
        score = credibility * 100
        
        source_name = source.get('name', 'Unknown')
        reasoning.append(f"Source: {source_name} (credibility: {credibility})")
        
        return score
    
    def _get_vendor_multiplier(self, text: str) -> float:
        """Get vendor importance multiplier"""
        max_multiplier = 1.0
        
        for vendor, multiplier in self.HIGH_VALUE_TARGETS.items():
            if vendor in text:
                max_multiplier = max(max_multiplier, multiplier)
        
        return max_multiplier
    
    def _get_severity_level(self, score: float) -> ThreatSeverity:
        """Convert score to severity level"""
        if score >= 80:
            return ThreatSeverity.CRITICAL
        elif score >= 60:
            return ThreatSeverity.HIGH
        elif score >= 40:
            return ThreatSeverity.MEDIUM
        elif score >= 20:
            return ThreatSeverity.LOW
        else:
            return ThreatSeverity.INFO
    
    def _categorize_threat(self, text: str) -> ThreatCategory:
        """Categorize threat type"""
        categories = {
            ThreatCategory.ZERO_DAY: ['zero-day', 'zero day', '0-day', '0day'],
            ThreatCategory.RANSOMWARE: ['ransomware', 'lockbit', 'blackcat', 'alphv', 'royal', 'play', 'clop'],
            ThreatCategory.APT: ['apt', 'apt28', 'apt29', 'apt41', 'lazarus', 'fancy bear', 'cozy bear'],
            ThreatCategory.VULNERABILITY: ['cve-', 'vulnerability', 'cvss'],
            ThreatCategory.EXPLOIT: ['exploit', 'poc', 'proof of concept'],
            ThreatCategory.MALWARE: ['malware', 'trojan', 'backdoor', 'rootkit', 'botnet'],
            ThreatCategory.PHISHING: ['phishing', 'spear phishing', 'bec', 'business email compromise'],
            ThreatCategory.DATA_BREACH: ['data breach', 'data leak', 'credentials leaked'],
            ThreatCategory.DDoS: ['ddos', 'denial of service'],
            ThreatCategory.IOC: ['ioc', 'indicator of compromise', 'hash', 'ip address'],
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return ThreatCategory.GENERAL
    
    def _calculate_confidence(self, threat: Dict[str, Any], factors: Dict[str, float]) -> float:
        """Calculate confidence in the scoring (0-1)"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we have more data
        if threat.get('title'):
            confidence += 0.1
        if threat.get('content') or threat.get('description'):
            confidence += 0.1
        if threat.get('published'):
            confidence += 0.1
        if threat.get('source', {}).get('credibility'):
            confidence += 0.1
        
        # Increase confidence if multiple factors contributed
        contributing_factors = sum(1 for v in factors.values() if v > 0)
        confidence += (contributing_factors / len(factors)) * 0.1
        
        return min(1.0, confidence)
    
    def _calculate_priority_rank(self, score: float, category: ThreatCategory, temporal: float) -> int:
        """Calculate priority rank for sorting (lower = higher priority)"""
        # Base rank from score (inverted)
        rank = int((100 - score) * 100)
        
        # Adjust for category urgency
        category_urgency = {
            ThreatCategory.ZERO_DAY: -5000,
            ThreatCategory.RANSOMWARE: -4000,
            ThreatCategory.APT: -3000,
            ThreatCategory.EXPLOIT: -2000,
            ThreatCategory.VULNERABILITY: -1000,
            ThreatCategory.MALWARE: 0,
            ThreatCategory.DATA_BREACH: -1500,
            ThreatCategory.PHISHING: 500,
            ThreatCategory.DDoS: 1000,
            ThreatCategory.IOC: 2000,
            ThreatCategory.GENERAL: 3000,
        }
        rank += category_urgency.get(category, 0)
        
        # Adjust for recency (newer = higher priority)
        rank += int((100 - temporal) * 10)
        
        return rank


def filter_threats_by_priority(
    threats: List[Dict[str, Any]],
    min_score: float = 60.0,
    max_results: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Filter and prioritize threats using intelligent scoring
    
    Args:
        threats: List of threat intelligence items
        min_score: Minimum score threshold (default: 60 = HIGH/CRITICAL only)
        max_results: Maximum results to return (None = all above threshold)
        
    Returns:
        Filtered and sorted list of threats with scoring metadata
    """
    engine = ThreatScoringEngine()
    
    # Score all threats
    scored_threats = []
    for threat in threats:
        score = engine.score_threat(threat)
        
        # Only include threats above threshold
        if score.total_score >= min_score:
            threat['_scoring'] = {
                'score': score.total_score,
                'severity': score.severity.value,
                'category': score.category.value,
                'factors': score.factors,
                'confidence': score.confidence,
                'reasoning': score.reasoning,
                'actionable': score.actionable,
                'priority_rank': score.priority_rank
            }
            scored_threats.append(threat)
    
    # Sort by priority rank (lower = higher priority)
    scored_threats.sort(key=lambda x: x['_scoring']['priority_rank'])
    
    # Limit results if specified
    if max_results:
        scored_threats = scored_threats[:max_results]
    
    return scored_threats


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    engine = ThreatScoringEngine()
    
    # Test threat
    test_threat = {
        'title': 'Critical Zero-Day in Microsoft Exchange Actively Exploited',
        'content': 'CVE-2025-12345 CVSS 9.8 - Remote code execution vulnerability in Microsoft Exchange Server is being actively exploited in the wild. Exploit code publicly available.',
        'published': datetime.now(timezone.utc).isoformat(),
        'source': {
            'name': 'Microsoft Security Response Center',
            'credibility': 0.95
        }
    }
    
    score = engine.score_threat(test_threat)
    
    print(f"\n{'='*80}")
    print(f"Threat Scoring Example")
    print(f"{'='*80}")
    print(f"Title: {test_threat['title']}")
    print(f"\nScore: {score.total_score}/100")
    print(f"Severity: {score.severity.value}")
    print(f"Category: {score.category.value}")
    print(f"Actionable: {score.actionable}")
    print(f"Confidence: {score.confidence:.2f}")
    print(f"\nFactor Breakdown:")
    for factor, value in score.factors.items():
        print(f"  {factor}: {value:.2f}")
    print(f"\nReasoning:")
    for reason in score.reasoning:
        print(f"  • {reason}")
    print(f"{'='*80}\n")
