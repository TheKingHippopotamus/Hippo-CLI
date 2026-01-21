# Getting Started with HippoCLI

## For Complete Beginners

This guide will get you up and running in **under 5 minutes**, even if you've never used Docker before.

### Step 1: Install Docker (if needed)

**On Mac:**
- Download Docker Desktop from https://www.docker.com/products/docker-desktop
- Install and start Docker Desktop
- Wait for Docker to start (you'll see a whale icon in your menu bar)

**On Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (optional, to avoid sudo)
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

**On Windows:**
- Download Docker Desktop from https://www.docker.com/products/docker-desktop
- Install and start Docker Desktop

### Step 2: Clone and Install

```bash
# Clone the repository
git clone https://github.com/TheKingHippopotamus/Hippo-CLI.git

# Go into the directory
cd Hippo-CLI

# Run the installation script
./scripts/install.sh
```

The installation script will:
- ✅ Check if Docker is installed and running
- ✅ Create all necessary directories
- ✅ Setup configuration files
- ✅ Build the Docker image (this takes 2-5 minutes the first time)
- ✅ Verify everything works

**If you get "Permission denied":**
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

### Step 3: Get Your First Ticker

```bash
# Quick start with Apple (AAPL)
./scripts/quick-start.sh AAPL

# Or choose your own ticker
./scripts/quick-start.sh MSFT
```

This will:
- Download data for the ticker
- Convert it to all formats (CSV, Parquet, SQL)
- Validate the data
- Show you what's next

### Step 4: Explore

```bash
# Check what you have
./scripts/hippocli.sh status

# List all tickers
./scripts/hippocli.sh list

# Run analytics
./scripts/hippocli.sh analytics AAPL

# Try interactive mode
./scripts/hippocli.sh shell start
```

## Common Commands

| What you want to do | Command |
|---------------------|---------|
| Add a new ticker | `./scripts/hippocli.sh setup TICKER` |
| Update all tickers | `./scripts/hippocli.sh update` |
| Check status | `./scripts/hippocli.sh status` |
| List tickers | `./scripts/hippocli.sh list` |
| Run analytics | `./scripts/hippocli.sh analytics TICKER` |
| Interactive mode | `./scripts/hippocli.sh shell start` |

## Troubleshooting

**"Docker not found"**
- Make sure Docker Desktop is installed and running
- Check: `docker ps` should work without errors

**"Permission denied"**
```bash
chmod +x scripts/*.sh
```

**"Build failed"**
```bash
docker-compose build --no-cache
```

**"Command not found"**
- Make sure you're in the Hippo-CLI directory
- Check: `pwd` should show the Hippo-CLI folder

**Still having issues?**
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed help
- Check the [README.md](README.md) for more information

## Next Steps

1. **Add more tickers:**
   ```bash
   ./scripts/hippocli.sh setup GOOGL
   ./scripts/hippocli.sh setup TSLA
   ```

2. **Update your data:**
   ```bash
   ./scripts/hippocli.sh update
   ```

3. **Explore interactive mode:**
   ```bash
   ./scripts/hippocli.sh shell start
   ```

4. **Read the full documentation:**
   - [README.md](README.md) - Complete documentation
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problem solving guide

## Need Help?

- Check the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide
- Read the full [README.md](README.md)
- Open an issue on GitHub if you find a bug

Happy data fetching! 🦛
