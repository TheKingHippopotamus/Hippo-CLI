#!/bin/bash
# HippoCLI Docker Wrapper Script
# Simplifies running HippoCLI commands with Docker Compose

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project directory
cd "$PROJECT_DIR"

# Ensure required directories exist
mkdir -p data config data/mappings data/json data/csv data/parquet data/sql

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH" >&2
    echo "Please install Docker Desktop or Docker Engine" >&2
    exit 1
fi

# Use docker compose (newer) or docker-compose (older)
if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "Error: Neither 'docker compose' nor 'docker-compose' is available" >&2
    exit 1
fi

# Check if .env file exists and is valid (optional, but warn if malformed)
if [ -f .env ]; then
    # Check for common .env file issues
    if grep -q "^[^#=]*[[:space:]]" .env 2>/dev/null; then
        echo "Warning: .env file may contain invalid entries (keys with spaces)" >&2
        echo "Consider checking your .env file format (should be KEY=value)" >&2
    fi
fi

# Build if needed
# Check if image exists by trying to inspect it
IMAGE_NAME="hippocli-hippocli"
if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${IMAGE_NAME}:" 2>/dev/null; then
    echo "Building Docker image (this may take a few minutes on first run)..."
    $DOCKER_COMPOSE_CMD build
fi

# Run the command with better error handling
if ! $DOCKER_COMPOSE_CMD run --rm hippocli "$@"; then
    echo "" >&2
    echo "Error: Command failed. Common issues:" >&2
    echo "  1. Make sure Docker is running" >&2
    echo "  2. Check that data/ and config/ directories exist" >&2
    echo "  3. Verify .env file format (if present)" >&2
    echo "  4. Try rebuilding: docker-compose build" >&2
    exit 1
fi
