# HippoCLI

**Enterprise-Grade CLI Toolkit for Financial Data Acquisition, Validation, Conversion, and Analytics**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

---

## 🎯 Overview

HippoCLI is a production-ready command-line interface designed for financial data engineers and analysts who require robust, scalable solutions for acquiring, processing, and analyzing company financial datasets. Built with modern Python best practices, it provides a comprehensive toolkit for end-to-end data pipeline management.

### The Story Behind HippoCLI

As a data professional working with financial markets, I found myself repeatedly building ad-hoc scripts to fetch, validate, and transform company data from various sources. Each project required reinventing the wheel—handling API rate limits, managing data consistency, converting between formats, and ensuring data quality. The manual process was time-consuming, error-prone, and didn't scale.

HippoCLI was born from the frustration of spending more time on infrastructure than on actual analysis. I needed a tool that could handle the entire data lifecycle—from acquisition through validation to multi-format conversion—with the reliability and professionalism expected in enterprise environments. What started as a personal productivity tool evolved into a comprehensive solution that embodies industry best practices: type safety, robust error handling, configurable pipelines, and containerized deployment.

Today, HippoCLI serves as the foundation for financial data workflows, enabling rapid iteration on data-driven insights while maintaining the rigor required for production systems.

---

## 🏗️ Architecture

HippoCLI follows a modular, layered architecture designed for maintainability and extensibility:

### Core Components

**Data Acquisition Layer (`fetcher`)**
- Implements resilient HTTP client with exponential backoff retry logic
- Handles session management and authentication
- Supports incremental data collection with resume capabilities
- Built on `httpx` for async-capable HTTP operations

**Validation Layer (`validator`)**
- Schema validation using Pydantic models
- Data integrity checks (duplicate detection, referential consistency)
- Comprehensive error reporting with line-level diagnostics
- Mapping file validation and auto-repair utilities

**Transformation Layer (`converter`)**
- Multi-format conversion engine (NDJSON, JSON, CSV, Parquet, SQL)
- Optimized for large datasets using Polars DataFrame operations
- Handles nested data structures with intelligent serialization
- Type-preserving conversions with proper schema inference

**Analytics Engine (`analytics`)**
- Time-series financial metrics computation
- Rolling window calculations for volatility and drawdown analysis
- Integration with Pandas for statistical operations
- Configurable analysis horizons

**Configuration Management (`config`)**
- Hierarchical configuration system (YAML + environment variables)
- Type-safe settings using Pydantic Settings
- Path management with automatic directory creation
- Environment-aware configuration loading

**CLI Interface (`cli`)**
- Built on Typer for type-safe command definitions
- Rich terminal UI with formatted tables and progress indicators
- Interactive shell mode for iterative workflows
- Comprehensive help system and error messages

### Design Principles

- **Type Safety**: Full type annotations with Pydantic validation throughout
- **Error Resilience**: Graceful degradation with detailed error reporting
- **Configuration Flexibility**: Multiple configuration sources with clear precedence
- **Performance**: Optimized data processing using Polars for large-scale operations
- **Developer Experience**: Rich CLI output, comprehensive logging, and intuitive APIs

---

## 🛠️ Technology Stack

### Core Technologies

- **Python 3.9+**: Modern Python features with type hints and dataclasses
- **Typer**: Type-safe CLI framework built on Click
- **Pydantic v2**: Data validation and settings management with runtime type checking
- **Polars**: High-performance DataFrame library for large-scale data processing
- **Pandas**: Statistical analysis and time-series operations
- **httpx**: Modern HTTP client with async support
- **Tenacity**: Retry logic with exponential backoff strategies
- **Rich**: Beautiful terminal formatting and progress indicators
- **PyArrow**: Parquet file format support
- **PyYAML**: Configuration file parsing

### Development & Quality

- **pytest**: Comprehensive test suite with coverage reporting
- **ruff**: Fast Python linter and formatter
- **black**: Code formatting
- **mypy**: Static type checking
- **pre-commit**: Git hooks for code quality

### Deployment

- **Docker**: Containerized deployment with multi-stage builds
- **docker-compose**: Orchestration for development environments

---

## 📦 Installation

### From Source

```bash
git clone https://github.com/yourusername/HippoCLI.git
cd HippoCLI
pip install -e .
```

### Using Docker

```bash
docker build -t hippocli .
docker run --rm -v $(pwd)/data:/app/data hippocli --help
```

### Using Docker Compose

```bash
docker-compose run --rm hippocli fetch --ticker AAPL
```

---

## 🚀 Quick Start

### Basic Workflow

1. **Fetch company data**:
   ```bash
   hippocli fetch --ticker AAPL
   ```

2. **Validate data integrity**:
   ```bash
   hippocli validate
   ```

3. **Convert to multiple formats**:
   ```bash
   hippocli convert
   ```

4. **Run analytics**:
   ```bash
   hippocli analytics AAPL --horizon 90
   ```

### Interactive Mode

Launch the interactive shell for iterative workflows:

```bash
hippocli shell start
```

---

## 📋 Features

### Data Acquisition
- ✅ Batch and single-ticker fetching
- ✅ Resume capability for interrupted downloads
- ✅ Automatic retry with exponential backoff
- ✅ Session management and authentication
- ✅ Rate limiting and timeout handling

### Data Validation
- ✅ Schema validation with detailed error reporting
- ✅ Duplicate detection (IDs and tickers)
- ✅ Data integrity checks
- ✅ Mapping file validation and repair

### Format Conversion
- ✅ NDJSON (Newline Delimited JSON) for streaming
- ✅ JSON array for web APIs
- ✅ CSV for spreadsheet compatibility
- ✅ Parquet for analytical workloads
- ✅ SQL INSERT statements for database import

### Analytics
- ✅ Price metrics (latest, average, high, low)
- ✅ Volatility calculations (annualized)
- ✅ Maximum drawdown analysis
- ✅ Configurable time horizons
- ✅ Time-series aggregation

### Developer Experience
- ✅ Type-safe CLI with auto-completion
- ✅ Rich terminal output with tables and colors
- ✅ Comprehensive logging with configurable levels
- ✅ Interactive shell mode
- ✅ Configuration via YAML or environment variables

---

## ⚙️ Configuration

HippoCLI supports multiple configuration sources with clear precedence:

1. Command-line arguments (highest priority)
2. Environment variables (`HIPPOCLI_*`)
3. YAML configuration file (`config/default.yaml`)
4. Default values (lowest priority)

### Environment Variables

```bash
export HIPPOCLI_BASE_URL="https://api.example.com"
export HIPPOCLI_REQUEST_TIMEOUT=60
export HIPPOCLI_SESSION_TOKEN="your-token"
```

### Configuration File

Edit `config/default.yaml` to customize default paths and settings.

---

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v --cov=hippocli --cov-report=html
```

---

## 📊 Performance

HippoCLI is optimized for handling large datasets:

- **Polars-based processing**: 10-100x faster than Pandas for large DataFrames
- **Streaming NDJSON**: Memory-efficient processing of large files
- **Parallel fetching**: Configurable concurrency for API requests
- **Incremental processing**: Resume capability prevents data loss

---

## 🔒 Production Considerations

- **Error Handling**: Comprehensive exception handling with detailed logging
- **Data Validation**: Schema validation prevents corrupted data propagation
- **Retry Logic**: Automatic retry with exponential backoff for transient failures
- **Configuration Management**: Environment-aware settings for different deployment stages
- **Containerization**: Docker support for consistent deployments
- **Type Safety**: Full type annotations enable static analysis and IDE support

---

## 🤝 Contributing

Contributions are welcome! Please ensure:

- Code follows the project's style guidelines (enforced by `ruff` and `black`)
- All tests pass (`pytest`)
- Type checking passes (`mypy`)
- New features include appropriate tests

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

Built with modern Python best practices and inspired by the need for reliable, professional-grade data tools in financial analysis workflows.

---

**HippoCLI** - *Empowering data professionals to focus on insights, not infrastructure.*

