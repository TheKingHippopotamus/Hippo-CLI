# HippoCLI: Enterprise Financial Data Pipeline

<div align="center">

![HippoCLI]

**A production-grade command-line toolkit for financial data acquisition, transformation, validation, and analytics**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Type Hints](https://img.shields.io/badge/type%20hints-complete-green.svg)](https://www.python.org/dev/peps/pep-0484/)

</div>

---

## The Story Behind HippoCLI

As a developer with a passion for financial markets, I found myself repeatedly wrestling with fragmented data sources, inconsistent formats, and manual data transformation workflows. What started as a weekend project to automate my personal investment research quickly evolved into a comprehensive data engineering solution.

The challenge was clear: financial data comes in many shapes and sizes—JSON from APIs, CSV for spreadsheets, Parquet for analytics, SQL for databases. Each format serves a different purpose, but manually converting between them was time-consuming and error-prone. More critically, I needed a system that could validate data integrity, handle failures gracefully, and provide actionable analytics—all while maintaining the flexibility to adapt to changing data schemas.

HippoCLI emerged from this need: a battle-tested, production-ready toolkit that transforms raw financial data into structured, validated, multi-format outputs. Built with modern Python best practices, it embodies the principle that great tools should be both powerful and elegant—handling complex data pipelines while remaining simple to use.

---

## Architecture Overview

HippoCLI follows a modular, extensible architecture designed for maintainability and scalability:

### Core Design Principles

- **Separation of Concerns**: Each module handles a distinct responsibility (fetching, validation, conversion, analytics)
- **Type Safety**: Comprehensive type hints using Python 3.9+ typing and Pydantic models
- **Configuration-Driven**: YAML-based configuration with environment variable overrides
- **Error Resilience**: Retry mechanisms with exponential backoff for network operations
- **Format Agnostic**: Unified data model that transforms seamlessly across formats

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      HippoCLI Core                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Fetcher    │  │  Validator   │  │  Converter   │      │
│  │              │  │              │  │              │      │
│  │ • HTTP/HTTPS │  │ • Schema     │  │ • JSON       │      │
│  │ • Retry      │  │   Validation │  │ • CSV        │      │
│  │ • Rate Limit │  │ • Data       │  │ • Parquet    │      │
│  │              │  │   Integrity  │  │ • SQL        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Analytics   │  │   Config     │  │   Models     │      │
│  │              │  │              │  │              │      │
│  │ • Metrics    │  │ • YAML       │  │ • Pydantic   │      │
│  │ • Statistics │  │ • Env Vars  │  │ • Validation │      │
│  │ • Insights   │  │ • Paths     │  │ • Type Safe  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   JSON   │  │   CSV    │  │  Parquet  │  │   SQL    │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion**: Fetcher module retrieves data from external APIs with retry logic and error handling
2. **Validation**: Validator ensures data integrity against Pydantic schemas and business rules
3. **Transformation**: Converter normalizes and flattens nested structures for target formats
4. **Analytics**: Analytics engine computes financial metrics and statistical insights
5. **Output**: Multi-format export (JSON, CSV, Parquet, SQL) with optimized schemas

---

## Technology Stack

### Core Technologies

- **Python 3.9+**: Modern Python with type hints, dataclasses, and pathlib
- **Typer**: Type-safe CLI framework built on Click, leveraging Python type hints
- **Pydantic v2**: Data validation and settings management with runtime type checking
- **Polars**: High-performance DataFrame library for data manipulation (Rust-based)
- **Pandas**: Statistical analysis and time-series operations
- **PyArrow**: Efficient Parquet I/O and columnar data processing

### Infrastructure & Tooling

- **httpx**: Modern async-capable HTTP client with connection pooling
- **Tenacity**: Sophisticated retry logic with exponential backoff
- **Rich**: Beautiful terminal output with tables, progress bars, and syntax highlighting
- **Docker**: Containerized deployment with multi-stage builds
- **pytest**: Comprehensive test suite with coverage reporting

### Development Standards

- **Type Safety**: Full type coverage with mypy strict mode
- **Code Quality**: Ruff for linting, Black for formatting
- **Testing**: pytest with coverage reporting and fixtures
- **Documentation**: Comprehensive docstrings and type annotations

---

## Key Features

### 🔄 Multi-Format Data Conversion

Transform financial data seamlessly across formats optimized for different use cases:

- **JSON**: Human-readable, schema-flexible storage
- **CSV**: Universal compatibility with spreadsheet tools
- **Parquet**: Columnar format for analytics workloads (10-100x compression)
- **SQL**: Ready-to-import database schemas with foreign key relationships

![Data Conversion](static/convert.png)

### ✅ Robust Data Validation

Ensure data integrity with multi-layer validation:

- Schema validation using Pydantic models
- Business rule enforcement (ticker format, required fields)
- Mapping file integrity checks
- Cross-reference validation between datasets

![Validation](static/validate.png)

### 📊 Advanced Analytics Engine

Compute financial metrics and statistical insights:

- Price volatility calculations (annualized)
- Maximum drawdown analysis
- Rolling window statistics
- Time-series aggregations

![Analytics](static/Analytics.png)

### 🚀 High-Performance Data Fetching

Efficient data acquisition with enterprise-grade reliability:

- Automatic retry with exponential backoff
- Resume capability for interrupted operations
- Concurrent request handling
- Rate limiting and timeout management

![Data Fetching](static/fetch.png)

### 🗺️ Intelligent Ticker Management

Flexible ticker mapping system with auto-discovery:

- JSON-based ticker registry
- Automatic ID assignment and validation
- Support for batch and single-ticker operations
- Mapping file repair utilities

![Ticker Mapping](static/tickermaps.png)

### 📈 Rich Terminal Interface

Beautiful, informative CLI output:

- Color-coded status messages
- Progress indicators for long operations
- Structured data tables
- JSON output formatting

![Results Display](static/results.png)

---

## Technical Highlights

### Type-Safe Configuration Management

Leveraging Pydantic Settings for type-safe, validated configuration with multiple sources:

```python
# YAML config → Environment variables → Defaults
# Automatic path resolution and validation
# Docker-aware path detection
```

### Efficient Data Processing

- **Polars** for high-performance DataFrame operations (10-100x faster than Pandas for large datasets)
- **Lazy evaluation** where possible to minimize memory footprint
- **Columnar storage** in Parquet format for optimal analytics performance

### Error Handling & Resilience

- Custom exception hierarchy for precise error handling
- Retry decorators with configurable strategies
- Graceful degradation when optional data is missing
- Comprehensive logging at multiple levels

### Extensibility

- Plugin-ready architecture for custom converters
- Modular design allows easy addition of new formats
- Configuration-driven behavior enables customization without code changes

---

## Installation & Quick Start

### Prerequisites

- Python 3.9 or higher
- pip or poetry for package management
- Docker (optional, for containerized usage)

### Installation

#### Local Installation

```bash
# Clone the repository
git clone https://github.com/TheKingHippopotamus/Hippo-CLI.git
cd Hippo-CLI

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

#### Docker Installation

```bash
# Build the image
docker build -t hippocli .

# Run commands
docker run --rm -v $(pwd)/data:/app/data hippocli fetch AAPL
```

#### Docker Compose Installation (Recommended)

Using Docker Compose provides a more convenient way to manage the container:

**Option 1: Using Wrapper Scripts (Easiest)**

```bash
# Make script executable (Linux/Mac)
chmod +x scripts/hippocli.sh

# Use the wrapper script
./scripts/hippocli.sh setup AAPL
./scripts/hippocli.sh status
./scripts/hippocli.sh shell start  # Interactive mode
```

**Option 2: Using Docker Compose Directly**

```bash
# Build the image
docker-compose build

# Run commands
docker-compose run --rm hippocli setup AAPL
docker-compose run --rm hippocli status
docker-compose run --rm hippocli shell start  # Interactive mode
```

**Option 3: Create an Alias (Most Convenient)**

Add to your `~/.bashrc` or `~/.zshrc`:
```bash
alias hippocli='docker-compose run --rm hippocli'
```

Then use directly:
```bash
hippocli setup AAPL
hippocli status
hippocli shell start
```

**Note**: The Docker Compose configuration mounts `./data` and `./config` directories. The application will automatically detect the `/app/data` mount point and use it for all output files.

### Command Reference

#### Understanding the Commands

HippoCLI offers different commands for different purposes. Here's what each command does:

| Command | What It Does | When to Use |
|---------|-------------|-------------|
| `setup [TICKER]` | **First-time setup**: Creates mapping file + fetches data + converts + validates | Adding a new ticker for the first time |
| `update [TICKER]` | **Full update**: Fetches + converts + validates (all steps) | Updating existing ticker(s) with latest data |
| `fetch [TICKER]` | **Download only**: Fetches raw data from API (JSON format) | When you only need to download new data |
| `convert [TICKER]` | **Format conversion**: Converts JSON to CSV, Parquet, SQL | After fetching, to generate other formats |
| `validate [TICKER]` | **Data validation**: Checks data integrity and schema | To verify data quality |
| `status` | **Project overview**: Shows tickers, files, and completion status | Check what you have and what's missing |
| `list` | **Ticker list**: Lists all tickers with their format status | Quick view of all tickers |
| `analytics TICKER` | **Financial analysis**: Calculates metrics and statistics | After data is ready, for insights |
| `shell start` | **Interactive mode**: Menu-driven interface | Best for beginners or complex workflows |

#### Key Differences

**`setup` vs `update`:**
- `setup` - For **new tickers** (creates mapping file if needed)
- `update` - For **existing tickers** (assumes mapping already exists)

**`update` vs individual commands:**
- `update` - Does **everything** (fetch + convert + validate) in one command
- Individual commands (`fetch`, `convert`, `validate`) - Do **one step** at a time

**When to use what:**
- **New ticker?** → Use `setup AAPL`
- **Update existing?** → Use `update AAPL` or `update` (all)
- **Only need fresh data?** → Use `fetch AAPL`
- **Only need formats?** → Use `convert AAPL`
- **Just checking?** → Use `status` or `list`

### Quick Start Guide

#### Scenario 1: Adding Your First Ticker

```bash
# One command does everything: creates mapping, fetches data, converts formats, validates
hippocli setup AAPL

# Check the results
hippocli status
```

#### Scenario 2: Adding More Tickers

```bash
# Add another ticker
hippocli setup MSFT

# Add multiple tickers one by one
hippocli setup GOOGL
hippocli setup TSLA
```

#### Scenario 3: Updating Existing Data

```bash
# Update all tickers (fetch + convert + validate)
hippocli update

# Or update just one ticker
hippocli update AAPL
```

#### Scenario 4: Step-by-Step Control

If you prefer to control each step:

```bash
# Step 1: Fetch latest data
hippocli fetch AAPL

# Step 2: Convert to all formats
hippocli convert AAPL

# Step 3: Validate
hippocli validate AAPL
```

#### Scenario 5: Interactive Mode (Recommended for Beginners)

The easiest way to use HippoCLI:

```bash
# Start interactive mode
hippocli shell start

# Or with Docker
./scripts/hippocli.sh shell start
```

The interactive menu guides you through all options with clear descriptions.

---

## Interactive Mode Guide

The interactive mode (`hippocli shell start`) provides an intuitive menu-driven interface:

### Main Menu Options

1. **Quick Start** - Complete setup for a new ticker (fetch + convert + validate)
2. **Update All** - Update all tickers (fetch + convert + validate)
3. **Full Pipeline** - Complete workflow for a specific ticker
4. **Fetch Data** - Download company data
5. **Convert Formats** - Convert JSON to CSV, Parquet, SQL
6. **Validate Data** - Check data integrity
7. **Run Analytics** - Calculate financial metrics
8. **View Status** - Display project status
9. **List Tickers** - Show all tickers with their status
10. **Fix Mapping IDs** - Repair mapping file IDs

### Features

- **Status Summary** - Always visible at the top showing:
  - Number of tickers in mapping
  - Tickers with data
  - Tickers with complete formats
  
- **Progress Indicators** - Visual feedback for long-running operations

- **Error Handling** - Clear error messages with suggestions

## Project Structure

```
HippoCLI/
├── src/hippocli/          # Core application code
│   ├── cli.py            # Typer CLI command definitions
│   ├── fetcher.py        # HTTP data acquisition
│   ├── converter.py      # Multi-format data transformation
│   ├── validator.py      # Data validation logic
│   ├── analytics.py      # Financial metrics computation
│   ├── config.py         # Configuration management
│   └── models.py         # Pydantic data models
├── scripts/              # Wrapper scripts for Docker
│   ├── hippocli.sh      # Linux/Mac wrapper
│   └── hippocli.bat      # Windows wrapper
├── config/               # Configuration files
├── tests/                # Test suite
├── static/               # Documentation assets
└── data/                 # Output data directory
```

---

## Performance Characteristics

- **Data Fetching**: ~100-200ms per ticker (network-dependent)
- **CSV Conversion**: ~10-50ms per file (depends on data size)
- **Parquet Conversion**: ~20-100ms per file (with compression)
- **SQL Generation**: ~5-30ms per file
- **Analytics**: ~50-200ms per ticker (depends on data volume)

---

## Best Practices & Design Decisions

### Why Polars + Pandas?

- **Polars**: Primary DataFrame library for data transformation (speed, memory efficiency)
- **Pandas**: Used selectively for time-series operations (mature ecosystem for financial data)

### Why Pydantic v2?

- Runtime type validation catches errors early
- Settings management with multiple source support
- Excellent performance with compiled validators
- Seamless integration with type checkers

### Why Typer over Click?

- Type hints provide automatic CLI argument validation
- Better IDE support and autocomplete
- Reduced boilerplate with decorator-based commands
- Native async support for future enhancements

### Why Separate Stock Price Data?

- Normalized database design (company details vs. time-series data)
- Optimized storage for different access patterns
- Enables efficient querying of historical price data
- Supports future time-series database integration

---

## Future Enhancements

- **Async/Await**: Full async support for concurrent data fetching
- **Database Integration**: Direct export to PostgreSQL, MySQL, SQLite
- **Streaming Processing**: Handle large datasets without loading into memory
- **Custom Analytics**: Plugin system for user-defined metrics
- **API Server**: REST API wrapper for web integration
- **Data Quality Reports**: Automated data quality scoring and reporting

---

## Contributing

This project demonstrates production-ready Python development practices:

- Comprehensive type annotations
- Modular, testable architecture
- Configuration-driven design
- Error handling and logging
- Docker containerization
- Professional documentation

---

## License

MIT License - See LICENSE file for details

---

<div align="center">

**Built with ❤️ by [TheKingHippopotamus](https://github.com/TheKingHippopotamus) for the financial data engineering community**

*Transforming raw data into actionable insights, one ticker at a time.*

</div>

