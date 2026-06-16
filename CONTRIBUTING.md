# Contributing to ULE

Thank you for your interest in contributing to ULE (Universal Ledger Engine)! 🎉

## Quick Start

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `PYTHONPATH=. .venv/bin/pytest tests/ -v`
5. Commit: `git commit -m "feat: add my feature"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ule.git
cd ule

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
PYTHONPATH=. pytest tests/ -v
```

## Code Style

- Follow PEP 8 conventions
- Use type hints for function signatures
- Add docstrings to all public functions/classes
- Keep functions focused and <50 lines when possible
- Use meaningful variable names

## Testing Requirements

- **All PRs must include tests**
- Maintain or improve code coverage
- Run full test suite before submitting: `PYTHONPATH=. pytest tests/`
- All 304 tests must pass
- No new warnings introduced

### Writing Tests

```python
def test_my_feature():
    """Test description."""
    # Arrange
    db = create_test_db()
    
    # Act
    result = db.my_feature()
    
    # Assert
    assert result is not None
    assert result['status'] == 'success'
```

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Test only
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

**Examples:**
```
feat(iot): add MQTT client for sensor data
fix(nlq): correct Italian language patterns
docs(api): update security examples
test(cdc): add integration tests for offline mode
```

## Pull Request Guidelines

### Before Submitting

- [ ] Tests added/updated and passing
- [ ] Documentation updated if needed
- [ ] No linting warnings/errors
- [ ] Commit messages follow convention
- [ ] PR description explains changes

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new features

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
```

## What We're Looking For

### High Priority
- Additional test coverage
- Performance optimizations
- Bug fixes
- Documentation improvements
- More language patterns for NLQ

### Medium Priority
- New engine plugins
- Additional domain models
- CLI enhancements
- Example scripts

### Future Ideas
- Web UI dashboard
- Docker deployment
- Kubernetes operator
- Cloud provider integrations

## Reporting Bugs

Use GitHub Issues with this template:

```markdown
**Describe the bug**
Clear description

**To Reproduce**
Steps:
1. ...
2. ...
3. ...

**Expected behavior**
What should happen

**Actual behavior**
What actually happens

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.12
- ULE version: 0.1.0a2
```

## Questions?

- Open a [GitHub Discussion](https://github.com/ule-db/ule/discussions)
- Email: sadiqaliali1987@gmail.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
