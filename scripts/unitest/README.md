# Unit Testing System for Data Fetching

## File Structure

```
scripts/unitest/
├── README.md                 # System documentation
├── run_all_tests.sh          # Main script to run all tests
├── test_runner.sh            # Basic functionality tests
├── data_validator.sh         # Data quality validation tests
├── performance_test.sh       # Performance and stability tests
├── results/                  # Test results
└── test_data/                # Temporary test files
```

## Setup

### Grant Permissions
```bash
chmod +x scripts/unitest/scripts/*.sh
```

## Usage

### Run All Tests
```bash
bash scripts/unitest/scripts/run_all_tests.sh --all
```

### Specific Tests
```bash
# Basic functionality tests
bash scripts/unitest/scripts/run_all_tests.sh --basic

# Data quality validation
bash scripts/unitest/scripts/run_all_tests.sh --data-quality

# Performance tests
bash scripts/unitest/scripts/run_all_tests.sh --performance
```

### Cleanup Test Files
```bash
bash scripts/unitest/scripts/run_all_tests.sh --cleanup
```

## System Requirements

- **Bash**: Version 4.0 and above
- **jq**: For JSON processing
- **curl**: For API data fetching
- **bc**: For calculations
- **time**: For performance measurement

## Result Files
- `results/api_performance.txt`: API performance
- `results/csv_performance.txt`: CSV conversion performance
- `results/sql_performance.txt`: SQL conversion performance
- `results/memory_usage.txt`: Memory usage
- `results/stability_test.txt`: Stability test results

## Troubleshooting

**1. "jq: command not found" error**
```bash
brew install jq  # macOS
sudo apt-get install jq  # Ubuntu
```

**2. "bc: command not found" error**
```bash
brew install bc  # macOS
sudo apt-get install bc  # Ubuntu
```

**3. Permission error**
```bash
chmod +x scripts/unitest/scripts/*.sh
```

**4. Path error**
```bash
cd /Users/kinghippo/Documents/shell_DataSet_DB
bash scripts/unitest/scripts/run_all_tests.sh
```
