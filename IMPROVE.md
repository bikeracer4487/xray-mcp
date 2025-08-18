# Future Improvements

This document contains a collection of potential future improvements for the Xray MCP server project.

## Toolset Generation Follow-ups

The following enhancements were identified during a recent `/toolset-gen` run:

### 1. Add missing schema blocks
Generate JSON Schema definitions for each tool's input/output parameters directly in the source code using Pydantic models or JSON Schema decorators.

### 2. Create test examples
Generate a comprehensive `examples/` directory with example invocations for each tool showing common use cases.

### 3. Add tool-specific error codes
Document specific error codes for each tool category to help with debugging.

### 4. Generate OpenAPI specification
Create an OpenAPI/Swagger spec from the tool definitions for API documentation.

### 5. Add performance notes
Include performance characteristics and expected response times for each tool.

## Repository Improvement Roadmap

This section outlines recommended improvements for the Xray MCP Server repository based on comprehensive analysis of the current structure, missing components, and development best practices.

### 🎯 Priority 1: Essential Governance Files

#### CODE_OF_CONDUCT.md
**Status**: ❌ Missing  
**Impact**: High - Essential for community standards  
**Action**: Create a comprehensive code of conduct

```markdown
# Recommended content:
- Contributor Covenant 2.1 or similar
- Clear behavioral expectations
- Enforcement guidelines
- Contact information for reporting
```

#### SECURITY.md
**Status**: ❌ Missing  
**Impact**: Critical - Required for security reporting  
**Action**: Implement security policy

```markdown
# Should include:
- Supported versions table
- Security vulnerability reporting process
- Response timeline commitments
- Security update policy
- Contact: security@[domain] or GitHub Security Advisories
```

### 🎯 Priority 2: CI/CD and Automation

#### GitHub Actions Workflows
**Status**: ❌ Missing  
**Impact**: Critical - No automated testing or deployment  
**Action**: Implement comprehensive CI/CD pipeline

##### .github/workflows/ci.yml
```yaml
# Core CI workflow should include:
- Python 3.10, 3.11, 3.12 matrix testing
- Unit and integration test execution
- Coverage reporting (maintain 80% threshold)
- Code quality checks (black, isort, flake8, mypy)
- Security scanning (bandit, safety)
- Documentation build verification
```

##### .github/workflows/release.yml
```yaml
# Release automation should include:
- Semantic versioning
- Automated changelog generation
- PyPI publishing
- GitHub Release creation
- Docker image building (if applicable)
```

#### Pre-commit Hooks
**Status**: ❌ Missing  
**Impact**: High - No automated code quality enforcement  
**Action**: Add .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/psf/black
    hooks: [black]
  - repo: https://github.com/pycqa/isort
    hooks: [isort]
  - repo: https://github.com/pycqa/flake8
    hooks: [flake8]
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks: [mypy]
```

### 🎯 Priority 3: Project Configuration

#### pyproject.toml
**Status**: ❌ Missing  
**Impact**: Medium - Modern Python packaging standard  
**Action**: Migrate from setup.py approach

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]

[project]
name = "xray-mcp"
version = "1.0.0"
dependencies = [...from requirements.txt...]

[tool.black]
line-length = 88
target-version = ['py310', 'py311', 'py312']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.10"
strict = true
```

#### Development Configuration Files
**Status**: ⚠️ Partial  
**Files to add**:
- `.flake8` - Flake8 configuration
- `.coveragerc` - Coverage.py configuration
- `tox.ini` - Multi-environment testing

### 🎯 Priority 4: GitHub Integration

#### Issue Templates (.github/ISSUE_TEMPLATE/)
**Status**: ❌ Missing  
**Action**: Create structured templates

1. **bug_report.md** - Bug reporting template
2. **feature_request.md** - Feature proposal template
3. **config.yml** - Issue template chooser configuration

#### Pull Request Template
**Status**: ❌ Missing  
**Action**: Add .github/pull_request_template.md

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Coverage maintained at 80%+

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
```

#### Dependabot Configuration
**Status**: ❌ Missing  
**Action**: Add .github/dependabot.yml

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

### 🎯 Priority 5: Developer Experience

#### VS Code Configuration (.vscode/)
**Status**: ❌ Missing  
**Action**: Add development environment config

##### settings.json
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```

##### extensions.json
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter"
  ]
}
```

#### EditorConfig
**Status**: ❌ Missing  
**Action**: Add .editorconfig for consistent formatting

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{yml,yaml}]
indent_style = space
indent_size = 2
```

### 🎯 Priority 6: Documentation Enhancements

#### CHANGELOG.md
**Status**: ❌ Missing  
**Impact**: Medium - No version history tracking  
**Action**: Implement Keep a Changelog format

```markdown
# Changelog
All notable changes documented here.

## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security
```

#### ARCHITECTURE.md
**Status**: ❌ Missing  
**Impact**: Low - Would help new contributors  
**Action**: Document system architecture and design decisions

#### API.md
**Status**: ❌ Missing  
**Impact**: Medium - No API reference documentation  
**Action**: Generate from docstrings using Sphinx or similar

### 🎯 Priority 7: Repository Management

#### CODEOWNERS
**Status**: ❌ Missing  
**Action**: Add .github/CODEOWNERS

```
# Global owners
* @dougs-xray-team

# Specific components
/auth/ @security-team
/tools/ @api-team
/tests/ @qa-team
```

#### Branch Protection Rules
**Status**: Unknown - Requires repository settings check  
**Recommended Settings**:
- Require PR reviews (1-2 reviewers)
- Dismiss stale reviews
- Require status checks (CI must pass)
- Require branches to be up to date
- Include administrators
- Restrict force pushes

## 📊 Implementation Roadmap

### Phase 1: Foundation (Week 1)
1. ✅ CONTRIBUTING.md (completed)
2. ✅ TOOLSET.md (completed)
3. ⏳ CODE_OF_CONDUCT.md
4. ⏳ SECURITY.md
5. ⏳ Basic CI workflow

### Phase 2: Automation (Week 2)
1. ⏳ Pre-commit hooks
2. ⏳ Full CI/CD pipeline
3. ⏳ Dependabot configuration
4. ⏳ Release automation

### Phase 3: Developer Experience (Week 3)
1. ⏳ pyproject.toml migration
2. ⏳ VS Code configuration
3. ⏳ EditorConfig
4. ⏳ Development configs (.flake8, .coveragerc)

### Phase 4: GitHub Integration (Week 4)
1. ⏳ Issue templates
2. ⏳ PR template
3. ⏳ CODEOWNERS
4. ⏳ Branch protection rules

### Phase 5: Documentation (Ongoing)
1. ⏳ CHANGELOG.md maintenance
2. ⏳ ARCHITECTURE.md
3. ⏳ API documentation generation
4. ⏳ Example notebooks/tutorials

## 🎯 Quick Wins (Can implement immediately)

1. **Add .gitignore entries**:
   ```
   .coverage
   htmlcov/
   .mypy_cache/
   .pytest_cache/
   .tox/
   *.egg-info/
   dist/
   build/
   ```

2. **Create empty marker files**:
   ```bash
   touch .github/FUNDING.yml
   touch .github/SECURITY.md
   mkdir -p .github/ISSUE_TEMPLATE
   ```

3. **Add badges to README.md**:
   ```markdown
   ![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
   ![License](https://img.shields.io/badge/license-MIT-green)
   ![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)
   ```

## 📈 Success Metrics

After implementing these improvements:

- **Code Quality**: Automated enforcement via pre-commit and CI
- **Security**: Clear reporting channels and scanning
- **Contributor Experience**: Clear guidelines and templates
- **Maintainability**: Automated dependency updates
- **Documentation**: Comprehensive and up-to-date
- **Testing**: Automated with 80%+ coverage maintained
- **Release Process**: Fully automated and versioned

## 📝 README Generation Follow-ups

The following improvements were identified during README.md audit and generation:

### 1. Create example.py file
**Status**: ❌ Missing  
**Impact**: High - README references this for validation  
**Action**: Create a minimal example script demonstrating basic usage

```python
# Should include:
- Basic connection validation
- Simple test creation example
- Query example with JQL
- Error handling demonstration
```

### 2. Create test_server.py wrapper
**Status**: ❌ Missing  
**Impact**: Medium - README references this for testing  
**Action**: Create a test runner script or update README to use pytest directly

### 3. Create dedicated TOOLSET.md
**Status**: ❌ Missing  
**Impact**: High - With 43+ tools, detailed documentation should be separated  
**Action**: Move detailed tool documentation from README to TOOLSET.md

```markdown
# Should include:
- Complete tool catalog with all parameters
- JSON Schema for each tool
- Usage examples for every tool
- Error codes and responses
- Performance characteristics
```

### 4. Add CI/CD workflows
**Status**: ❌ Missing  
**Impact**: Critical - No automated testing  
**Action**: Create .github/workflows/test.yml for automated testing and quality checks

### 5. Create CONTRIBUTING.md
**Status**: ❌ Missing  
**Impact**: High - No clear contribution guidelines  
**Action**: Establish contribution guidelines, commit conventions, and PR process

### 6. Add Makefile
**Status**: ❌ Missing  
**Impact**: Medium - Would improve developer experience  
**Action**: Create simple Makefile with common commands

```makefile
# Should include targets:
- make test
- make format
- make lint
- make coverage
- make install
- make clean
```

### 7. Fix documentation references
**Status**: ⚠️ Incorrect  
**Impact**: Low - Minor corrections needed  
**Action**: Update README to remove references to non-existent files:
- Remove reference to abstractions/ directory
- Update test commands to use pytest
- Correct docs/ structure references

## 🔄 Continuous Improvement

This document should be reviewed quarterly and updated based on:
- Community feedback
- Industry best practices evolution
- Project growth and needs
- Security advisories
- Technology updates

## 📋 CONTRIBUTING.md Generation Follow-ups

The following improvements were identified during the comprehensive contributor guide analysis and generation:

### 1. Essential Governance Files (High Priority)

#### CODE_OF_CONDUCT.md
**Status**: ❌ Missing  
**Impact**: High - Community standards and behavior expectations  
**Action**: Create Contributor Covenant-based code of conduct

```markdown
# Contributor Covenant Code of Conduct

## Our Pledge
We pledge to make participation in our community a harassment-free experience for everyone, 
regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, 
gender identity and expression, level of experience, education, socio-economic status, 
nationality, personal appearance, race, religion, or sexual identity and orientation.

## Our Standards
Examples of behavior that contributes to a positive environment:
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## Enforcement Responsibilities
Community leaders are responsible for clarifying and enforcing our standards of 
acceptable behavior and will take appropriate and fair corrective action in 
response to any behavior that they deem inappropriate, threatening, offensive, or harmful.

## Scope
This Code of Conduct applies within all community spaces, and also applies when 
an individual is officially representing the community in public spaces.

## Enforcement
Instances of abusive, harassing, or otherwise unacceptable behavior may be 
reported to the community leaders responsible for enforcement at [CONTACT_EMAIL].

## Attribution
This Code of Conduct is adapted from the Contributor Covenant, version 2.1.
```

#### SECURITY.md
**Status**: ❌ Missing  
**Impact**: Critical - Security vulnerability reporting process  
**Action**: Implement comprehensive security policy

```markdown
# Security Policy

## Supported Versions
| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | ✅ Yes             |

## Reporting a Vulnerability

**DO NOT** open public GitHub issues for security vulnerabilities.

### For Security Issues:
1. **Email**: Send details to security@[domain] or use GitHub Security Advisories
2. **Include**: 
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

### Response Timeline:
- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Status Update**: Weekly during investigation
- **Resolution**: Target 30 days for critical issues

### Security Update Policy:
- Critical vulnerabilities: Immediate patch release
- High severity: Patch within 1 week
- Medium/Low severity: Next scheduled release

### Disclosure Policy:
We follow coordinated disclosure. We'll work with you to understand and resolve 
the issue before any public disclosure.
```

### 2. GitHub Automation (High Priority)

#### .github/workflows/ci.yml
**Status**: ❌ Missing  
**Impact**: Critical - No automated testing or quality checks  
**Action**: Implement comprehensive CI pipeline

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: python test_server.py
    
    - name: Run pytest with coverage
      run: python -m pytest --cov=. --cov-report=xml --cov-fail-under=80
    
    - name: Code formatting check
      run: black --check .
    
    - name: Import sorting check
      run: isort --check-only .
    
    - name: Linting
      run: flake8 .
    
    - name: Type checking
      run: mypy .
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

#### .pre-commit-config.yaml
**Status**: ❌ Missing  
**Impact**: High - No automated code quality enforcement  
**Action**: Add pre-commit hooks for code quality

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-r", ".", "-f", "json", "-o", "bandit-report.json"]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### 3. Project Configuration (Medium Priority)

#### .github/ISSUE_TEMPLATE/bug_report.md
**Status**: ❌ Missing  
**Action**: Create structured bug report template

```markdown
---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: 'bug'
assignees: ''
---

## 🐛 Bug Description
A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## ✅ Expected Behavior
A clear and concise description of what you expected to happen.

## 🚫 Actual Behavior
A clear and concise description of what actually happened.

## 📱 Environment
- **Python version**: [e.g., 3.12.0]
- **OS**: [e.g., macOS 14.0, Ubuntu 22.04, Windows 11]
- **Xray instance**: [e.g., Cloud, Server/DC v8.5]
- **MCP Client**: [e.g., Claude Desktop, Cursor IDE]

## 🔍 Additional Context
- Error messages or logs
- Screenshots (if applicable)
- Configuration files (remove sensitive data)

## 🔐 API Credentials Note
**NEVER** include real API credentials. Use dummy values like:
```
XRAY_CLIENT_ID=test_client_id
XRAY_CLIENT_SECRET=test_secret
```
```

#### .github/ISSUE_TEMPLATE/feature_request.md
**Status**: ❌ Missing  
**Action**: Create feature request template

```markdown
---
name: Feature request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: 'enhancement'
assignees: ''
---

## 🚀 Feature Description
A clear and concise description of what you want to happen.

## 💡 Motivation
Is your feature request related to a problem? Please describe.
A clear and concise description of what the problem is.

## 🎯 Proposed Solution
Describe the solution you'd like.
A clear and concise description of what you want to happen.

## 🔄 Alternative Solutions
Describe alternatives you've considered.
A clear and concise description of any alternative solutions or features you've considered.

## 🛠️ Implementation Details
- Which MCP tools would be affected?
- Any Xray API endpoints involved?
- Backwards compatibility considerations?

## 📝 Additional Context
Add any other context, screenshots, or examples about the feature request here.
```

#### .github/pull_request_template.md
**Status**: ❌ Missing  
**Action**: Create comprehensive PR template

```markdown
## 📋 Description
Brief description of the changes in this PR.

## 🔄 Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactoring (no functional changes)
- [ ] 🧪 Test improvements

## 🧪 Testing
- [ ] Unit tests pass (`python test_server.py`)
- [ ] Integration tests pass (`python -m pytest tests/`)
- [ ] Coverage maintained at 80%+ (`python -m pytest --cov=.`)
- [ ] Manual testing completed with real Xray instance

## 🔍 Code Quality
- [ ] Code follows project style (`black .`)
- [ ] Imports are sorted (`isort .`)
- [ ] Linting passes (`flake8 .`)
- [ ] Type checking passes (`mypy .`)
- [ ] No security issues (`bandit -r .`)

## 📚 Documentation
- [ ] Updated TOOLSET.md (if adding/modifying tools)
- [ ] Updated README.md (if applicable)
- [ ] Added/updated docstrings
- [ ] Updated CHANGELOG.md

## 🔗 Related Issues
Fixes #(issue number)
Closes #(issue number)
Related to #(issue number)

## 🖼️ Screenshots (if applicable)
Include screenshots of UI changes, console output, or test results.

## 📝 Additional Notes
Any additional information, deployment notes, or context for reviewers.

## ✅ Reviewer Checklist
- [ ] Code review completed
- [ ] Architecture fits project patterns
- [ ] Security considerations reviewed
- [ ] Performance impact assessed
- [ ] Documentation is adequate
```

### 4. Developer Experience (Low Priority)

#### pyproject.toml Migration
**Status**: ❌ Missing - Currently using requirements.txt  
**Action**: Modern Python packaging configuration

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "xray-mcp"
version = "1.0.0"
description = "Model Context Protocol server for Jira Xray test management"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Doug Mason", email = "douglas.mason@example.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.8"
dependencies = [
    "fastmcp>=2.0.0",
    "aiohttp>=3.8.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "PyJWT>=2.8.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "bandit[toml]>=1.7.0",
    "pre-commit>=3.0.0",
]

[project.urls]
Homepage = "https://github.com/dougs-repo/xray-mcp"
Repository = "https://github.com/dougs-repo/xray-mcp.git"
Issues = "https://github.com/dougs-repo/xray-mcp/issues"

[tool.black]
line-length = 88
target-version = ['py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  \.git
  | \.venv
  | \.mypy_cache
  | \.pytest_cache
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-v --strict-markers --tb=short --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=80"
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "unit: Unit tests",
    "integration: Integration tests requiring external services",
    "security: Security-focused tests",
    "slow: Tests that take a long time to run",
]

[tool.coverage.run]
source = ["."]
omit = [
    "tests/*",
    ".venv/*",
    "*/site-packages/*",
    "setup.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]

[tool.bandit]
exclude_dirs = ["tests", ".venv"]
skips = ["B101", "B601"]
```

### 5. Quality and Security Enhancements

#### Additional Configuration Files

##### .editorconfig
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4
max_line_length = 88

[*.{yml,yaml}]
indent_style = space
indent_size = 2

[*.{json,md}]
indent_style = space
indent_size = 2
```

##### .gitattributes
```
# Ensure consistent line endings
* text=auto eol=lf

# Binary files
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.woff binary
*.woff2 binary

# Python files
*.py text eol=lf

# Configuration files
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
*.toml text eol=lf
*.cfg text eol=lf
*.ini text eol=lf

# Documentation
*.md text eol=lf
*.rst text eol=lf
*.txt text eol=lf
```

### 6. Immediate Action Items

#### Quick Implementation Commands
```bash
# 1. Create directory structure
mkdir -p .github/{ISSUE_TEMPLATE,workflows}
mkdir -p .vscode

# 2. Initialize basic files
touch .github/SECURITY.md
touch .github/CODE_OF_CONDUCT.md
touch .github/pull_request_template.md
touch .pre-commit-config.yaml
touch pyproject.toml
touch .editorconfig
touch .gitattributes

# 3. Set up pre-commit (after creating config)
pip install pre-commit
pre-commit install

# 4. Update .gitignore
echo ".coverage" >> .gitignore
echo "htmlcov/" >> .gitignore
echo ".mypy_cache/" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo "bandit-report.json" >> .gitignore
```

### 7. Validation Checklist

After implementing these follow-ups:

- [ ] **All commands verified**: Every command in CONTRIBUTING.md works
- [ ] **File references accurate**: All mentioned files exist
- [ ] **Environment variables correct**: Match actual project requirements
- [ ] **Test commands functional**: pytest.ini configuration works
- [ ] **Quality tools configured**: black, isort, flake8, mypy all function
- [ ] **CI pipeline valid**: GitHub Actions workflow runs successfully
- [ ] **Security policy complete**: Clear reporting and response process
- [ ] **Templates functional**: Issue and PR templates render correctly

---

*Last Updated: 2025-01-14*  
*Next Review: Q2 2025*