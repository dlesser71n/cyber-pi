#!/usr/bin/env python3
"""
Cyber Periscope Configuration
Loads settings from .windsurf/config.json and provides logging setup
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any


def load_windsurf_config() -> Dict[str, Any]:
    """Load Windsurf configuration"""
    config_path = Path(__file__).parent.parent.parent / ".windsurf" / "config.json"
    
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    
    # Default config if file doesn't exist
    return {
        "periscope": {
            "logging": {"level": "INFO", "showDetails": False}
        }
    }


def setup_logging():
    """Setup logging based on Windsurf config"""
    config = load_windsurf_config()
    
    # Get logging config
    log_config = config.get("periscope", {}).get("logging", {})
    python_log_config = config.get("python", {}).get("logging", {})
    
    # Determine log level
    level_str = log_config.get("level", "INFO")
    level = getattr(logging, level_str, logging.INFO)
    
    # Create formatter
    log_format = python_log_config.get(
        "format",
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    date_format = python_log_config.get("dateFormat", "%Y-%m-%d %H:%M:%S")
    
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Log configuration loaded
    if log_config.get("showDetails", False):
        root_logger.info("="*70)
        root_logger.info("🧠 Cyber Periscope - Debug Mode Enabled")
        root_logger.info("="*70)
        root_logger.info(f"Log Level: {level_str}")
        root_logger.info(f"Show Details: {log_config.get('showDetails', False)}")
        root_logger.info(f"Show Timestamps: {log_config.get('showTimestamps', True)}")
        root_logger.info(f"Show Source Location: {log_config.get('showSourceLocation', True)}")
        root_logger.info(f"Verbose Logging: {config.get('cascade', {}).get('memory', {}).get('verboseLogging', False)}")
        root_logger.info("="*70)
    
    return config


# Global config
CONFIG = load_windsurf_config()


def get_config() -> Dict[str, Any]:
    """Get current configuration"""
    return CONFIG


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return CONFIG.get("development", {}).get("mode") == "debug"


def is_verbose() -> bool:
    """Check if verbose logging is enabled"""
    return CONFIG.get("periscope", {}).get("memory", {}).get("verboseLogging", False)


def should_show_metrics() -> bool:
    """Check if metrics should be shown"""
    return CONFIG.get("periscope", {}).get("memory", {}).get("showMetrics", True)


def should_show_promotions() -> bool:
    """Check if promotions should be logged"""
    return CONFIG.get("periscope", {}).get("memory", {}).get("showPromotions", True)


def should_track_performance() -> bool:
    """Check if performance tracking is enabled"""
    return CONFIG.get("periscope", {}).get("performance", {}).get("trackOperationTimes", True)


# Setup logging on import
setup_logging()
