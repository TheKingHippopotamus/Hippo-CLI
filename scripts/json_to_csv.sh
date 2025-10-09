#!/usr/bin/env bash
set -euo pipefail

# ---- קונפיג ----
INPUT_JSON="/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/json/company_details_complete.json"
OUTPUT_CSV="/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/csv/company_details.csv"

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

echo "Converting JSON to CSV..."

# המרה ל-CSV עם jq
# נחלץ את כל השדות הבסיסיים ואת השדות המורכבים
jq -r '
  # כותרת CSV
  "id,name,ticker,sector,industry,description,exchanges,indices,lastUpdated," +
  "earnings,ebit,roe,roa,fcf,equity,g_stability,pe,peg,pb,pfcf,ps,price_to_cash," +
  "debt_over_equity,debt_over_fcf,net_margins,gross_margins,op_margins," +
  "earnings_cagrr,sales_growth_yoy,sales_growth_qoq,sales_cagrr,fcf_cagrr,equity_cagrr," +
  "earnings_stability,earnings_growth_yoy,earnings_growth_qoq," +
  "market_cap,revenue,dividend_yield,payout_ratio,assets,total_debt,cash,shares_outstanding,ev," +
  "earnings_score,moat_score,safety_score,final_score,working_capital,current_ratio,gross_profit"

  # נתונים
  , (.[] | 
    [
      .id,
      .name,
      .ticker,
      .sector,
      .industry,
      (.description // ""),
      (.exchanges // [] | join(";")),
      (.indices // [] | join(";")),
      (.lastUpdated // {} | tostring),
      # aggregations
      (.aggregations.earnings // ""),
      (.aggregations.ebit // ""),
      (.aggregations.roe // ""),
      (.aggregations.roa // ""),
      (.aggregations.fcf // ""),
      (.aggregations.equity // ""),
      (.aggregations.g_stability // ""),
      (.aggregations.pe // ""),
      (.aggregations.peg // ""),
      (.aggregations.pb // ""),
      (.aggregations.pfcf // ""),
      (.aggregations.ps // ""),
      (.aggregations.price_to_cash // ""),
      (.aggregations.debt_over_equity // ""),
      (.aggregations.debt_over_fcf // ""),
      (.aggregations.net_margins // ""),
      (.aggregations.gross_margins // ""),
      (.aggregations.op_margins // ""),
      (.aggregations.earnings_cagrr // ""),
      (.aggregations.sales_growth_yoy // ""),
      (.aggregations.sales_growth_qoq // ""),
      (.aggregations.sales_cagrr // ""),
      (.aggregations.fcf_cagrr // ""),
      (.aggregations.equity_cagrr // ""),
      (.aggregations.earnings_stability // ""),
      (.aggregations.earnings_growth_yoy // ""),
      (.aggregations.earnings_growth_qoq // ""),
      (.aggregations.market_cap // ""),
      (.aggregations.revenue // ""),
      (.aggregations.dividend_yield // ""),
      (.aggregations.payout_ratio // ""),
      (.aggregations.assets // ""),
      (.aggregations.total_debt // ""),
      (.aggregations.cash // ""),
      (.aggregations.shares_outstanding // ""),
      (.aggregations.ev // ""),
      (.aggregations.earnings_score // ""),
      (.aggregations.moat_score // ""),
      (.aggregations.safety_score // ""),
      (.aggregations.final_score // ""),
      (.aggregations.working_capital // ""),
      (.aggregations.current_ratio // ""),
      (.aggregations.gross_profit // "")
    ] | 
    map(if . == null then "" else . end) |
    map(if type == "string" then "\"" + . + "\"" else . end) |
    join(",")
  )
' "$INPUT_JSON" > "$OUTPUT_CSV"

echo "✓ CSV saved: $OUTPUT_CSV"
echo "Total rows: $(wc -l < "$OUTPUT_CSV")"
