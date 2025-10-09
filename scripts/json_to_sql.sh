#!/usr/bin/env bash
set -euo pipefail

# ---- קונפיג ----
INPUT_JSON="/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/json/company_details_complete.json"
OUTPUT_SQL="/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/sql/company_details.sql"
TABLE_NAME="companies"

# בדיקה שהקובץ קיים
if [[ ! -f "$INPUT_JSON" ]]; then
    echo "Error: Input file $INPUT_JSON not found" >&2
    exit 1
fi

# בדיקה שהקובץ לא ריק
if [[ ! -s "$INPUT_JSON" ]]; then
    echo "Error: Input file $INPUT_JSON is empty" >&2
    exit 1
fi

echo "Converting JSON to SQL..."

# יצירת טבלת SQL עם כל השדות
cat > "$OUTPUT_SQL" << 'EOF'
-- טבלת חברות עם נתונים פיננסיים מלאים
-- נוצר אוטומטית מקובץ JSON

DROP TABLE IF EXISTS companies;

CREATE TABLE companies (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    ticker TEXT,
    sector TEXT,
    industry TEXT,
    description TEXT,
    exchanges TEXT,
    indices TEXT,
    last_updated TEXT,
    
    -- נתונים פיננסיים בסיסיים
    earnings BIGINT,
    ebit BIGINT,
    roe DECIMAL(10,6),
    roa DECIMAL(10,6),
    fcf BIGINT,
    equity BIGINT,
    g_stability DECIMAL(10,6),
    
    -- יחסי הערכה
    pe DECIMAL(10,6),
    peg DECIMAL(10,6),
    pb DECIMAL(10,6),
    pfcf DECIMAL(10,6),
    ps DECIMAL(10,6),
    price_to_cash DECIMAL(10,6),
    
    -- יחסי חוב
    debt_over_equity DECIMAL(10,6),
    debt_over_fcf DECIMAL(10,6),
    
    -- מרווחים
    net_margins DECIMAL(10,6),
    gross_margins DECIMAL(10,6),
    op_margins DECIMAL(10,6),
    
    -- צמיחה
    earnings_cagrr DECIMAL(10,6),
    sales_growth_yoy DECIMAL(10,6),
    sales_growth_qoq DECIMAL(10,6),
    sales_cagrr DECIMAL(10,6),
    fcf_cagrr DECIMAL(10,6),
    equity_cagrr DECIMAL(10,6),
    
    -- יציבות
    earnings_stability DECIMAL(10,6),
    earnings_growth_yoy DECIMAL(10,6),
    earnings_growth_qoq DECIMAL(10,6),
    
    -- שווי שוק ונתונים נוספים
    market_cap DECIMAL(20,2),
    revenue BIGINT,
    dividend_yield DECIMAL(10,6),
    payout_ratio DECIMAL(10,6),
    assets BIGINT,
    total_debt BIGINT,
    cash BIGINT,
    shares_outstanding BIGINT,
    ev DECIMAL(20,2),
    
    -- ציונים
    earnings_score DECIMAL(10,6),
    moat_score DECIMAL(10,6),
    safety_score DECIMAL(10,6),
    final_score DECIMAL(10,6),
    
    -- הון חוזר ויחסים נוספים
    working_capital BIGINT,
    current_ratio DECIMAL(10,6),
    gross_profit BIGINT
);

EOF

# הוספת נתונים לטבלה
echo "INSERT INTO companies VALUES" >> "$OUTPUT_SQL"

# המרת הנתונים ל-SQL עם jq
jq -r '
  .[] | 
  "(" + (
    [
      .id,
      (.name | "\"" + . + "\""),
      (.ticker | if . then "\"" + . + "\"" else "NULL" end),
      (.sector | if . then "\"" + . + "\"" else "NULL" end),
      (.industry | if . then "\"" + . + "\"" else "NULL" end),
      (.description | if . then "\"" + . + "\"" else "NULL" end),
      (.exchanges // [] | if length > 0 then "\"" + (join(";")) + "\"" else "NULL" end),
      (.indices // [] | if length > 0 then "\"" + (join(";")) + "\"" else "NULL" end),
      (.lastUpdated // {} | if . then "\"" + (tostring) + "\"" else "NULL" end),
      # aggregations
      (.aggregations.earnings // "NULL"),
      (.aggregations.ebit // "NULL"),
      (.aggregations.roe // "NULL"),
      (.aggregations.roa // "NULL"),
      (.aggregations.fcf // "NULL"),
      (.aggregations.equity // "NULL"),
      (.aggregations.g_stability // "NULL"),
      (.aggregations.pe // "NULL"),
      (.aggregations.peg // "NULL"),
      (.aggregations.pb // "NULL"),
      (.aggregations.pfcf // "NULL"),
      (.aggregations.ps // "NULL"),
      (.aggregations.price_to_cash // "NULL"),
      (.aggregations.debt_over_equity // "NULL"),
      (.aggregations.debt_over_fcf // "NULL"),
      (.aggregations.net_margins // "NULL"),
      (.aggregations.gross_margins // "NULL"),
      (.aggregations.op_margins // "NULL"),
      (.aggregations.earnings_cagrr // "NULL"),
      (.aggregations.sales_growth_yoy // "NULL"),
      (.aggregations.sales_growth_qoq // "NULL"),
      (.aggregations.sales_cagrr // "NULL"),
      (.aggregations.fcf_cagrr // "NULL"),
      (.aggregations.equity_cagrr // "NULL"),
      (.aggregations.earnings_stability // "NULL"),
      (.aggregations.earnings_growth_yoy // "NULL"),
      (.aggregations.earnings_growth_qoq // "NULL"),
      (.aggregations.market_cap // "NULL"),
      (.aggregations.revenue // "NULL"),
      (.aggregations.dividend_yield // "NULL"),
      (.aggregations.payout_ratio // "NULL"),
      (.aggregations.assets // "NULL"),
      (.aggregations.total_debt // "NULL"),
      (.aggregations.cash // "NULL"),
      (.aggregations.shares_outstanding // "NULL"),
      (.aggregations.ev // "NULL"),
      (.aggregations.earnings_score // "NULL"),
      (.aggregations.moat_score // "NULL"),
      (.aggregations.safety_score // "NULL"),
      (.aggregations.final_score // "NULL"),
      (.aggregations.working_capital // "NULL"),
      (.aggregations.current_ratio // "NULL"),
      (.aggregations.gross_profit // "NULL")
    ] | join(",")
  ) + ")"
' "$INPUT_JSON" | sed '$!s/$/,/' >> "$OUTPUT_SQL"

# הוספת נקודה-פסיק בסוף
echo ";" >> "$OUTPUT_SQL"

# הוספת אינדקסים לשיפור ביצועים
cat >> "$OUTPUT_SQL" << 'EOF'

-- אינדקסים לשיפור ביצועי חיפוש
CREATE INDEX idx_companies_ticker ON companies(ticker);
CREATE INDEX idx_companies_sector ON companies(sector);
CREATE INDEX idx_companies_industry ON companies(industry);
CREATE INDEX idx_companies_market_cap ON companies(market_cap);
CREATE INDEX idx_companies_revenue ON companies(revenue);
CREATE INDEX idx_companies_pe ON companies(pe);
CREATE INDEX idx_companies_roe ON companies(roe);

-- סטטיסטיקות
SELECT 'Total companies: ' || COUNT(*) as stats FROM companies;
SELECT 'Companies with tickers: ' || COUNT(*) as stats FROM companies WHERE ticker IS NOT NULL;
SELECT 'Companies by sector: ' || sector || ' (' || COUNT(*) || ')' as stats FROM companies GROUP BY sector ORDER BY COUNT(*) DESC LIMIT 10;

EOF

echo "✓ SQL saved: $OUTPUT_SQL"
echo "Total rows: $(grep -c "INSERT INTO" "$OUTPUT_SQL" || echo "0")"
echo "File size: $(ls -lh "$OUTPUT_SQL" | awk '{print $5}')"
