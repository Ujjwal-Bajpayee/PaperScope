#!/bin/bash
# Validation script for PR preview deployment setup
# This script checks that all necessary files are in place

set -e

echo "🔍 Validating PR Preview Deployment Setup..."
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track status
ERRORS=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
    else
        echo -e "${RED}✗${NC} $1 missing"
        ((ERRORS++))
    fi
}

# Function to check file has content
check_file_content() {
    if [ -f "$1" ] && [ -s "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 has content"
    else
        echo -e "${YELLOW}⚠${NC} $1 empty or missing"
        ((WARNINGS++))
    fi
}

# Check workflow files
echo "📋 Checking workflow files..."
check_file ".github/workflows/pr-preview-simple.yml"
check_file ".github/workflows/pr-preview.yml"
check_file ".github/workflows/render-preview.yml"
echo ""

# Check documentation
echo "📚 Checking documentation..."
check_file ".github/PREVIEW_DEPLOYMENTS.md"
check_file ".github/PR_PREVIEW_QUICKSTART.md"
echo ""

# Check Docker files
echo "🐳 Checking Docker configuration..."
check_file "Dockerfile"
check_file ".dockerignore"
check_file "render.yaml"
echo ""

# Check required Python files
echo "🐍 Checking Python files..."
check_file "streamlit_app.py"
check_file "requirements.txt"
check_file "paperscope/__init__.py"
echo ""

# Validate YAML syntax
echo "🔧 Validating YAML syntax..."
if command -v python3 &> /dev/null; then
    python3 << 'EOF'
import yaml
import sys

files = [
    '.github/workflows/pr-preview-simple.yml',
    '.github/workflows/pr-preview.yml',
    '.github/workflows/render-preview.yml',
    'render.yaml'
]

errors = 0
for f in files:
    try:
        with open(f) as file:
            yaml.safe_load(file)
        print(f"✓ {f} - valid YAML")
    except Exception as e:
        print(f"✗ {f} - invalid YAML: {e}")
        errors += 1

sys.exit(errors)
EOF
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All YAML files are valid"
    else
        echo -e "${RED}✗${NC} Some YAML files have errors"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Python3 not found, skipping YAML validation"
    ((WARNINGS++))
fi
echo ""

# Check if in git repo
echo "📦 Checking git repository..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Git repository detected"
    
    # Check if workflows are tracked
    if git ls-files .github/workflows/*.yml > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Workflow files are tracked by git"
    else
        echo -e "${YELLOW}⚠${NC} Workflow files not yet committed"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Not a git repository"
    ((WARNINGS++))
fi
echo ""

# Test demo config creation
echo "⚙️  Testing demo config creation..."
mkdir -p paperscope
cat > paperscope/config_test.py << 'EOF'
API_KEY = "demo_key"
MODEL = "gemini-pro"
DB_PATH = "db.json"
EOF

if [ -f "paperscope/config_test.py" ]; then
    echo -e "${GREEN}✓${NC} Demo config can be created"
    rm paperscope/config_test.py
else
    echo -e "${RED}✗${NC} Failed to create demo config"
    ((ERRORS++))
fi
echo ""

# Check if GitHub CLI is available
echo "🔌 Checking deployment tools..."
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✓${NC} GitHub CLI (gh) is installed"
else
    echo -e "${YELLOW}⚠${NC} GitHub CLI (gh) not found - optional for secret management"
    ((WARNINGS++))
fi

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed"
else
    echo -e "${YELLOW}⚠${NC} Docker not found - needed for local testing"
    ((WARNINGS++))
fi
echo ""

# Summary
echo "════════════════════════════════════════"
echo "📊 Validation Summary"
echo "════════════════════════════════════════"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Your PR preview setup is ready to use."
    echo "See .github/PR_PREVIEW_QUICKSTART.md for next steps."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Validation completed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Setup is functional but some optional components are missing."
    echo "See .github/PREVIEW_DEPLOYMENTS.md for details."
    exit 0
else
    echo -e "${RED}✗ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before using PR previews."
    exit 1
fi
