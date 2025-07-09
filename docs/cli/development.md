# CLI Development Guide

This guide provides detailed information for contributing to the Nixopus CLI development.

## Project Structure

```
cli/
├── main.py              # Main CLI entry point
├── pyproject.toml       # Project configuration
├── commands/            # Command implementations
│   ├── version/         # Version command module
│   ├── test/            # Test command module
│   └── preflight/       # Preflight command module
├── core/                # Core functionality
│   ├── config.py        # Configuration utilities
│   ├── version/         # Version display logic
│   └── test/            # Test functionality
├── utils/               # Utility functions
└── tests/               # Test files
```

## Development Setup

1. **Clone and Install**
   ```bash
   git clone https://github.com/raghavyuva/nixopus.git
   cd nixopus/cli
   make install
   ```

2. **Verify Installation**
   ```bash
   make version
   make test
   ```

3. **Available Commands**
   ```bash
   make help
   ```

## Adding New Commands

### Step 1: Create Command Module

Create a new directory in the `commands/` directory with the following structure:

```python
# commands/new_command/__init__.py
# Empty file to make it a module

# commands/new_command/command.py
import typer
from .messages import new_command_help

new_command_app = typer.Typer(
    help=new_command_help,
    invoke_without_command=True
)

@new_command_app.callback()
def new_command_callback(ctx: typer.Context):
    """Description of the new command"""
    if ctx.invoked_subcommand is None:
        # Main command logic here
        pass

# commands/new_command/messages.py
new_command_help = "Description of the new command"
```

### Step 2: Register Command

Import and register the command in `main.py`:

```python
from commands.new_command.command import new_command_app

app.add_typer(new_command_app, name="new-command")
```

### Step 3: Add Tests

Create corresponding test files in the `tests/` directory:

```python
# tests/test_commands_new_command.py
import pytest
from typer.testing import CliRunner
from cli.main import app

runner = CliRunner()

def test_new_command():
    result = runner.invoke(app, ["new-command"])
    assert result.exit_code == 0
```

### Step 4: Update Documentation

Add the command to the appropriate table in the [Commands Reference](commands.md).

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run tests in watch mode
make test-watch

# Run specific test
poetry run pytest tests/test_commands_version.py

# Run with verbose output
poetry run pytest -v
```

### Test Structure

Tests are organized in the `tests/` directory:

- **Command Tests**: Test individual command functionality
- **Core Tests**: Test core utility functions
- **Integration Tests**: Test command interactions

### Writing Tests

Follow these guidelines:

1. **Test Command Execution**
   ```python
   def test_version_command():
       result = runner.invoke(app, ["version"])
       assert result.exit_code == 0
       assert "Nixopus CLI" in result.stdout
   ```

2. **Test Error Cases**
   ```python
   def test_test_command_development_only():
       result = runner.invoke(app, ["test"])
       assert result.exit_code == 1
       assert "DEVELOPMENT" in result.stdout
   ```

3. **Test Parameters**
   ```python
   def test_test_command_with_target():
       with patch('commands.test.is_development', return_value=True):
           result = runner.invoke(app, ["test", "version"])
           assert result.exit_code == 0
   ```

## Code Standards

### General Guidelines

1. **Follow existing patterns**: Match the structure of existing commands
2. **Keep functions short**: Focus on single responsibility
3. **Use type hints**: Add type annotations where helpful
4. **Follow DRY principles**: Avoid code duplication
5. **Clean code**: Write readable, maintainable code

### Command Guidelines

1. **Use Typer apps**: Structure commands as Typer applications
2. **Separate messages**: Keep command messages in separate files
3. **Descriptive names**: Use clear, action-oriented command names
4. **Help text**: Provide helpful descriptions for all commands
5. **Error handling**: Handle errors gracefully with clear messages
6. **Exit codes**: Return appropriate exit codes (0 for success, 1 for error)

### Documentation Guidelines

1. **Update command docs**: Add new commands to [Commands Reference](commands.md)
2. **Include examples**: Provide usage examples for all commands
3. **Document parameters**: Explain all parameters and options
4. **Specify requirements**: Note any environment or dependency requirements

## Dependencies

### Core Dependencies
- **typer**: Modern CLI framework for Python
- **rich**: Rich text and beautiful formatting in the terminal

### Development Dependencies
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting for pytest

## Environment Configuration

The CLI supports different environments through the `ENV` environment variable:

- `PRODUCTION` (default): Production environment
- `DEVELOPMENT`: Development environment (enables test commands)

Set the environment:
```bash
export ENV=DEVELOPMENT
```

## Contributing Process

1. **Create a branch**
   ```bash
   git checkout -b feature/new-command
   ```

2. **Make changes**
   - Add new command module with proper structure
   - Update main.py to register the command
   - Add tests
   - Update documentation

3. **Run tests**
   ```bash
   make test
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "Add new command: description"
   ```

5. **Submit pull request**

## Makefile Commands

The project includes a Makefile with common development tasks:

```bash
make help          
make install       
make install-dev   
make test          
make test-cov      
make test-watch    
make lint          
make format
make clean
make build         
make publish       
make dev           
make run
```

## Testing Guidelines

- Write tests for all new commands
- Use pytest for testing
- Maintain good test coverage
- Test both success and error scenarios
- Test command help and usage
- Test environment-specific behavior