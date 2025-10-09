#!/usr/bin/env bash
set -euo pipefail

# ---- קונפיג ----
ID_NAME_JSON="/Users/kinghippo/Documents/shell_DataSet_DB/json_Map/ticker_mapping.json"
TICKER_MAPPING="/Users/kinghippo/Documents/shell_DataSet_DB/json_Map/ticker_mapping.json"
OUT_JSON="/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/json/company_details_complete.json"   # פלט סופי כ־JSON array
OUT_JSONL="/Users/kinghippo/Documents/shell_DataSet_DB/complete_companies_data/json/company_details.ndjson"         # פלט מצטבר כ־JSONL (שורה לכל טיקר)
TMP_DIR="$(mktemp -d)"
BASE_URL='https://compoundeer.com/api/trpc/company.getByTicker?batch=1&input='

# אם יש לך טוקן (אם בכלל נדרש), תן דרך משתנה סביבה, לא בקוד:
# export SESSION_TOKEN="eyJhbGciOi..."
SESSION_COOKIE_HEADER=()
if [[ -n "${SESSION_TOKEN:-}" ]]; then
  SESSION_COOKIE_HEADER=(-b "compoundeer.session-token=${SESSION_TOKEN}")
fi

# ---- ניקוי קבצי פלט קודמים ----
: > "$OUT_JSONL"

# ---- לולאת שמות/טיקרים מתוך id_name.json ----
# מצפה למבנה: [{"id": "...", "name":"AAPL"}, ...]
TOTAL=$(jq 'length' "$ID_NAME_JSON")
COUNTER=0

jq -c '.[]' "$ID_NAME_JSON" | while read -r row; do
  COUNTER=$((COUNTER+1))
  ID=$(echo "$row"   | jq -r '.id')
  NAME=$(echo "$row" | jq -r '.name')

  # חיפוש הטיקר המתאים במיפוי
  TICKER=$(jq -r --arg name "$NAME" '.[] | select(.name == $name) | .ticker' "$TICKER_MAPPING" | head -1)
  
  if [[ -z "$TICKER" ]]; then
    echo "[$COUNTER/$TOTAL] Skip: $NAME (no ticker found)" >&2
    continue
  fi

  echo "[$COUNTER/$TOTAL] Fetch: $NAME -> $TICKER"

  # בונים את input JSON ומקודדים ל-URL:
  # {"0":{"json":"<TICKER>"}}
  INPUT_JSON=$(jq -nc --arg t "$TICKER" '
    {
      "0": {"json": $t}
    }')
  ENCODED_INPUT=$(printf '%s' "$INPUT_JSON" | jq -sRr @uri)

  # הקריאה:
  RESP=$(curl -sS \
      "${SESSION_COOKIE_HEADER[@]}" \
      -H 'accept: */*' \
      -H 'accept-language: en-US,en;q=0.8' \
      -H 'cache-control: no-cache' \
      -H 'content-type: application/json' \
      -H 'dnt: 1' \
      -H 'pragma: no-cache' \
      -H 'sec-fetch-dest: empty' \
      -H 'sec-fetch-mode: cors' \
      -H 'sec-fetch-site: same-origin' \
      -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36' \
      -H 'x-trpc-source: nextjs-react' \
      "${BASE_URL}${ENCODED_INPUT}" \
    || true)

  # בדיקת תגובה בסיסית
  if [[ -z "$RESP" ]]; then
    echo "  ! empty / network error: $NAME" >&2
    continue
  fi

  # בדיקה אם התגובה היא JSON תקין
  if ! echo "$RESP" | jq empty 2>/dev/null; then
    echo "  ! invalid JSON response: $NAME" >&2
    continue
  fi

  # בדיקה אם יש שגיאה בתגובה
  if echo "$RESP" | jq -e '.error' >/dev/null 2>&1; then
    echo "  ! API error: $NAME" >&2
    continue
  fi

  # חילוץ ה־payload של company.getByTicker המופיע במקום [0]
  # ושמירה רק של המפתחות שציינת:
  # נרכז גם id ו-name המקוריים כדי לשמר קשר
  echo "$RESP" | jq -c --arg id "$ID" --arg name "$NAME" --arg ticker "$TICKER" '
    (.[0].result.data.json.company // {}) as $c
    | {
        id: $id,
        name: $name,
        ticker: $ticker,
        aggregations: $c.aggregations,
        insights: $c.insights,
        sector: $c.sector,
        industry: $c.industry,
        description: $c.description,
        indices: $c.indices,
        exchanges: $c.exchanges,
        lastUpdated: $c.lastUpdated
      }' >> "$OUT_JSONL"

  # האטה קלה למניעת rate limiting
  sleep 0.25
done

# הרכבת JSON array מה־NDJSON
jq -s '.' "$OUT_JSONL" > "$OUT_JSON"

echo "✓ saved: $OUT_JSON"
