# Troubleshooting Guide

## Common Issues and Solutions

### Issue: "Command failed" or "Cannot connect to Docker"

**Symptoms:**
- Error messages about Docker daemon
- Commands fail immediately

**Solutions:**
1. Make sure Docker is running:
   ```bash
   docker ps
   ```
   If this fails, start Docker Desktop or Docker daemon

2. Check Docker permissions:
   ```bash
   # On Linux, you may need to add your user to docker group
   sudo usermod -aG docker $USER
   # Then log out and back in
   ```

### Issue: ".env file errors" or "key cannot contain a space"

**Symptoms:**
- Error: `failed to read .env: line X: key cannot contain a space`

**Solutions:**
1. Check your `.env` file format - it should contain lines like:
   ```
   KEY=value
   ```
   Not:
   ```
   KEY WITH SPACE=value  # WRONG
   ```

2. If you don't need a `.env` file, you can delete it or rename it:
   ```bash
   mv .env .env.backup
   ```

3. Create a proper `.env` file:
   ```bash
   cat > .env << 'EOF'
   # HippoCLI Environment Variables
   # HIPPOCLI_SESSION_TOKEN=your_token_here
   EOF
   ```

### Issue: "No such file or directory" for data/config

**Symptoms:**
- Errors about missing directories
- Volume mount failures

**Solutions:**
1. Create required directories:
   ```bash
   mkdir -p data/mappings data/json data/csv data/parquet data/sql
   mkdir -p config
   ```

2. Or let the script create them automatically (it should do this)

### Issue: "Image not found" or build failures

**Symptoms:**
- Docker can't find the image
- Build errors

**Solutions:**
1. Rebuild the image:
   ```bash
   docker-compose build
   ```

2. Check Dockerfile syntax:
   ```bash
   docker build -t hippocli-test .
   ```

3. Clear Docker cache and rebuild:
   ```bash
   docker-compose build --no-cache
   ```

### Issue: Script permission denied

**Symptoms:**
- `./scripts/hippocli.sh: Permission denied`

**Solutions:**
1. Make script executable:
   ```bash
   chmod +x scripts/hippocli.sh
   ```

2. Or use directly:
   ```bash
   bash scripts/hippocli.sh status
   ```

### Issue: "docker-compose" vs "docker compose"

**Symptoms:**
- Command not found errors
- Version compatibility issues

**Solutions:**
1. Check which version you have:
   ```bash
   docker compose version  # Newer Docker Desktop
   docker-compose version  # Older installations
   ```

2. Use the wrapper script which handles both automatically

3. Or create an alias:
   ```bash
   # For newer Docker
   alias docker-compose='docker compose'
   ```

### Issue: Container exits immediately

**Symptoms:**
- Container starts and stops right away
- No output

**Solutions:**
1. Check if you're passing a command:
   ```bash
   # Wrong - no command
   docker-compose run --rm hippocli
   
   # Correct - with command
   docker-compose run --rm hippocli status
   ```

2. For interactive mode, make sure to use `-it`:
   ```bash
   docker-compose run --rm -it hippocli shell start
   ```

### Issue: Data not persisting

**Symptoms:**
- Files disappear after container stops
- Changes not saved

**Solutions:**
1. Check volume mounts in `docker-compose.yml`:
   ```yaml
   volumes:
     - ./data:/app/data
   ```

2. Verify directories exist on host:
   ```bash
   ls -la data/
   ```

3. Check file permissions:
   ```bash
   ls -la data/json/
   ```

## Getting Help

If you're still having issues:

1. Check Docker logs:
   ```bash
   docker-compose logs hippocli
   ```

2. Run with verbose output:
   ```bash
   docker-compose run --rm hippocli --help
   ```

3. Verify installation:
   ```bash
   docker-compose run --rm hippocli status
   ```

4. Check system requirements:
   - Docker Desktop 4.0+ or Docker Engine 20.10+
   - At least 2GB free disk space
   - Internet connection for first build
