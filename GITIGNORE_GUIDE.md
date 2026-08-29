# .gitignore Configuration Guide

## Overview

The `.gitignore` file has been updated with comprehensive coverage for the StoreOps FastAPI project. It includes rules for:

- ✅ Python artifacts and packages
- ✅ Virtual environments (multiple types)
- ✅ IDE/Editor files (VS Code, JetBrains, etc.)
- ✅ Environment configuration files
- ✅ Testing and coverage reports
- ✅ Type checking caches
- ✅ Linting and code quality tools
- ✅ Docker configuration overrides
- ✅ Database files
- ✅ Log files
- ✅ OS-specific files
- ✅ Build artifacts
- ✅ CI/CD temporary files

## Key Sections

### 1. Python Files
```
__pycache__/
*.py[cod]
*.egg
*.egg-info/
```
Prevents compiled Python files and package metadata from being tracked.

### 2. Virtual Environments
```
venv/
env/
.venv/
virtualenv/
```
Keeps virtual environment directories out of the repository (they're environment-specific).

### 3. IDE Files
```
.vscode/
.idea/
*.swp
*.swo
```
Excludes editor-specific settings and temporary files that shouldn't be shared.

### 4. Environment Configuration
```
.env
.env.local
.env.*.local
```
Keeps sensitive configuration out of version control. Only commit `.env.example`.

### 5. Testing & Coverage
```
.pytest_cache/
.coverage
htmlcov/
```
Prevents test artifacts from bloating the repository.

### 6. Type Checking & Linting
```
.mypy_cache/
.ruff_cache/
```
Keeps tool cache directories out of version control.

### 7. Docker
```
docker-compose.override.yml
```
Excludes local Docker Compose overrides that shouldn't be shared.

### 8. Logs
```
*.log
logs/
debug.log
```
Prevents runtime logs from being committed.

### 9. Databases
```
*.db
*.sqlite
*.sqlite3
```
Keeps local database files out of the repository.

## Important Notes

### What IS Committed
- ✅ `.env.example` - Template for configuration
- ✅ `.gitkeep` - Placeholder files for empty directories
- ✅ Source code (*.py)
- ✅ Configuration templates
- ✅ Documentation
- ✅ Tests

### What IS NOT Committed
- ❌ `.env` - Actual secrets
- ❌ Virtual environments - Recreate with pip install
- ❌ IDE settings - Each developer configures locally
- ❌ Test artifacts - Regenerate with pytest
- ❌ Cache files - Regenerate automatically
- ❌ Log files - Generated at runtime
- ❌ Database files - Created at runtime

## For New Developers

When cloning the repository, you'll need to:

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file from template
cp .env.example .env
# Edit .env with your local settings
```

## Verification

To verify the .gitignore is working correctly:

```bash
# Show all files that would be committed (not ignored)
git status

# Show ignored files
git check-ignore -v <filename>

# Test if a file would be ignored
git status --ignored
```

## Modifying .gitignore

If you need to add new patterns:

1. Add them to the appropriate section
2. Use comments to explain why
3. Test with `git status` to verify
4. Commit the change

### Examples

**To ignore a new Python package structure:**
```
# MyPackage
src/mypackage/__pycache__/
src/mypackage/*.egg-info/
```

**To ignore a new IDE:**
```
# Sublime Text
*.sublime-project
*.sublime-workspace
```

**To ignore a new log pattern:**
```
# Application logs
logs/application_*.log
app_logs/
```

## Recommended .env.example

The `.env.example` file should be committed to show what environment variables are needed:

```bash
# Application
APP_NAME=StoreOps API
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/storeops

# API
API_PORT=8000
API_HOST=0.0.0.0

# JWT (for future auth)
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

## Best Practices

1. **Use negation carefully** - Only use `!` when you want to exclude something from an ignore pattern
2. **Keep it organized** - Group related patterns with comments
3. **Be specific** - Use full paths when possible to avoid accidents
4. **Review regularly** - Update as the project evolves
5. **Document changes** - Add comments explaining unusual patterns

## CI/CD Considerations

The `.gitignore` is designed to work well with CI/CD:

- ✅ Won't commit secrets in `.env`
- ✅ Test artifacts won't clutter history
- ✅ Build artifacts are properly excluded
- ✅ Dependencies are installed fresh from `requirements.txt`

## Troubleshooting

**"File is committed but I want to ignore it"**
```bash
git rm --cached <filename>
git commit -m "Stop tracking <filename>"
```

**"File should be ignored but it's showing as modified"**
```bash
# Clear git cache
git rm -r --cached .

# Re-add everything (now respecting updated .gitignore)
git add .
```

**"I need to temporarily commit something that's ignored"**
```bash
# Force add an ignored file
git add -f <filename>
```

---

**Last Updated**: 2024-12-14
**Status**: Production Ready ✅
