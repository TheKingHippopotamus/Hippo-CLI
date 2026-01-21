#!/bin/bash
# HippoCLI Docker Wrapper Script
# Simplifies running HippoCLI commands with Docker Compose

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project directory
cd "$PROJECT_DIR"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "Error: Docker or docker-compose is not installed or not in PATH" >&2
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

# Build if needed (only on first run or if image doesn't exist)
if ! docker images | grep -q "hippocli.*hippocli"; then
    echo "Building Docker image..."
    $DOCKER_COMPOSE_CMD build --quiet
fi

# Run the command
$DOCKER_COMPOSE_CMD run --rm hippocli "$@"
