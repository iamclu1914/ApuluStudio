#!/bin/bash

# =============================================================================
# Apulu Suite Quality Team Runner
# =============================================================================
# Runs all quality checks locally, coordinating the 4 specialist agents:
#   1. Test Suites Agent (--persona-qa)
#   2. Code Review Agent (--persona-refactorer)
#   3. Documentation Agent (--persona-scribe)
#   4. Security Review Agent (--persona-security)
#
# Usage:
#   ./scripts/run-quality-team.sh [options]
#
# Options:
#   --quick         Run quick checks only (lint, type check)
#   --full          Run full quality audit (all checks)
#   --backend       Run backend checks only
#   --frontend      Run frontend checks only
#   --security      Run security checks only
#   --tests         Run tests only
#   --fix           Auto-fix issues where possible
#   --report        Generate unified quality report
#   --ci            CI mode (stricter, no fixes)
#   --help          Show this help message
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$PROJECT_ROOT/quality-reports"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
REPORT_FILE="$REPORTS_DIR/quality-report-$TIMESTAMP.md"

# Default options
QUICK_MODE=false
FULL_MODE=false
BACKEND_ONLY=false
FRONTEND_ONLY=false
SECURITY_ONLY=false
TESTS_ONLY=false
AUTO_FIX=false
GENERATE_REPORT=false
CI_MODE=false

# Counters
TOTAL_ERRORS=0
TOTAL_WARNINGS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${CYAN}━━━ $1 ━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED_CHECKS++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED_CHECKS++))
    ((TOTAL_ERRORS++))
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    ((TOTAL_WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_warning "$1 is not installed. Skipping related checks."
        return 1
    fi
    return 0
}

# =============================================================================
# Parse Arguments
# =============================================================================

show_help() {
    echo "Apulu Suite Quality Team Runner"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --quick         Run quick checks only (lint, type check)"
    echo "  --full          Run full quality audit (all checks)"
    echo "  --backend       Run backend checks only"
    echo "  --frontend      Run frontend checks only"
    echo "  --security      Run security checks only"
    echo "  --tests         Run tests only"
    echo "  --fix           Auto-fix issues where possible"
    echo "  --report        Generate unified quality report"
    echo "  --ci            CI mode (stricter, no fixes)"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --quick              # Quick lint and type checks"
    echo "  $0 --full --report      # Full audit with report"
    echo "  $0 --backend --fix      # Backend checks with auto-fix"
    echo "  $0 --security           # Security scan only"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --full)
            FULL_MODE=true
            shift
            ;;
        --backend)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend)
            FRONTEND_ONLY=true
            shift
            ;;
        --security)
            SECURITY_ONLY=true
            shift
            ;;
        --tests)
            TESTS_ONLY=true
            shift
            ;;
        --fix)
            AUTO_FIX=true
            shift
            ;;
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        --ci)
            CI_MODE=true
            AUTO_FIX=false
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Default to quick mode if no specific mode selected
if ! $FULL_MODE && ! $BACKEND_ONLY && ! $FRONTEND_ONLY && ! $SECURITY_ONLY && ! $TESTS_ONLY; then
    QUICK_MODE=true
fi

# =============================================================================
# Setup
# =============================================================================

print_header "APULU SUITE QUALITY TEAM"

echo -e "Project Root: ${BLUE}$PROJECT_ROOT${NC}"
echo -e "Reports Dir:  ${BLUE}$REPORTS_DIR${NC}"
echo -e "Timestamp:    ${BLUE}$TIMESTAMP${NC}"
echo ""

# Ensure reports directory exists
mkdir -p "$REPORTS_DIR"

# Change to project root
cd "$PROJECT_ROOT"

# =============================================================================
# Backend Checks (Code Review + Test Suites + Security Agents)
# =============================================================================

run_backend_checks() {
    if $FRONTEND_ONLY || $SECURITY_ONLY; then
        return
    fi

    print_header "BACKEND QUALITY CHECKS"

    # Check if backend directory exists
    if [ ! -d "backend" ]; then
        print_error "Backend directory not found"
        return
    fi

    cd "$PROJECT_ROOT/backend"

    # Activate virtual environment if exists
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    fi

    # ----- Linting (Code Review Agent) -----
    print_section "Linting (Ruff)"

    if check_command ruff; then
        if $AUTO_FIX; then
            ruff check . --fix && print_success "Ruff linting passed (with fixes)" || print_error "Ruff linting failed"
            ruff format . && print_success "Ruff formatting applied" || print_error "Ruff formatting failed"
        else
            ruff check . && print_success "Ruff linting passed" || print_error "Ruff linting failed"
            ruff format --check . && print_success "Ruff format check passed" || print_warning "Format issues found (run with --fix)"
        fi
    fi

    # ----- Type Checking (Code Review Agent) -----
    print_section "Type Checking (MyPy)"

    if check_command mypy; then
        mypy app --ignore-missing-imports --no-error-summary 2>/dev/null && print_success "MyPy type check passed" || print_warning "MyPy found type issues"
    fi

    # ----- Tests (Test Suites Agent) -----
    if ! $QUICK_MODE || $TESTS_ONLY || $FULL_MODE; then
        print_section "Running Tests (pytest)"

        if check_command pytest; then
            pytest -v --asyncio-mode=auto \
                --cov=app \
                --cov-report=term-missing \
                --cov-report=xml:"$REPORTS_DIR/backend-coverage.xml" \
                --junitxml="$REPORTS_DIR/backend-pytest-results.xml" \
                2>/dev/null && print_success "Backend tests passed" || print_error "Backend tests failed"
        fi
    fi

    # ----- Security Scan (Security Agent) -----
    if ! $QUICK_MODE || $SECURITY_ONLY || $FULL_MODE; then
        print_section "Security Scan (Bandit)"

        if check_command bandit; then
            bandit -r app -ll -ii -f txt > "$REPORTS_DIR/backend-bandit.txt" 2>/dev/null
            if [ $? -eq 0 ]; then
                print_success "Bandit security scan passed"
            else
                print_warning "Bandit found security issues (see $REPORTS_DIR/backend-bandit.txt)"
            fi
        fi

        print_section "Dependency Audit (pip-audit)"

        if check_command pip-audit; then
            pip-audit --format json --output "$REPORTS_DIR/backend-pip-audit.json" 2>/dev/null
            if [ $? -eq 0 ]; then
                print_success "pip-audit passed - no vulnerabilities"
            else
                print_warning "pip-audit found vulnerabilities (see $REPORTS_DIR/backend-pip-audit.json)"
            fi
        fi
    fi

    # ----- Code Complexity (Code Review Agent) -----
    if $FULL_MODE; then
        print_section "Code Complexity Analysis (radon)"

        if check_command radon; then
            radon cc app -a -s > "$REPORTS_DIR/backend-complexity.txt"
            print_info "Complexity report: $REPORTS_DIR/backend-complexity.txt"
            radon mi app -s > "$REPORTS_DIR/backend-maintainability.txt"
            print_info "Maintainability report: $REPORTS_DIR/backend-maintainability.txt"
        fi
    fi

    cd "$PROJECT_ROOT"
}

# =============================================================================
# Frontend Checks (Code Review + Test Suites Agents)
# =============================================================================

run_frontend_checks() {
    if $BACKEND_ONLY || $SECURITY_ONLY; then
        return
    fi

    print_header "FRONTEND QUALITY CHECKS"

    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found"
        return
    fi

    cd "$PROJECT_ROOT/frontend"

    # Check for node_modules
    if [ ! -d "node_modules" ]; then
        print_info "Installing npm dependencies..."
        npm ci
    fi

    # ----- Linting (Code Review Agent) -----
    print_section "Linting (ESLint)"

    npm run lint 2>/dev/null && print_success "ESLint passed" || print_error "ESLint found issues"

    # ----- Type Checking (Code Review Agent) -----
    print_section "Type Checking (TypeScript)"

    npx tsc --noEmit 2>/dev/null && print_success "TypeScript check passed" || print_error "TypeScript errors found"

    # ----- Build Test (Code Review Agent) -----
    if ! $QUICK_MODE || $FULL_MODE; then
        print_section "Build Test"

        NEXT_PUBLIC_API_URL=http://localhost:8000/api npm run build 2>/dev/null && print_success "Production build succeeded" || print_error "Build failed"
    fi

    # ----- Security Audit (Security Agent) -----
    if ! $QUICK_MODE || $SECURITY_ONLY || $FULL_MODE; then
        print_section "Security Audit (npm audit)"

        npm audit --json > "$REPORTS_DIR/frontend-npm-audit.json" 2>/dev/null
        if npm audit --audit-level=high 2>/dev/null; then
            print_success "npm audit passed"
        else
            print_warning "npm audit found vulnerabilities (see $REPORTS_DIR/frontend-npm-audit.json)"
        fi
    fi

    cd "$PROJECT_ROOT"
}

# =============================================================================
# Security-Only Checks
# =============================================================================

run_security_checks() {
    if ! $SECURITY_ONLY; then
        return
    fi

    print_header "SECURITY REVIEW"

    # ----- Secrets Detection -----
    print_section "Secrets Detection"

    if check_command detect-secrets; then
        detect-secrets scan --all-files > "$REPORTS_DIR/secrets-scan.json" 2>/dev/null
        if [ $? -eq 0 ]; then
            print_success "No secrets detected"
        else
            print_error "Potential secrets found (see $REPORTS_DIR/secrets-scan.json)"
        fi
    fi

    # ----- Check for common security issues -----
    print_section "Security File Checks"

    # Check for .env files
    if [ -f ".env" ]; then
        print_warning ".env file found in repository root"
    else
        print_success "No .env file in repository root"
    fi

    # Check for exposed credentials in common locations
    if grep -r "password\s*=" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | grep -v "node_modules" | grep -v "venv" | head -5; then
        print_warning "Potential hardcoded passwords found"
    else
        print_success "No obvious hardcoded passwords detected"
    fi
}

# =============================================================================
# Generate Report (Coordinator Agent)
# =============================================================================

generate_report() {
    if ! $GENERATE_REPORT; then
        return
    fi

    print_header "GENERATING QUALITY REPORT"

    # Create report from template
    cp "$REPORTS_DIR/REPORT_TEMPLATE.md" "$REPORT_FILE"

    # Replace placeholders with actual values
    sed -i "s/{{TIMESTAMP}}/$TIMESTAMP/g" "$REPORT_FILE"
    sed -i "s/{{RUN_ID}}/local-$TIMESTAMP/g" "$REPORT_FILE"
    sed -i "s/{{QUALITY_SCORE}}/$((100 - TOTAL_ERRORS * 5 - TOTAL_WARNINGS))/g" "$REPORT_FILE"
    sed -i "s/{{GATE_STATUS}}/$([[ $FAILED_CHECKS -eq 0 ]] && echo 'PASSED' || echo 'FAILED')/g" "$REPORT_FILE"

    print_success "Report generated: $REPORT_FILE"
}

# =============================================================================
# Summary
# =============================================================================

print_summary() {
    print_header "QUALITY TEAM SUMMARY"

    echo -e "Checks Passed:  ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "Checks Failed:  ${RED}$FAILED_CHECKS${NC}"
    echo -e "Total Errors:   ${RED}$TOTAL_ERRORS${NC}"
    echo -e "Total Warnings: ${YELLOW}$TOTAL_WARNINGS${NC}"
    echo ""

    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║     QUALITY GATE: PASSED               ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
        exit 0
    else
        echo -e "${RED}╔════════════════════════════════════════╗${NC}"
        echo -e "${RED}║     QUALITY GATE: FAILED               ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════╝${NC}"
        echo ""
        echo "Run with --fix to auto-fix issues where possible."

        if $CI_MODE; then
            exit 1
        else
            exit 0
        fi
    fi
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    run_backend_checks
    run_frontend_checks
    run_security_checks
    generate_report
    print_summary
}

main
