
##  First Step — Manage Permissions

Before running any script, make them executable:

```bash
cd scripts
```

```bash
chmod +x scripts/*.sh
chmod +x scripts/unitest/scripts/*.sh

```

---

##  Second Step — Run the Main Script

The main script (`get_Data.sh`) loops through your ticker list, fetches data for each company, and creates two output files:

* `company_details_complete.json` — JSON array
* `company_details.ndjson` — NDJSON (line-per-company)

**Command:**

```bash
./get_Data.sh
```

After completion, both JSON files will be created in your working directory.

---

##  Third Step — Convert to CSV or SQL

Once the JSON is ready, you can easily convert it:

### ➤ To CSV

Creates `company_details.csv` for spreadsheet analysis.

```bash
./json_to_csv.sh
```

### ➤ To SQL

Creates `company_details.sql` for loading into databases like SQLite or PostgreSQL.

```bash
./json_to_sql.sh
```

---

# shell_DataSet_DB
