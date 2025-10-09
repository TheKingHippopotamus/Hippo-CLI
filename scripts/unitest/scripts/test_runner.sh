#!/usr/bin/env bash
set -euo pipefail

# מערכת בדיקות יחידה למשיכת מידע
# מבצעת בדיקות ברמה גבוהה על שלמות המידע

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RESULTS_DIR="$SCRIPT_DIR/../results"
TEST_DATA_DIR="$SCRIPT_DIR/../test_data"

# צבעים לפלט
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# יצירת תיקיות
mkdir -p "$RESULTS_DIR" "$TEST_DATA_DIR"

# פונקציות עזר
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ספירת בדיקות
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_name="$1"
    local test_function="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "Running test: $test_name"
    
    if $test_function; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        log_success "✓ $test_name passed"
        return 0
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        log_error "✗ $test_name failed"
        return 1
    fi
}

# בדיקת מבנה קבצי הקלט
test_input_files_structure() {
    log_info "Checking input files structure..."
    
    # בדיקת קובץ המיפוי
    if [[ ! -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json" ]]; then
        log_error "ticker_mapping.json not found"
        return 1
    fi
    
    # בדיקת קובץ החברות המלא
    if [[ ! -f "$PROJECT_ROOT/complete_companies_data/json_Map/all_companies_complete.json" ]]; then
        log_error "all_companies_complete.json not found"
        return 1
    fi
    
    # בדיקת מבנה JSON
    if ! jq empty "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json" 2>/dev/null; then
        log_error "ticker_mapping.json is not valid JSON"
        return 1
    fi
    
    if ! jq empty "$PROJECT_ROOT/complete_companies_data/json_Map/all_companies_complete.json" 2>/dev/null; then
        log_error "all_companies_complete.json is not valid JSON"
        return 1
    fi
    
    log_success "Input files structure is valid"
    return 0
}

# בדיקת שלמות נתוני המיפוי
test_mapping_data_integrity() {
    log_info "Checking mapping data integrity..."
    
    local mapping_file="$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
    
    # בדיקת שדות חובה
    local missing_fields=$(jq -r '.[] | select(.id == null or .name == null or .ticker == null) | .id' "$mapping_file" | wc -l)
    if [[ $missing_fields -gt 0 ]]; then
        log_error "Found $missing_fields records with missing required fields"
        return 1
    fi
    
    # בדיקת כפילויות ID
    local duplicate_ids=$(jq -r '.[].id' "$mapping_file" | sort | uniq -d | wc -l)
    if [[ $duplicate_ids -gt 0 ]]; then
        log_error "Found $duplicate_ids duplicate IDs"
        return 1
    fi
    
    # בדיקת כפילויות טיקרים
    local duplicate_tickers=$(jq -r '.[].ticker' "$mapping_file" | sort | uniq -d | wc -l)
    if [[ $duplicate_tickers -gt 0 ]]; then
        log_error "Found $duplicate_tickers duplicate tickers"
        return 1
    fi
    
    # בדיקת תקינות טיקרים (רק אותיות ומספרים)
    local invalid_tickers=$(jq -r '.[].ticker' "$mapping_file" | grep -v '^[A-Z0-9]*$' | wc -l)
    if [[ $invalid_tickers -gt 0 ]]; then
        log_error "Found $invalid_tickers invalid ticker formats"
        return 1
    fi
    
    log_success "Mapping data integrity is valid"
    return 0
}

# בדיקת נתוני החברות המלאים
test_companies_data_integrity() {
    log_info "Checking companies data integrity..."
    
    local companies_file="$PROJECT_ROOT/complete_companies_data/json_Map/all_companies_complete.json"
    
    # בדיקת שדות חובה
    local missing_names=$(jq -r '.[] | select(.name == null) | .id' "$companies_file" | wc -l)
    if [[ $missing_names -gt 0 ]]; then
        log_error "Found $missing_names records with missing names"
        return 1
    fi
    
    # בדיקת כפילויות ID
    local duplicate_ids=$(jq -r '.[].id' "$companies_file" | sort | uniq -d | wc -l)
    if [[ $duplicate_ids -gt 0 ]]; then
        log_error "Found $duplicate_ids duplicate IDs in companies data"
        return 1
    fi
    
    # בדיקת תקינות נתונים פיננסיים
    local invalid_financials=$(jq -r '.[] | select(.aggregations != null) | .aggregations | to_entries[] | select(.value == null or .value == "") | .key' "$companies_file" | wc -l)
    if [[ $invalid_financials -gt 100 ]]; then
        log_warning "Found $invalid_financials missing financial data points (acceptable)"
    fi
    
    log_success "Companies data integrity is valid"
    return 0
}

# בדיקת התאמה בין קבצי המיפוי והחברות
test_data_consistency() {
    log_info "Checking data consistency between mapping and companies..."
    
    local mapping_file="$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
    local companies_file="$PROJECT_ROOT/complete_companies_data/json_Map/all_companies_complete.json"
    
    # יצירת קובץ זמני לבדיקת התאמה
    local temp_mapping="$TEST_DATA_DIR/temp_mapping.json"
    local temp_companies="$TEST_DATA_DIR/temp_companies.json"
    
    # מיון לפי ID לבדיקה
    jq 'sort_by(.id)' "$mapping_file" > "$temp_mapping"
    jq 'sort_by(.id)' "$companies_file" > "$temp_companies"
    
    # בדיקת התאמת ID - רק עבור ID שקיימים בשני הקבצים
    local common_ids=$(comm -12 <(jq -r '.[].id' "$temp_mapping" | sort) <(jq -r '.[].id' "$temp_companies" | sort))
    local mapping_count=$(jq 'length' "$temp_mapping")
    local companies_count=$(jq 'length' "$temp_companies")
    local common_count=$(echo "$common_ids" | wc -l)
    
    log_info "Mapping file: $mapping_count records"
    log_info "Companies file: $companies_count records"
    log_info "Common IDs: $common_count records"
    
    if [[ $common_count -lt 100 ]]; then
        log_warning "Very few common IDs between files ($common_count), this might indicate different datasets"
        return 0
    fi
    
    # בדיקת התאמת שמות רק עבור ID משותפים
    local mismatched_names=0
    while IFS= read -r id; do
        if [[ -n "$id" ]]; then
            local mapping_name=$(jq -r --arg id "$id" '.[] | select(.id == ($id | tonumber)) | .name' "$temp_mapping")
            local companies_name=$(jq -r --arg id "$id" '.[] | select(.id == ($id | tonumber)) | .name' "$temp_companies")
            
            if [[ "$mapping_name" != "$companies_name" ]]; then
                mismatched_names=$((mismatched_names + 1))
                if [[ $mismatched_names -le 5 ]]; then
                    log_warning "Name mismatch for ID $id: '$mapping_name' vs '$companies_name'"
                fi
            fi
        fi
    done < <(echo "$common_ids")
    
    if [[ $mismatched_names -gt 10 ]]; then
        log_error "Found $mismatched_names name mismatches (threshold: 10)"
        return 1
    fi
    
    # ניקוי קבצים זמניים
    rm -f "$temp_mapping" "$temp_companies"
    
    log_success "Data consistency is valid"
    return 0
}

# בדיקת משיכת מידע מה-API
test_api_data_fetch() {
    log_info "Testing API data fetch..."
    
    # יצירת קובץ בדיקה קטן
    local test_mapping="$TEST_DATA_DIR/test_api_mapping.json"
    cat > "$test_mapping" << 'EOF'
[
  {"id": 1, "name": "Apple Inc", "ticker": "AAPL"},
  {"id": 2, "name": "Microsoft Corporation", "ticker": "MSFT"}
]
EOF
    
    # שמירת הקובץ המקורי
    cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
    cp "$test_mapping" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
    
    # הרצת הסקריפט הראשי
    local output_json="$PROJECT_ROOT/complete_companies_data/json/test_company_details.json"
    local output_jsonl="$PROJECT_ROOT/complete_companies_data/json/test_company_details.ndjson"
    
    mkdir -p "$(dirname "$output_json")"
    
    # שינוי הנתיבים בסקריפט זמנית
    sed "s|company_details_complete.json|test_company_details.json|g; s|company_details.ndjson|test_company_details.ndjson|g" \
        "$PROJECT_ROOT/scripts/get_Data.sh" > "$TEST_DATA_DIR/temp_script.sh"
    
    chmod +x "$TEST_DATA_DIR/temp_script.sh"
    
    if ! bash "$TEST_DATA_DIR/temp_script.sh"; then
        log_error "API fetch script failed"
        # שחזור
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # בדיקת התוצאות
    if [[ ! -f "$output_json" ]]; then
        log_error "Output JSON file not created"
        # שחזור
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # בדיקת מבנה הנתונים
    local records_count=$(jq 'length' "$output_json")
    if [[ $records_count -ne 2 ]]; then
        log_error "Expected 2 records, got $records_count"
        # שחזור
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # בדיקת שדות חובה בתוצאות
    local missing_fields=$(jq -r '.[] | select(.id == null or .name == null or .ticker == null) | .id' "$output_json" | wc -l)
    if [[ $missing_fields -gt 0 ]]; then
        log_error "Found $missing_fields records with missing required fields in API response"
        # שחזור
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # בדיקת התאמת ID
    local api_ids=$(jq -r '.[].id' "$output_json" | sort | tr '\n' ' ' | sed 's/ $//')
    local expected_ids="1 2"
    if [[ "$api_ids" != "$expected_ids" ]]; then
        log_error "ID mismatch in API response: got '$api_ids', expected '$expected_ids'"
        # שחזור
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # שחזור הקובץ המקורי
    cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
    rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
    
    # ניקוי קבצים זמניים
    rm -f "$test_mapping" "$TEST_DATA_DIR/temp_script.sh" "$output_json" "$output_jsonl"
    
    log_success "API data fetch is working correctly"
    return 0
}

# בדיקת המרה ל-CSV
test_csv_conversion() {
    log_info "Testing CSV conversion..."
    
    # יצירת קובץ JSON בדיקה
    local test_json="$TEST_DATA_DIR/test_csv_input.json"
    cat > "$test_json" << 'EOF'
[
  {
    "id": 1,
    "name": "Test Company",
    "ticker": "TEST",
    "sector": "technology",
    "industry": "Software",
    "description": "Test company for validation",
    "exchanges": ["NASDAQ"],
    "indices": ["SP500"],
    "lastUpdated": {"test": "data"},
    "aggregations": {
      "earnings": 1000000,
      "ebit": 1200000,
      "roe": 0.15,
      "roa": 0.10,
      "market_cap": 10000000,
      "revenue": 5000000
    }
  }
]
EOF
    
    # יצירת סקריפט CSV זמני
    local csv_script="$TEST_DATA_DIR/temp_csv_script.sh"
    sed "s|/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/json/company_details_complete.json|$test_json|g; s|/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/csv/company_details.csv|$TEST_DATA_DIR/test_output.csv|g" \
        "$PROJECT_ROOT/scripts/json_to_csv.sh" > "$csv_script"
    
    chmod +x "$csv_script"
    
    if ! bash "$csv_script"; then
        log_error "CSV conversion script failed"
        return 1
    fi
    
    # בדיקת קובץ הפלט
    if [[ ! -f "$TEST_DATA_DIR/test_output.csv" ]]; then
        log_error "CSV output file not created"
        return 1
    fi
    
    # בדיקת מבנה CSV
    local csv_lines=$(wc -l < "$TEST_DATA_DIR/test_output.csv")
    if [[ $csv_lines -ne 2 ]]; then
        log_error "Expected 2 CSV lines (header + data), got $csv_lines"
        return 1
    fi
    
    # בדיקת כותרת
    local header=$(head -1 "$TEST_DATA_DIR/test_output.csv")
    if [[ "$header" != *"id,name,ticker"* ]]; then
        log_error "CSV header is missing required fields"
        return 1
    fi
    
    # בדיקת נתונים
    local data_line=$(tail -1 "$TEST_DATA_DIR/test_output.csv")
    if [[ "$data_line" != *"1,\"Test Company\",\"TEST\""* ]]; then
        log_error "CSV data line is incorrect"
        return 1
    fi
    
    # ניקוי
    rm -f "$test_json" "$csv_script" "$TEST_DATA_DIR/test_output.csv"
    
    log_success "CSV conversion is working correctly"
    return 0
}

# בדיקת המרה ל-SQL
test_sql_conversion() {
    log_info "Testing SQL conversion..."
    
    # יצירת קובץ JSON בדיקה
    local test_json="$TEST_DATA_DIR/test_sql_input.json"
    cat > "$test_json" << 'EOF'
[
  {
    "id": 1,
    "name": "Test Company",
    "ticker": "TEST",
    "sector": "technology",
    "industry": "Software",
    "description": "Test company for validation",
    "exchanges": ["NASDAQ"],
    "indices": ["SP500"],
    "lastUpdated": {"test": "data"},
    "aggregations": {
      "earnings": 1000000,
      "ebit": 1200000,
      "roe": 0.15,
      "roa": 0.10,
      "market_cap": 10000000,
      "revenue": 5000000
    }
  }
]
EOF
    
    # יצירת סקריפט SQL זמני
    local sql_script="$TEST_DATA_DIR/temp_sql_script.sh"
    sed "s|/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/json/company_details_complete.json|$test_json|g; s|/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/sql/company_details.sql|$TEST_DATA_DIR/test_output.sql|g" \
        "$PROJECT_ROOT/scripts/json_to_sql.sh" > "$sql_script"
    
    chmod +x "$sql_script"
    
    if ! bash "$sql_script"; then
        log_error "SQL conversion script failed"
        return 1
    fi
    
    # בדיקת קובץ הפלט
    if [[ ! -f "$TEST_DATA_DIR/test_output.sql" ]]; then
        log_error "SQL output file not created"
        return 1
    fi
    
    # בדיקת מבנה SQL
    if ! grep -q "CREATE TABLE companies" "$TEST_DATA_DIR/test_output.sql"; then
        log_error "SQL file missing CREATE TABLE statement"
        return 1
    fi
    
    if ! grep -q "INSERT INTO companies VALUES" "$TEST_DATA_DIR/test_output.sql"; then
        log_error "SQL file missing INSERT statement"
        return 1
    fi
    
    # בדיקת נתונים
    if ! grep -q "1,\"Test Company\",\"TEST\"" "$TEST_DATA_DIR/test_output.sql"; then
        log_error "SQL data is incorrect"
        return 1
    fi
    
    # ניקוי
    rm -f "$test_json" "$sql_script" "$TEST_DATA_DIR/test_output.sql"
    
    log_success "SQL conversion is working correctly"
    return 0
}

# בדיקת שלמות הנתונים לאורך כל התהליך
test_end_to_end_integrity() {
    log_info "Testing end-to-end data integrity..."
    
    # יצירת קובץ בדיקה עם נתונים מלאים
    local test_mapping="$TEST_DATA_DIR/test_e2e_mapping.json"
    cat > "$test_mapping" << 'EOF'
[
  {"id": 1, "name": "Apple Inc", "ticker": "AAPL"},
  {"id": 2, "name": "Microsoft Corporation", "ticker": "MSFT"},
  {"id": 3, "name": "Amazon.com Inc", "ticker": "AMZN"}
]
EOF
    
    # שמירת הקובץ המקורי
    cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
    cp "$test_mapping" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
    
    # שלב 1: משיכת נתונים מה-API
    local output_json="$PROJECT_ROOT/complete_companies_data/json/test_e2e.json"
    local output_jsonl="$PROJECT_ROOT/complete_companies_data/json/test_e2e.ndjson"
    
    mkdir -p "$(dirname "$output_json")"
    
    sed "s|company_details_complete.json|test_e2e.json|g; s|company_details.ndjson|test_e2e.ndjson|g" \
        "$PROJECT_ROOT/scripts/get_Data.sh" > "$TEST_DATA_DIR/temp_e2e_script.sh"
    
    chmod +x "$TEST_DATA_DIR/temp_e2e_script.sh"
    
    if ! bash "$TEST_DATA_DIR/temp_e2e_script.sh"; then
        log_error "E2E: API fetch failed"
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # שלב 2: המרה ל-CSV
    local csv_output="$TEST_DATA_DIR/test_e2e.csv"
    sed "s|/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/json/company_details_complete.json|$output_json|g; s|/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/csv/company_details.csv|$csv_output|g" \
        "$PROJECT_ROOT/scripts/json_to_csv.sh" > "$TEST_DATA_DIR/temp_csv_e2e.sh"
    
    chmod +x "$TEST_DATA_DIR/temp_csv_e2e.sh"
    
    if ! bash "$TEST_DATA_DIR/temp_csv_e2e.sh"; then
        log_error "E2E: CSV conversion failed"
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # שלב 3: המרה ל-SQL
    local sql_output="$TEST_DATA_DIR/test_e2e.sql"
    sed "s|/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/json/company_details_complete.json|$output_json|g; s|/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/sql/company_details.sql|$sql_output|g" \
        "$PROJECT_ROOT/scripts/json_to_sql.sh" > "$TEST_DATA_DIR/temp_sql_e2e.sh"
    
    chmod +x "$TEST_DATA_DIR/temp_sql_e2e.sh"
    
    if ! bash "$TEST_DATA_DIR/temp_sql_e2e.sh"; then
        log_error "E2E: SQL conversion failed"
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # בדיקת שלמות הנתונים בין כל השלבים
    local json_records=$(jq 'length' "$output_json")
    local csv_records=$(tail -n +2 "$csv_output" | wc -l)
    local sql_records=$(grep -c "INSERT INTO" "$sql_output")
    
    log_info "Record counts: JSON=$json_records, CSV=$csv_records, SQL=$sql_records"
    
    # CSV צריך להיות שווה ל-JSON (כולל כותרת)
    if [[ $json_records -ne $csv_records ]]; then
        log_error "Record count mismatch: JSON=$json_records, CSV=$csv_records"
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # SQL צריך להיות 1 INSERT statement (כל הרשומות בשורה אחת)
    if [[ $sql_records -ne 1 ]]; then
        log_error "SQL INSERT count mismatch: expected 1, got $sql_records"
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # בדיקת התאמת ID בכל השלבים
    local json_ids=$(jq -r '.[].id' "$output_json" | sort | tr '\n' ' ' | sed 's/ $//')
    local csv_ids=$(tail -n +2 "$csv_output" | cut -d',' -f1 | tr -d '"' | sort | tr '\n' ' ' | sed 's/ $//')
    local sql_ids=$(grep "INSERT INTO" "$sql_output" -A 10 | grep -o '([0-9]*,' | tr -d '(,' | sort | tr '\n' ' ' | sed 's/ $//')
    
    log_info "ID comparison: JSON='$json_ids', CSV='$csv_ids', SQL='$sql_ids'"
    
    # בדיקת התאמת ID בין JSON ו-CSV
    if [[ "$json_ids" != "$csv_ids" ]]; then
        log_error "ID mismatch between JSON and CSV formats"
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # בדיקת התאמת ID בין JSON ו-SQL (רק אם יש רשומות ב-SQL)
    if [[ -n "$sql_ids" ]] && [[ "$json_ids" != "$sql_ids" ]]; then
        log_error "ID mismatch between JSON and SQL formats"
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        return 1
    fi
    
    # שחזור הקובץ המקורי
    cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
    rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
    
    # ניקוי קבצים זמניים
    rm -f "$test_mapping" "$TEST_DATA_DIR/temp_e2e_script.sh" "$TEST_DATA_DIR/temp_csv_e2e.sh" "$TEST_DATA_DIR/temp_sql_e2e.sh"
    rm -f "$output_json" "$output_jsonl" "$csv_output" "$sql_output"
    
    log_success "End-to-end data integrity is maintained"
    return 0
}

# פונקציה ראשית
main() {
    echo "🧪 Unit Testing System for Data Fetching"
    echo "========================================"
    echo "Project Root: $PROJECT_ROOT"
    echo "Results Dir: $RESULTS_DIR"
    echo ""
    
    # הרצת כל הבדיקות
    run_test "Input Files Structure" test_input_files_structure
    run_test "Mapping Data Integrity" test_mapping_data_integrity
    run_test "Companies Data Integrity" test_companies_data_integrity
    run_test "Data Consistency" test_data_consistency
    run_test "API Data Fetch" test_api_data_fetch
    run_test "CSV Conversion" test_csv_conversion
    run_test "SQL Conversion" test_sql_conversion
    run_test "End-to-End Integrity" test_end_to_end_integrity
    
    # סיכום תוצאות
    echo ""
    echo "📊 Test Results Summary"
    echo "======================="
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo ""
        log_success "🎉 All tests passed! System is ready for production."
        exit 0
    else
        echo ""
        log_error "❌ Some tests failed. Please review the errors above."
        exit 1
    fi
}

# הרצה אם הסקריפט נקרא ישירות
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
