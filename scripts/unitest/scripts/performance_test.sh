#!/usr/bin/env bash
set -euo pipefail

# בדיקות ביצועים של המערכת
# בודק זמני ביצוע, שימוש בזיכרון, ואיכות התוצאות

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

# מדידת זמן ביצוע
measure_time() {
    local start_time=$(date +%s.%N)
    "$@"
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)
    echo "$duration"
}

# בדיקת ביצועי משיכת נתונים מה-API
test_api_performance() {
    log_info "Testing API performance..."
    
    # יצירת קובץ בדיקה עם מספר שונה של רשומות
    local test_sizes=(1 5 10 20)
    local results_file="$RESULTS_DIR/api_performance.txt"
    
    echo "API Performance Test Results" > "$results_file"
    echo "============================" >> "$results_file"
    echo "Records | Time (seconds) | Rate (records/sec)" >> "$results_file"
    echo "--------|----------------|-------------------" >> "$results_file"
    
    for size in "${test_sizes[@]}"; do
        log_info "Testing with $size records..."
        
        # יצירת קובץ בדיקה
        local test_mapping="$PROJECT_ROOT/scripts/unitest/test_data/test_${size}_records.json"
        mkdir -p "$(dirname "$test_mapping")"
        
        jq ".[0:$size]" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json" > "$test_mapping"
        
        # שמירת הקובץ המקורי
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        cp "$test_mapping" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        
        # מדידת זמן
        local output_json="$PROJECT_ROOT/complete_companies_data/json/test_perf_${size}.json"
        local output_jsonl="$PROJECT_ROOT/complete_companies_data/json/test_perf_${size}.ndjson"
        
        mkdir -p "$(dirname "$output_json")"
        
        # יצירת סקריפט זמני
        local temp_script="$PROJECT_ROOT/scripts/unitest/test_data/temp_perf_${size}.sh"
        sed "s|company_details_complete.json|test_perf_${size}.json|g; s|company_details.ndjson|test_perf_${size}.ndjson|g" \
            "$PROJECT_ROOT/scripts/get_Data.sh" > "$temp_script"
        
        chmod +x "$temp_script"
        
        local duration=$(measure_time bash "$temp_script")
        local rate=$(echo "scale=2; $size / $duration" | bc)
        
        echo "$size      | $duration        | $rate" >> "$results_file"
        
        # בדיקת איכות התוצאות
        if [[ -f "$output_json" ]]; then
            local actual_records=$(jq 'length' "$output_json")
            if [[ $actual_records -ne $size ]]; then
                log_warning "Expected $size records, got $actual_records"
            fi
        fi
        
        # ניקוי
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$test_mapping" "$temp_script"
        rm -f "$output_json" "$output_jsonl"
    done
    
    log_success "API performance test completed"
    cat "$results_file"
}

# בדיקת ביצועי המרה ל-CSV
test_csv_performance() {
    log_info "Testing CSV conversion performance..."
    
    local test_sizes=(10 50 100 500)
    local results_file="$RESULTS_DIR/csv_performance.txt"
    
    echo "CSV Conversion Performance Test Results" > "$results_file"
    echo "=======================================" >> "$results_file"
    echo "Records | Time (seconds) | Rate (records/sec)" >> "$results_file"
    echo "--------|----------------|-------------------" >> "$results_file"
    
    for size in "${test_sizes[@]}"; do
        log_info "Testing CSV conversion with $size records..."
        
        # יצירת קובץ JSON בדיקה
        local test_json="$PROJECT_ROOT/scripts/unitest/test_data/test_csv_${size}.json"
        mkdir -p "$(dirname "$test_json")"
        
        jq ".[0:$size]" "$PROJECT_ROOT/complete_companies_data/json/company_details_complete.json" > "$test_json" 2>/dev/null || {
            # אם הקובץ לא קיים, ניצור נתונים דמה
            local temp_data=""
            for ((i=1; i<=size; i++)); do
                if [[ $i -gt 1 ]]; then
                    temp_data+=","
                fi
                temp_data+="{\"id\":$i,\"name\":\"Company $i\",\"ticker\":\"TEST$i\",\"sector\":\"technology\",\"industry\":\"Software\",\"description\":\"Test company $i\",\"exchanges\":[\"NASDAQ\"],\"indices\":[\"SP500\"],\"lastUpdated\":{},\"aggregations\":{\"earnings\":1000000,\"ebit\":1200000,\"roe\":0.15,\"roa\":0.10,\"market_cap\":10000000,\"revenue\":5000000}}"
            done
            echo "[$temp_data]" > "$test_json"
        }
        
        # מדידת זמן המרה
        local output_csv="$PROJECT_ROOT/scripts/unitest/test_data/test_csv_output_${size}.csv"
        
        local duration=$(measure_time bash -c "
            sed 's|company_details_complete.json|$test_json|g; s|company_details.csv|$output_csv|g' \
                '$PROJECT_ROOT/scripts/json_to_csv.sh' > '$PROJECT_ROOT/scripts/unitest/test_data/temp_csv_${size}.sh' && \
            chmod +x '$PROJECT_ROOT/scripts/unitest/test_data/temp_csv_${size}.sh' && \
            bash '$PROJECT_ROOT/scripts/unitest/test_data/temp_csv_${size}.sh'
        ")
        
        local rate=$(echo "scale=2; $size / $duration" | bc)
        echo "$size      | $duration        | $rate" >> "$results_file"
        
        # בדיקת איכות התוצאות
        if [[ -f "$output_csv" ]]; then
            local csv_lines=$(wc -l < "$output_csv")
            local expected_lines=$((size + 1))  # +1 for header
            if [[ $csv_lines -ne $expected_lines ]]; then
                log_warning "Expected $expected_lines CSV lines, got $csv_lines"
            fi
        fi
        
        # ניקוי
        rm -f "$test_json" "$output_csv" "$PROJECT_ROOT/scripts/unitest/test_data/temp_csv_${size}.sh"
    done
    
    log_success "CSV performance test completed"
    cat "$results_file"
}

# בדיקת ביצועי המרה ל-SQL
test_sql_performance() {
    log_info "Testing SQL conversion performance..."
    
    local test_sizes=(10 50 100 500)
    local results_file="$RESULTS_DIR/sql_performance.txt"
    
    echo "SQL Conversion Performance Test Results" > "$results_file"
    echo "=======================================" >> "$results_file"
    echo "Records | Time (seconds) | Rate (records/sec)" >> "$results_file"
    echo "--------|----------------|-------------------" >> "$results_file"
    
    for size in "${test_sizes[@]}"; do
        log_info "Testing SQL conversion with $size records..."
        
        # יצירת קובץ JSON בדיקה
        local test_json="$PROJECT_ROOT/scripts/unitest/test_data/test_sql_${size}.json"
        mkdir -p "$(dirname "$test_json")"
        
        jq ".[0:$size]" "$PROJECT_ROOT/complete_companies_data/json/company_details_complete.json" > "$test_json" 2>/dev/null || {
            # אם הקובץ לא קיים, ניצור נתונים דמה
            local temp_data=""
            for ((i=1; i<=size; i++)); do
                if [[ $i -gt 1 ]]; then
                    temp_data+=","
                fi
                temp_data+="{\"id\":$i,\"name\":\"Company $i\",\"ticker\":\"TEST$i\",\"sector\":\"technology\",\"industry\":\"Software\",\"description\":\"Test company $i\",\"exchanges\":[\"NASDAQ\"],\"indices\":[\"SP500\"],\"lastUpdated\":{},\"aggregations\":{\"earnings\":1000000,\"ebit\":1200000,\"roe\":0.15,\"roa\":0.10,\"market_cap\":10000000,\"revenue\":5000000}}"
            done
            echo "[$temp_data]" > "$test_json"
        }
        
        # מדידת זמן המרה
        local output_sql="$PROJECT_ROOT/scripts/unitest/test_data/test_sql_output_${size}.sql"
        
        local duration=$(measure_time bash -c "
            sed 's|company_details_complete.json|$test_json|g; s|company_details.sql|$output_sql|g' \
                '$PROJECT_ROOT/scripts/json_to_sql.sh' > '$PROJECT_ROOT/scripts/unitest/test_data/temp_sql_${size}.sh' && \
            chmod +x '$PROJECT_ROOT/scripts/unitest/test_data/temp_sql_${size}.sh' && \
            bash '$PROJECT_ROOT/scripts/unitest/test_data/temp_sql_${size}.sh'
        ")
        
        local rate=$(echo "scale=2; $size / $duration" | bc)
        echo "$size      | $duration        | $rate" >> "$results_file"
        
        # בדיקת איכות התוצאות
        if [[ -f "$output_sql" ]]; then
            local sql_inserts=$(grep -c "INSERT INTO" "$output_sql")
            if [[ $sql_inserts -ne 1 ]]; then
                log_warning "Expected 1 INSERT statement, got $sql_inserts"
            fi
        fi
        
        # ניקוי
        rm -f "$test_json" "$output_sql" "$PROJECT_ROOT/scripts/unitest/test_data/temp_sql_${size}.sh"
    done
    
    log_success "SQL performance test completed"
    cat "$results_file"
}

# בדיקת שימוש בזיכרון
test_memory_usage() {
    log_info "Testing memory usage..."
    
    local results_file="$RESULTS_DIR/memory_usage.txt"
    
    echo "Memory Usage Test Results" > "$results_file"
    echo "========================" >> "$results_file"
    echo "Process | Memory (MB) | Peak Memory (MB)" >> "$results_file"
    echo "--------|-------------|------------------" >> "$results_file"
    
    # בדיקת שימוש בזיכרון בסקריפט הראשי
    log_info "Testing memory usage for main script..."
    
    # יצירת קובץ בדיקה קטן
    local test_mapping="$PROJECT_ROOT/scripts/unitest/test_data/test_memory.json"
    mkdir -p "$(dirname "$test_mapping")"
    
    echo '[{"id": 1, "name": "Test Company", "ticker": "TEST"}]' > "$test_mapping"
    
    # שמירת הקובץ המקורי
    cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
    cp "$test_mapping" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
    
    # מדידת זיכרון
    local output_json="$PROJECT_ROOT/complete_companies_data/json/test_memory.json"
    local output_jsonl="$PROJECT_ROOT/complete_companies_data/json/test_memory.ndjson"
    
    mkdir -p "$(dirname "$output_json")"
    
    # יצירת סקריפט זמני
    local temp_script="$PROJECT_ROOT/scripts/unitest/test_data/temp_memory.sh"
    sed "s|company_details_complete.json|test_memory.json|g; s|company_details.ndjson|test_memory.ndjson|g" \
        "$PROJECT_ROOT/scripts/get_Data.sh" > "$temp_script"
    
    chmod +x "$temp_script"
    
    # הרצה עם מדידת זיכרון
    /usr/bin/time -v bash "$temp_script" 2>&1 | grep -E "(Maximum resident set size|Average resident set size)" >> "$results_file" || true
    
    # שחזור הקובץ המקורי
    cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
    rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$test_mapping" "$temp_script"
    rm -f "$output_json" "$output_jsonl"
    
    log_success "Memory usage test completed"
    cat "$results_file"
}

# בדיקת עמידות (stress test)
test_system_stability() {
    log_info "Testing system stability..."
    
    local results_file="$RESULTS_DIR/stability_test.txt"
    
    echo "System Stability Test Results" > "$results_file"
    echo "============================" >> "$results_file"
    
    # בדיקת עמידות עם מספר הרצות
    local test_runs=5
    local success_count=0
    
    for ((run=1; run<=test_runs; run++)); do
        log_info "Stability test run $run/$test_runs..."
        
        # יצירת קובץ בדיקה
        local test_mapping="$PROJECT_ROOT/scripts/unitest/test_data/test_stability_${run}.json"
        mkdir -p "$(dirname "$test_mapping")"
        
        echo '[{"id": 1, "name": "Test Company", "ticker": "TEST"}]' > "$test_mapping"
        
        # שמירת הקובץ המקורי
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup"
        cp "$test_mapping" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        
        # הרצת הסקריפט
        local output_json="$PROJECT_ROOT/complete_companies_data/json/test_stability_${run}.json"
        local output_jsonl="$PROJECT_ROOT/complete_companies_data/json/test_stability_${run}.ndjson"
        
        mkdir -p "$(dirname "$output_json")"
        
        local temp_script="$PROJECT_ROOT/scripts/unitest/test_data/temp_stability_${run}.sh"
        sed "s|company_details_complete.json|test_stability_${run}.json|g; s|company_details.ndjson|test_stability_${run}.ndjson|g" \
            "$PROJECT_ROOT/scripts/get_Data.sh" > "$temp_script"
        
        chmod +x "$temp_script"
        
        if bash "$temp_script"; then
            success_count=$((success_count + 1))
            echo "Run $run: SUCCESS" >> "$results_file"
        else
            echo "Run $run: FAILED" >> "$results_file"
        fi
        
        # שחזור הקובץ המקורי
        cp "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json"
        rm -f "$PROJECT_ROOT/complete_companies_data/json_Map/ticker_mapping.json.backup" "$test_mapping" "$temp_script"
        rm -f "$output_json" "$output_jsonl"
    done
    
    local success_rate=$((success_count * 100 / test_runs))
    echo "Success Rate: $success_count/$test_runs ($success_rate%)" >> "$results_file"
    
    if [[ $success_rate -ge 80 ]]; then
        log_success "System stability test passed ($success_rate% success rate)"
    else
        log_warning "System stability test failed ($success_rate% success rate)"
    fi
    
    cat "$results_file"
}

# פונקציה ראשית
main() {
    echo "⚡ Performance Testing System"
    echo "============================="
    echo ""
    
    mkdir -p "$RESULTS_DIR"
    
    test_api_performance
    echo ""
    test_csv_performance
    echo ""
    test_sql_performance
    echo ""
    test_memory_usage
    echo ""
    test_system_stability
    
    echo ""
    log_success "Performance testing completed!"
    echo "Results saved in: $RESULTS_DIR/"
}

# הרצה אם הסקריפט נקרא ישירות
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
