# Contributing to LuckApi

Thank you for your interest in contributing to LuckApi! This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- Clear, descriptive title
- Steps to reproduce the bug
- Expected vs actual behavior
- Your environment (OS, Python version, Docker version)
- Screenshots if applicable

### Suggesting Enhancements

- Use a clear, descriptive title
- Explain the suggested change and why it would be useful
- Provide examples of how you would use the feature

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests if available
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone & setup backend
git clone https://github.com/your-username/LuckApi.git
cd LuckApi/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install
```

## Code Style

- **Python**: PEP 8, type hints, docstrings
- **Python**: 4-space indent, 100 char line limit
- **Python**: Use `asyncpg` SQLAlchemy 2.0 syntax
- **Python**: Pydantic v2 with `Field()` constraints
- **Python**: FastAPI best practices
- **Vue**: Element Plus components, Pinia stores

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `chore:` maintenance
- `refactor:` code refactoring
- `perf:` performance improvement

## Questions?

Open an issue with the `question` label or start a Discussion.
