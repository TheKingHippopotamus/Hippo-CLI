#!/bin/bash
# HippoCLI Quick Start Script
# Gets you up and running with your first ticker in 3 steps

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              HippoCLI Quick Start Guide                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if installed
if ! docker images | grep -q "hippocli"; then
    echo -e "${YELLOW}First time setup detected. Running installation...${NC}"
    ./scripts/install.sh
    echo ""
fi

# Get ticker from user
if [ -z "$1" ]; then
    echo -e "${BLUE}Enter a ticker symbol to get started (e.g., AAPL, MSFT, GOOGL):${NC}"
    read -r TICKER
    TICKER=$(echo "$TICKER" | tr '[:lower:]' '[:upper:]' | tr -d '[:space:]')
else
    TICKER=$(echo "$1" | tr '[:lower:]' '[:upper:]' | tr -d '[:space:]')
fi

if [ -z "$TICKER" ]; then
    echo -e "${YELLOW}No ticker provided. Exiting.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Setting up ${GREEN}$TICKER${BLUE}...${NC}"
echo ""

# Run setup
if ./scripts/hippocli.sh setup "$TICKER"; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Success! 🎉                             ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}What's next?${NC}"
    echo -e "  ${GREEN}./scripts/hippocli.sh status${NC}       # View project status"
    echo -e "  ${GREEN}./scripts/hippocli.sh list${NC}        # List all tickers"
    echo -e "  ${GREEN}./scripts/hippocli.sh analytics $TICKER${NC}  # Run analytics"
    echo -e "  ${GREEN}./scripts/hippocli.sh shell start${NC}  # Interactive mode"
    echo ""
else
    echo ""
    echo -e "${YELLOW}Setup encountered issues. Check the output above for details.${NC}"
    echo -e "${BLUE}For help, see: TROUBLESHOOTING.md${NC}"
    exit 1
fi
