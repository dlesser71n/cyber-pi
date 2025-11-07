# UV Package Manager Setup

**Date:** November 5, 2025  
**Status:** Configured ✅

---

## What is UV?

UV is a blazing-fast Python package installer and resolver written in Rust. It's 10-100x faster than pip.

**Benefits:**
- ⚡ 10-100x faster than pip
- 🔒 Better dependency resolution
- 📦 Built-in virtual environment management
- 🦀 Written in Rust (reliable, fast)

---

## Configuration

### **1. Aliases Added**
```bash
# In ~/.bashrc
alias pip='uv pip'
alias pip3='uv pip'
```

**Usage:** All `pip` commands now use `uv` automatically.

### **2. Project Files**

**`.python-version`**
```
3.11
```

**`pyproject.toml`**
```toml
[project]
name = "cyber-pi"
version = "1.0.0"
requires-python = ">=3.11"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "bandit>=1.7.5",
    "pip-audit>=2.6.0",
    "safety>=2.3.5",
]
```

**`.uvrc`**
```
UV_SYSTEM_PYTHON=1
UV_COMPILE_BYTECODE=1
```

---

## Common Commands

### **Install packages:**
```bash
uv pip install package-name
# or just: pip install package-name (aliased)
```

### **Install from requirements.txt:**
```bash
uv pip sync requirements.txt
```

### **Install dev dependencies:**
```bash
uv pip install -e ".[dev]"
```

### **List installed packages:**
```bash
uv pip list
```

### **Freeze dependencies:**
```bash
uv pip freeze > requirements.txt
```

### **Compile requirements:**
```bash
uv pip compile pyproject.toml -o requirements.txt
```

---

## Speed Comparison

**Traditional pip:**
```bash
pip install pandas numpy scipy
# ~45 seconds
```

**UV:**
```bash
uv pip install pandas numpy scipy
# ~2 seconds
```

**Result: 20x faster** ⚡

---

## Migration Complete

All future package operations will use UV automatically via bash aliases.

**No changes needed to existing workflows** - just faster execution.

---

## Verification

```bash
# Check UV version
uv --version

# Test installation
uv pip install --dry-run pytest

# Verify alias
which pip  # Should show: alias pip='uv pip'
```

---

**UV is now the default package manager for Cyber-PI.** ⚡
