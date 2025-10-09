#!/usr/bin/env bash
set -euo pipefail

# סקריפט ראשי להרצת כל הבדיקות
# מאגד את כל מערכת הבדיקות יחידה

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RESULTS_DIR="$SCRIPT_DIR/../results"

# צבעים
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_header() { echo -e "${PURPLE}[HEADER]${NC} $1"; }
log_section() { echo -e "${CYAN}[SECTION]${NC} $1"; }

# יצירת תיקיות
mkdir -p "$RESULTS_DIR"

# ספירת בדיקות כוללת
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# פונקציה להרצת בדיקה
run_test_suite() {
    local suite_name="$1"
    local suite_script="$2"
    
    log_section "Running $suite_name..."
    echo "========================================"
    
    if [[ -f "$suite_script" ]]; then
        if bash "$suite_script"; then
            log_success "$suite_name completed successfully"
            return 0
        else
            log_error "$suite_name failed"
            return 1
        fi
    else
        log_error "Test suite script not found: $suite_script"
        return 1
    fi
}

# פונקציה להצגת סיכום
show_summary() {
    echo ""
    echo "📊 Test Suite Summary"
    echo "===================="
    echo "Total Test Suites: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo ""
        log_success "🎉 All test suites passed! System is ready for production."
        return 0
    else
        echo ""
        log_error "❌ Some test suites failed. Please review the errors above."
        return 1
    fi
}

# פונקציה להצגת תוצאות מפורטות
show_detailed_results() {
    echo ""
    echo "📋 Detailed Results"
    echo "==================="
    
    if [[ -d "$RESULTS_DIR" ]]; then
        for result_file in "$RESULTS_DIR"/*.txt; do
            if [[ -f "$result_file" ]]; then
                local filename=$(basename "$result_file" .txt)
                echo ""
                log_info "Results from: $filename"
                echo "----------------------------------------"
                cat "$result_file"
            fi
        done
    else
        log_warning "No detailed results found"
    fi
}

# פונקציה לניקוי קבצי בדיקה
cleanup_test_files() {
    log_info "Cleaning up test files..."
    
    # ניקוי קבצי בדיקה זמניים
    rm -rf "$SCRIPT_DIR/test_data"
    
    # ניקוי קבצי פלט זמניים
    rm -f "$PROJECT_ROOT/complete_companies_data/json/test_*.json"
    rm -f "$PROJECT_ROOT/complete_companies_data/json/test_*.ndjson"
    rm -f "$PROJECT_ROOT/complete_companies_data/csv/test_*.csv"
    rm -f "$PROJECT_ROOT/complete_companies_data/sql/test_*.sql"
    
    # ניקוי קבצי גיבוי
    rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
    
    log_success "Cleanup completed"
}

# פונקציה להצגת עזרה
show_help() {
    echo "🧪 Unit Testing System"
    echo "======================"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --all              Run all test suites (default)"
    echo "  --basic            Run basic functionality tests only"
    echo "  --data-quality     Run data quality validation only"
    echo "  --performance      Run performance tests only"
    echo "  --cleanup          Clean up test files only"
    echo "  --help             Show this help message"
    echo ""
    echo "Test Suites:"
    echo "  Basic Tests        - Core functionality and data integrity"
    echo "  Data Quality       - Data validation and consistency"
    echo "  Performance        - Performance and stability testing"
    echo ""
    echo "Results are saved in: $RESULTS_DIR/"
}

# פונקציה ראשית
main() {
    local run_all=true
    local run_basic=false
    local run_data_quality=false
    local run_performance=false
    local cleanup_only=false
    
    # פרסור ארגומנטים
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                run_all=true
                shift
                ;;
            --basic)
                run_all=false
                run_basic=true
                shift
                ;;
            --data-quality)
                run_all=false
                run_data_quality=true
                shift
                ;;
            --performance)
                run_all=false
                run_performance=true
                shift
                ;;
            --cleanup)
                cleanup_only=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # ניקוי בלבד
    if [[ $cleanup_only == true ]]; then
        cleanup_test_files
        exit 0
    fi
    
    # הצגת כותרת
    log_header "Unit Testing System for Data Fetching"
    echo "Project Root: $PROJECT_ROOT"
    echo "Results Dir: $RESULTS_DIR"
    echo "Timestamp: $(date)"
    echo ""
    
    # הרצת בדיקות בסיסיות
    if [[ $run_all == true ]] || [[ $run_basic == true ]]; then
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        if run_test_suite "Basic Functionality Tests" "$SCRIPT_DIR/test_runner.sh"; then
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        echo ""
    fi
    
    # הרצת בדיקות איכות נתונים
    if [[ $run_all == true ]] || [[ $run_data_quality == true ]]; then
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        if run_test_suite "Data Quality Validation" "$SCRIPT_DIR/data_validator.sh"; then
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        echo ""
    fi
    
    # הרצת בדיקות ביצועים
    if [[ $run_all == true ]] || [[ $run_performance == true ]]; then
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        if run_test_suite "Performance Tests" "$SCRIPT_DIR/performance_test.sh"; then
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        echo ""
    fi
    
    # הצגת סיכום
    show_summary
    local exit_code=$?
    
    # הצגת תוצאות מפורטות
    show_detailed_results
    
    # ניקוי קבצי בדיקה
    cleanup_test_files
    
    exit $exit_code
}

# הרצה אם הסקריפט נקרא ישירות
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
