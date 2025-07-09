# CLI Installation Guide

This guide provides detailed instructions for installing and setting up the Nixopus CLI.

## Prerequisites

Before installing the Nixopus CLI, ensure you have:

- **Python 3.8 or higher**
- **pip** (Python package installer)
- **Git** (for cloning the repository)

### Check Python Version

```bash
python3 --version
```

### Check pip Installation

```bash
pip --version
```

## Installation Methods

### Method 1: Install from Source (Recommended)

1. **Clone the Repository**
   ```bash
   git clone https://github.com/raghavyuva/nixopus.git
   cd nixopus
   ```

2. **Navigate to CLI Directory**
   ```bash
   cd cli
   ```

3. **Install in Development Mode**
   ```bash
   pip install -e .
   ```

### Method 2: Install Dependencies

For development work, install additional dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting

## Verification

After installation, verify the CLI is working:

```bash
nixopus --help

nixopus version
```

Expected output:
```
┌───────────────── Version Info ───────────────── ┐
│ Nixopus CLI version                             │
└─────────────────────────────────────────────────┘
```

## Troubleshooting

### Common Issues

1. **Command Not Found**
   - Ensure you're in the correct directory (`cli/`)
   - Verify Python and pip are properly installed
   - Try reinstalling: `pip install -e .`

2. **Permission Errors**
   - Use `pip install -e . --user` for user installation
   - Or use a virtual environment

3. **Import Errors**
   - Check that all dependencies are installed
   - Verify Python version compatibility

### Virtual Environment (Optional)

For isolated installation:

```bash
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install CLI
pip install -e .
```

## Development Setup

For contributors who want to develop the CLI:

1. **Clone and Install**
   ```bash
   git clone https://github.com/raghavyuva/nixopus.git
   cd nixopus/cli
   pip install -e ".[dev]"
   ```

2. **Run Tests**
   ```bash
   pytest
   ```

3. **Check Coverage**
   ```bash
   pytest --cov=core --cov=utils --cov-report=term-missing
   ```

## Next Steps

After successful installation:

- [Commands Reference](../cli/commands.md) - Learn available commands
- [Development Guide](../cli/development.md) - Contribute to the CLI