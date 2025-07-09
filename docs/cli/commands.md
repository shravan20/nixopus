# CLI Commands Reference

This guide provides detailed documentation for all available Nixopus CLI commands.

## Command Overview

The Nixopus CLI provides essential commands for managing your Nixopus deployments:

| Command | Description | Usage |
|---------|-------------|-------|
| `version` | Display CLI version | `nixopus version` |
| `test` | Run CLI tests | `nixopus test [target]` |
| `preflight` | Run system readiness checks | `nixopus preflight check` |

## Core Commands

Core commands provide essential functionality for the CLI.

### `version`

Display the current version of the Nixopus CLI.

**Usage:**
```bash
nixopus version
nixopus --version
nixopus -v
```

**Options:**
- `-v, --version`: Show version information and exit

**Example Output:**
```
┌───────────────── Version Info ─────────────────┐
│ Nixopus CLI v0.1.0                            │
└─────────────────────────────────────────────────┘
```

**Aliases:** `-v`, `--version`

**Description:**
The version command displays the current version of the Nixopus CLI using rich formatting. The version information is retrieved from the package metadata and displayed in a styled panel.

---

### `preflight`

Run system readiness checks to ensure the environment is properly configured for Nixopus self-hosting.

**Usage:**
```bash
nixopus preflight check
```

**Subcommands:**
- `check`: Run all preflight checks

**Description:**
The preflight command performs system checks to ensure your environment is ready for Nixopus self-hosting. This includes verifying system requirements, dependencies, and configuration.

**Example Output:**
```
Running preflight checks...
```

---

## Development Commands

Development commands are available only in development environments and help with CLI development and testing.

### `test`

Run tests for the CLI components. This command is only available in development environments.

**Usage:**
```bash
nixopus test [target]
```

**Parameters:**
- `target` (optional): Specific test target (e.g., "version")

**Environment Requirements:**
- Requires `ENV=DEVELOPMENT` environment variable

**Examples:**
```bash
# Run all tests
nixopus test

# Run specific test file
nixopus test version
```

**Description:**
The test command runs the CLI test suite using pytest. It can run all tests or target specific test files. This command is restricted to development environments for security reasons.

**Error Handling:**
- If not in development environment: Shows error message and exits
- If target file doesn't exist: pytest will handle the error

**Output:**
```
Running: venv/bin/python -m pytest tests/version.py
```

---

## Command Help

Get help for any command:

```bash
# General help
nixopus --help

# Command-specific help
nixopus version --help
nixopus test --help
nixopus preflight --help
```

## Command Structure

All CLI commands follow a consistent structure:

1. **Command Name**: Descriptive, action-oriented names
2. **Parameters**: Optional arguments for command customization
3. **Options**: Flags for additional functionality
4. **Environment**: Some commands require specific environment settings

## Error Handling

The CLI provides clear error messages for common issues:

- **Invalid Commands**: Shows help and available commands
- **Missing Parameters**: Displays parameter requirements
- **Environment Errors**: Clear messages about environment requirements
- **Permission Errors**: Guidance on fixing permission issues

## Exit Codes

Commands return appropriate exit codes:

- `0`: Success
- `1`: General error
- `2`: Usage error (invalid arguments)
