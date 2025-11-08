# Windsurf Configuration for Cascade Memory System

This directory contains Windsurf-specific configuration for the Cascade 3-Level Memory System.

## Configuration File

**File:** `.windsurf/config.json`

### Debug Mode Settings

The configuration enables detailed debug output and verbose logging:

```json
{
  "cascade": {
    "logging": {
      "level": "DEBUG",              // Log level: DEBUG, INFO, WARNING, ERROR
      "showDetails": true,           // Show detailed operation info
      "showTimestamps": true,        // Include timestamps in logs
      "showSourceLocation": true,    // Show file:line in logs
      "colorize": true              // Colorize output (if supported)
    },
    "memory": {
      "showMetrics": true,           // Show cache hits/misses
      "showPromotions": true,        // Log tier promotions
      "showCacheHits": true,         // Log cache hit/miss details
      "showDecayOperations": true,   // Log confidence decay operations
      "verboseLogging": true         // Enable verbose memory operations
    },
    "testing": {
      "verboseOutput": true,         // Verbose test output
      "showAllAssertions": true,     // Show all assertion checks
      "printIntermediateResults": true, // Print intermediate test results
      "showTimings": true            // Show operation timings
    },
    "redis": {
      "logCommands": true,           // Log Redis commands
      "showConnectionDetails": true, // Show connection info
      "logKeyOperations": true       // Log key operations (get/set/del)
    },
    "performance": {
      "trackOperationTimes": true,   // Track operation durations
      "showSlowQueries": true,       // Highlight slow operations
      "logMemoryUsage": true         // Log memory usage stats
    }
  }
}
```

## Usage

The configuration is automatically loaded by `src/cascade/config.py` when the module is imported.

### In Your Code

```python
from cascade.config import get_config, is_debug_mode, is_verbose

# Check if debug mode is enabled
if is_debug_mode():
    print("Debug mode active")

# Check if verbose logging is enabled
if is_verbose():
    logger.debug("Detailed operation info...")

# Get full config
config = get_config()
```

### Log Output Format

With debug mode enabled, you'll see detailed logs like:

```
2025-11-03 21:15:30 - cascade.memory - DEBUG - cascade_memory_threat_ops.py:123 - Adding threat: threat_001
2025-11-03 21:15:30 - cascade.memory - DEBUG - cascade_memory_threat_ops.py:145 - Calculated threat score: 0.75
2025-11-03 21:15:30 - cascade.memory - INFO - cascade_memory_threat_ops.py:156 - ✅ Added to Level 1: threat_001
2025-11-03 21:15:31 - cascade.memory - DEBUG - cascade_memory_threat_ops.py:234 - Recording interaction: analyst_1 -> escalate
2025-11-03 21:15:31 - cascade.memory - INFO - cascade_memory_threat_ops.py:245 - ⬆️ Promoted to Level 2: threat_001
```

## Changing Log Level

To change the log level, edit `config.json`:

```json
{
  "cascade": {
    "logging": {
      "level": "INFO"  // Change to: DEBUG, INFO, WARNING, ERROR
    }
  }
}
```

## Disabling Debug Mode

To disable debug mode:

```json
{
  "development": {
    "mode": "production",  // Change from "debug" to "production"
    "verboseErrors": false,
    "showStackTraces": false
  }
}
```

## Performance Impact

Debug mode has minimal performance impact:
- **Log Level DEBUG**: ~5-10% overhead
- **Verbose Logging**: ~2-3% overhead
- **Performance Tracking**: ~1-2% overhead

For production deployments, consider using `INFO` or `WARNING` level.

## Environment-Specific Configs

You can create environment-specific configs:

- `.windsurf/config.json` - Default (development)
- `.windsurf/config.production.json` - Production settings
- `.windsurf/config.test.json` - Testing settings

Load specific config:
```python
import os
config_file = os.getenv('CASCADE_CONFIG', 'config.json')
```

## Troubleshooting

### Logs Not Showing

1. Check log level: `"level": "DEBUG"`
2. Verify config file exists: `.windsurf/config.json`
3. Check if config is loaded: `from cascade.config import CONFIG; print(CONFIG)`

### Too Much Output

Reduce verbosity:
```json
{
  "cascade": {
    "logging": {"level": "INFO"},
    "memory": {"verboseLogging": false}
  }
}
```

### Performance Issues

Disable performance tracking:
```json
{
  "cascade": {
    "performance": {
      "trackOperationTimes": false,
      "logMemoryUsage": false
    }
  }
}
```

## Best Practices

1. **Development**: Use `DEBUG` level with all verbose options
2. **Testing**: Use `INFO` level with test verbosity
3. **Production**: Use `WARNING` or `ERROR` level
4. **Debugging Issues**: Enable specific subsystem logging (redis, memory, etc.)

## Configuration Reference

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `logging.level` | string | "INFO" | Log level (DEBUG/INFO/WARNING/ERROR) |
| `logging.showDetails` | boolean | false | Show detailed operation info |
| `memory.verboseLogging` | boolean | false | Enable verbose memory operations |
| `memory.showMetrics` | boolean | true | Show cache metrics |
| `memory.showPromotions` | boolean | true | Log tier promotions |
| `redis.logCommands` | boolean | false | Log all Redis commands |
| `performance.trackOperationTimes` | boolean | true | Track operation durations |
| `development.mode` | string | "production" | Development mode (debug/production) |

## System Context (NEW!)

**File:** `SYSTEM_CONTEXT.md` (symlink to `~/.claude/CLAUDE.md`)

This file provides persistent system context shared between terminal Claude Code sessions and Windsurf/Cascade:

- **Current Projects**: Active project details, status, GitHub links
- **System Configuration**: MicroK8s, services, resource status  
- **Code Patterns**: Monitoring, async, testing, documentation standards
- **Critical Preferences**: NO DOCKER, use MicroK8s, NGINX Ingress only, uv pip
- **Development Tools**: Python 3.11, GPU setup, toolchain preferences

Cascade can reference this file for context about your system and coding standards.

---

**Created:** November 3, 2025  
**Updated:** November 8, 2025  
**For:** Cascade 3-Level Memory System + System Context  
**Status:** Production-Ready with Debug Support
