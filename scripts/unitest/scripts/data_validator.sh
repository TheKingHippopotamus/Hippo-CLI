#!/usr/bin/env bash
set -euo pipefail

# בדיקות ספציפיות לנתונים
# מתמקד בבדיקת איכות הנתונים והתאמה בין מקורות שונים

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RESULTS_DIR="$SCRIPT_DIR/../results"

# צבעים
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# בדיקת איכות נתונים פיננסיים
validate_financial_data() {
    log_info "Validating financial data quality..."
    
    local companies_file="$PROJECT_ROOT/complete_companies_data/json_Map/all_companies_complete.json"
    local issues=0
    
    # בדיקת ערכים שליליים לא הגיוניים
    local negative_revenue=$(jq -r '.[] | select(.aggregations.revenue < 0) | .id' "$companies_file" | wc -l)
    if [[ $negative_revenue -gt 0 ]]; then
        log_warning "Found $negative_revenue companies with negative revenue"
        issues=$((issues + 1))
    fi
    
    # בדיקת ערכים אפסיים לא הגיוניים
    local zero_market_cap=$(jq -r '.[] | select(.aggregations.market_cap == 0) | .id' "$companies_file" | wc -l)
    if [[ $zero_market_cap -gt 0 ]]; then
        log_warning "Found $zero_market_cap companies with zero market cap"
        issues=$((issues + 1))
    fi
    
    # בדיקת יחסים פיננסיים קיצוניים
    local extreme_pe=$(jq -r '.[] | select(.aggregations.pe != null and (.aggregations.pe > 1000 or .aggregations.pe < -1000)) | .id' "$companies_file" | wc -l)
    if [[ $extreme_pe -gt 0 ]]; then
        log_warning "Found $extreme_pe companies with extreme P/E ratios"
        issues=$((issues + 1))
    fi
    
    # בדיקת ROE קיצוני
    local extreme_roe=$(jq -r '.[] | select(.aggregations.roe != null and (.aggregations.roe > 10 or .aggregations.roe < -10)) | .id' "$companies_file" | wc -l)
    if [[ $extreme_roe -gt 0 ]]; then
        log_warning "Found $extreme_roe companies with extreme ROE values"
        issues=$((issues + 1))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log_success "Financial data quality is good"
        return 0
    else
        log_warning "Found $issues financial data quality issues (non-critical)"
        return 0
    fi
}

# בדיקת התאמת מגזרים ותעשיות
validate_sector_industry() {
    log_info "Validating sector and industry data..."
    
    local companies_file="$PROJECT_ROOT/complete_companies_data/json_Map/all_companies_complete.json"
    local issues=0
    
    # בדיקת מגזרים ריקים
    local empty_sectors=$(jq -r '.[] | select(.sector == null or .sector == "") | .id' "$companies_file" | wc -l)
    if [[ $empty_sectors -gt 0 ]]; then
        log_warning "Found $empty_sectors companies with empty sectors"
        issues=$((issues + 1))
    fi
    
    # בדיקת תעשיות ריקות
    local empty_industries=$(jq -r '.[] | select(.industry == null or .industry == "") | .id' "$companies_file" | wc -l)
    if [[ $empty_industries -gt 0 ]]; then
        log_warning "Found $empty_industries companies with empty industries"
        issues=$((issues + 1))
    fi
    
    # בדיקת מגזרים לא סטנדרטיים
    local non_standard_sectors=$(jq -r '.[].sector' "$companies_file" | sort | uniq | grep -v -E '^(technology|healthcare|financials|industrials|consumer|energy|materials|utilities|real estate|communication)$' | wc -l)
    if [[ $non_standard_sectors -gt 0 ]]; then
        log_info "Found $non_standard_sectors non-standard sector names"
    fi
    
    # הצגת פילוח מגזרים
    log_info "Sector distribution:"
    jq -r '.[].sector' "$companies_file" | sort | uniq -c | sort -nr | head -10 | while read count sector; do
        echo "  $sector: $count companies"
    done
    
    if [[ $issues -eq 0 ]]; then
        log_success "Sector and industry data is valid"
        return 0
    else
        log_warning "Found $issues sector/industry issues (non-critical)"
        return 0
    fi
}

# בדיקת איכות תיאורים
validate_descriptions() {
    log_info "Validating company descriptions..."
    
    local companies_file="$PROJECT_ROOT/complete_companies_data/json_Map/all_companies_complete.json"
    local issues=0
    
    # בדיקת תיאורים ריקים
    local empty_descriptions=$(jq -r '.[] | select(.description == null or .description == "") | .id' "$companies_file" | wc -l)
    if [[ $empty_descriptions -gt 0 ]]; then
        log_warning "Found $empty_descriptions companies with empty descriptions"
        issues=$((issues + 1))
    fi
    
    # בדיקת תיאורים קצרים מדי
    local short_descriptions=$(jq -r '.[] | select(.description != null and (.description | length) < 50) | .id' "$companies_file" | wc -l)
    if [[ $short_descriptions -gt 0 ]]; then
        log_warning "Found $short_descriptions companies with very short descriptions"
        issues=$((issues + 1))
    fi
    
    # בדיקת תיאורים ארוכים מדי
    local long_descriptions=$(jq -r '.[] | select(.description != null and (.description | length) > 2000) | .id' "$companies_file" | wc -l)
    if [[ $long_descriptions -gt 0 ]]; then
        log_warning "Found $long_descriptions companies with very long descriptions"
        issues=$((issues + 1))
    fi
    
    # סטטיסטיקות תיאורים
    local avg_length=$(jq -r '.[] | select(.description != null) | .description | length' "$companies_file" | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print 0}')
    log_info "Average description length: ${avg_length%.*} characters"
    
    if [[ $issues -eq 0 ]]; then
        log_success "Description quality is good"
        return 0
    else
        log_warning "Found $issues description quality issues (non-critical)"
        return 0
    fi
}

# בדיקת התאמת טיקרים
validate_ticker_mapping() {
    log_info "Validating ticker mapping accuracy..."
    
    local mapping_file="$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
    local companies_file="$PROJECT_ROOT/complete_companies_data/json_Map/all_companies_complete.json"
    local issues=0
    
    # בדיקת טיקרים חסרים במיפוי
    local missing_tickers=$(jq -r '.[] | select(.ticker == null or .ticker == "") | .id' "$mapping_file" | wc -l)
    if [[ $missing_tickers -gt 0 ]]; then
        log_error "Found $missing_tickers companies with missing tickers in mapping"
        issues=$((issues + 1))
    fi
    
    # בדיקת התאמת טיקרים בין הקבצים
    local ticker_mismatches=0
    while IFS= read -r id; do
        local mapping_ticker=$(jq -r --arg id "$id" '.[] | select(.id == ($id | tonumber)) | .ticker' "$mapping_file")
        local companies_tickers=$(jq -r --arg id "$id" '.[] | select(.id == ($id | tonumber)) | .tickers[0] // empty' "$companies_file")
        
        if [[ "$mapping_ticker" != "$companies_tickers" ]] && [[ -n "$companies_tickers" ]]; then
            ticker_mismatches=$((ticker_mismatches + 1))
            if [[ $ticker_mismatches -le 5 ]]; then
                log_warning "Ticker mismatch for ID $id: mapping='$mapping_ticker', companies='$companies_tickers'"
            fi
        fi
    done < <(jq -r '.[].id' "$mapping_file")
    
    if [[ $ticker_mismatches -gt 0 ]]; then
        log_warning "Found $ticker_mismatches ticker mismatches"
        issues=$((issues + 1))
    fi
    
    # בדיקת פורמט טיקרים
    local invalid_format=$(jq -r '.[].ticker' "$mapping_file" | grep -v '^[A-Z0-9]*$' | wc -l)
    if [[ $invalid_format -gt 0 ]]; then
        log_warning "Found $invalid_format tickers with invalid format"
        issues=$((issues + 1))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log_success "Ticker mapping is accurate"
        return 0
    else
        log_warning "Found $issues ticker mapping issues"
        return 0
    fi
}

# בדיקת שלמות נתונים לאורך זמן
validate_data_completeness() {
    log_info "Validating data completeness over time..."
    
    local companies_file="$PROJECT_ROOT/complete_companies_data/json_Map/all_companies_complete.json"
    local issues=0
    
    # בדיקת נתונים פיננסיים חסרים
    local missing_earnings=$(jq -r '.[] | select(.aggregations.earnings == null) | .id' "$companies_file" | wc -l)
    local missing_revenue=$(jq -r '.[] | select(.aggregations.revenue == null) | .id' "$companies_file" | wc -l)
    local missing_market_cap=$(jq -r '.[] | select(.aggregations.market_cap == null) | .id' "$companies_file" | wc -l)
    
    log_info "Missing financial data:"
    log_info "  Earnings: $missing_earnings companies"
    log_info "  Revenue: $missing_revenue companies"
    log_info "  Market Cap: $missing_market_cap companies"
    
    # בדיקת נתונים בסיסיים חסרים
    local missing_names=$(jq -r '.[] | select(.name == null or .name == "") | .id' "$companies_file" | wc -l)
    local missing_sectors=$(jq -r '.[] | select(.sector == null or .sector == "") | .id' "$companies_file" | wc -l)
    
    if [[ $missing_names -gt 0 ]]; then
        log_error "Found $missing_names companies with missing names"
        issues=$((issues + 1))
    fi
    
    if [[ $missing_sectors -gt 0 ]]; then
        log_warning "Found $missing_sectors companies with missing sectors"
        issues=$((issues + 1))
    fi
    
    # חישוב אחוז השלמות
    local total_companies=$(jq 'length' "$companies_file")
    local complete_companies=$(jq -r '.[] | select(.name != null and .sector != null and .aggregations.earnings != null and .aggregations.revenue != null) | .id' "$companies_file" | wc -l)
    local completeness_percent=$((complete_companies * 100 / total_companies))
    
    log_info "Data completeness: $complete_companies/$total_companies ($completeness_percent%)"
    
    if [[ $completeness_percent -lt 80 ]]; then
        log_warning "Data completeness is below 80%"
        issues=$((issues + 1))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log_success "Data completeness is acceptable"
        return 0
    else
        log_warning "Found $issues data completeness issues"
        return 0
    fi
}

# פונקציה ראשית
main() {
    echo "🔍 Data Quality Validator"
    echo "========================"
    echo ""
    
    validate_financial_data
    echo ""
    validate_sector_industry
    echo ""
    validate_descriptions
    echo ""
    validate_ticker_mapping
    echo ""
    validate_data_completeness
    
    echo ""
    log_success "Data validation completed!"
}

# הרצה אם הסקריפט נקרא ישירות
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
