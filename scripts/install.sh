#!/bin/bash
# HippoCLI Installation Script
# Automatically sets up the environment for first-time users

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         HippoCLI Installation & Setup Script            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${YELLOW}[1/5] Checking prerequisites...${NC}"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "  ${GREEN}✓${NC} Docker found: $DOCKER_VERSION"
    
    # Check if Docker is running
    if docker ps &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Docker is running"
    else
        echo -e "  ${RED}✗${NC} Docker is not running. Please start Docker Desktop."
        exit 1
    fi
else
    echo -e "  ${RED}✗${NC} Docker is not installed"
    echo -e "  ${YELLOW}Please install Docker Desktop from: https://www.docker.com/products/docker-desktop${NC}"
    exit 1
fi

# Check docker-compose
if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    COMPOSE_VERSION=$(docker compose version)
    echo -e "  ${GREEN}✓${NC} Docker Compose found: $COMPOSE_VERSION"
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "  ${GREEN}✓${NC} Docker Compose found: $COMPOSE_VERSION"
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo -e "  ${RED}✗${NC} Docker Compose is not available"
    exit 1
fi

# Step 2: Create required directories
echo -e "\n${YELLOW}[2/5] Creating required directories...${NC}"
mkdir -p data/mappings data/json data/csv data/parquet data/sql
mkdir -p config
echo -e "  ${GREEN}✓${NC} Directories created"

# Step 3: Setup .env file
echo -e "\n${YELLOW}[3/5] Setting up .env file...${NC}"
if [ -f .env ]; then
    # Check if .env is valid
    if grep -q "^[^#=]*[[:space:]]" .env 2>/dev/null; then
        echo -e "  ${YELLOW}⚠${NC}  .env file exists but may have issues"
        echo -e "  ${YELLOW}   Creating backup and new .env file...${NC}"
        mv .env .env.backup.$(date +%Y%m%d_%H%M%S)
        cat > .env << 'ENVEOF'
# HippoCLI Environment Variables
# Copy this file and adjust values as needed

# Optional: Session token for API authentication
# HIPPOCLI_SESSION_TOKEN=your_session_token_here

# Optional: Override base URL
# HIPPOCLI_BASE_URL=https://compoundeer.com/api/trpc/company.getByTicker

# Optional: Request timeout (seconds)
# HIPPOCLI_REQUEST_TIMEOUT=30

# Optional: Max retries
# HIPPOCLI_MAX_RETRIES=3

# Optional: Concurrency level
# HIPPOCLI_CONCURRENCY=4
ENVEOF
        echo -e "  ${GREEN}✓${NC} New .env file created (old one backed up)"
    else
        echo -e "  ${GREEN}✓${NC} .env file exists and looks valid"
    fi
else
    cat > .env << 'ENVEOF'
# HippoCLI Environment Variables
# Copy this file and adjust values as needed

# Optional: Session token for API authentication
# HIPPOCLI_SESSION_TOKEN=your_session_token_here

# Optional: Override base URL
# HIPPOCLI_BASE_URL=https://compoundeer.com/api/trpc/company.getByTicker

# Optional: Request timeout (seconds)
# HIPPOCLI_REQUEST_TIMEOUT=30

# Optional: Max retries
# HIPPOCLI_MAX_RETRIES=3

# Optional: Concurrency level
# HIPPOCLI_CONCURRENCY=4
ENVEOF
    echo -e "  ${GREEN}✓${NC} .env file created"
fi

# Step 4: Make scripts executable
echo -e "\n${YELLOW}[4/5] Setting up scripts...${NC}"
chmod +x scripts/hippocli.sh 2>/dev/null || true
chmod +x scripts/install.sh 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} Scripts are executable"

# Step 5: Build Docker image
echo -e "\n${YELLOW}[5/5] Building Docker image (this may take a few minutes)...${NC}"
echo -e "  ${BLUE}This is a one-time setup. Future runs will be faster.${NC}"
if $DOCKER_COMPOSE_CMD build; then
    echo -e "  ${GREEN}✓${NC} Docker image built successfully"
else
    echo -e "  ${RED}✗${NC} Docker build failed"
    echo -e "  ${YELLOW}Try running: docker-compose build --no-cache${NC}"
    exit 1
fi

# Final verification
echo -e "\n${YELLOW}Verifying installation...${NC}"
if $DOCKER_COMPOSE_CMD run --rm hippocli --help &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Installation verified successfully!"
else
    echo -e "  ${YELLOW}⚠${NC}  Verification had issues, but installation may still work"
fi

# Success message
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Installation Complete! 🎉                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Quick Start:${NC}"
echo -e "  ${GREEN}./scripts/hippocli.sh status${NC}          # Check status"
echo -e "  ${GREEN}./scripts/hippocli.sh setup AAPL${NC}     # Setup your first ticker"
echo -e "  ${GREEN}./scripts/hippocli.sh shell start${NC}    # Interactive mode"
echo ""
echo -e "${BLUE}Need help?${NC}"
echo -e "  See README.md or TROUBLESHOOTING.md"
echo ""
