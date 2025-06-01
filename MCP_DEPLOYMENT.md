# MCP Server Deployment Guide

✅ **DEPLOYMENT STATUS: READY FOR PRODUCTION**

The alligator.ai MCP Server has been successfully implemented and tested. This guide provides deployment instructions for production use.

## Quick Verification

```bash
# Verify all tests pass
cd /path/to/citation_graph
poetry run python test_mcp_server.py

# Expected: 5/5 tests passed
# ✅ MCP Server Setup & Configuration  
# ✅ CourtListener Tools (Multi-Jurisdiction)
# ✅ Research Workflow Tools  
# ✅ Legal Analysis Tools
# ✅ Full Research Workflow
```

## Claude Desktop Integration

### 1. Configure Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "alligator-ai": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/citation_graph",
      "env": {
        "PYTHONPATH": "/path/to/citation_graph",
        "API_BASE_URL": "http://localhost:8001",
        "DEVELOPMENT_MODE": "true"
      }
    }
  }
}
```

### 2. Start Required Services

```bash
# Start the alligator.ai platform services
cd /path/to/citation_graph
docker compose up -d

# Start the API Gateway
poetry run python start_api.py
```

### 3. Test in Claude Desktop

Example queries to test:

```
Search for recent Supreme Court cases on equal protection and constitutional law
```

```
Analyze the legal authority of Miranda v. Arizona and its precedential value
```

```
Conduct comprehensive research on the constitutional limits of police use of deadly force
```

## Available MCP Tools

| Tool Name | Description | Example Usage |
|-----------|-------------|---------------|
| `search_legal_cases` | Search all U.S. jurisdictions | "Find civil rights cases in the 9th Circuit" |
| `get_case_details` | Detailed case information | "Get full details for case ID 12345" |
| `citation_network_expansion` | Citation-driven discovery | "Find related cases citing Brown v. Board" |
| `conduct_legal_research` | AI research workflows | "Research police qualified immunity doctrine" |
| `semantic_case_search` | Similarity-based search | "Find cases similar to employment discrimination" |
| `analyze_case_authority` | Authority assessment | "Analyze precedential value of Roe v. Wade" |
| `generate_legal_memo` | Professional memos | "Generate memo from research session ABC123" |
| `identify_opposing_arguments` | Opposition research | "Find counterarguments to our position" |

## Production Deployment Options

### Option 1: Docker Container

```dockerfile
# Dockerfile.mcp
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY mcp_server/ ./mcp_server/
COPY services/ ./services/
COPY shared/ ./shared/
COPY api/ ./api/

# Install Python dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only=main

# Expose MCP port
EXPOSE 8000

# Run MCP server
CMD ["python", "-m", "mcp_server.server"]
```

Build and run:
```bash
docker build -f Dockerfile.mcp -t alligator-ai-mcp:latest .
docker run -p 8000:8000 \
  -e API_BASE_URL=http://host.docker.internal:8001 \
  alligator-ai-mcp:latest
```

Claude Desktop config for Docker:
```json
{
  "mcpServers": {
    "alligator-ai": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "-p", "8000:8000", "alligator-ai-mcp:latest"]
    }
  }
}
```

### Option 2: Systemd Service

```ini
# /etc/systemd/system/alligator-ai-mcp.service
[Unit]
Description=alligator.ai MCP Server
After=network.target

[Service]
Type=simple
User=alligator
WorkingDirectory=/opt/alligator-ai/citation_graph
Environment=PYTHONPATH=/opt/alligator-ai/citation_graph
Environment=API_BASE_URL=http://localhost:8001
ExecStart=/opt/alligator-ai/venv/bin/python -m mcp_server.server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable alligator-ai-mcp
sudo systemctl start alligator-ai-mcp
sudo systemctl status alligator-ai-mcp
```

### Option 3: Process Manager (PM2)

```json
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'alligator-ai-mcp',
    script: 'python',
    args: ['-m', 'mcp_server.server'],
    cwd: '/opt/alligator-ai/citation_graph',
    env: {
      PYTHONPATH: '/opt/alligator-ai/citation_graph',
      API_BASE_URL: 'http://localhost:8001',
      NODE_ENV: 'production'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G'
  }]
};
```

Start with PM2:
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## Environment Configuration

### Development Environment
```bash
# .env.development
DEVELOPMENT_MODE=true
API_BASE_URL=http://localhost:8001
LOG_LEVEL=DEBUG
COURTLISTENER_API_TOKEN=  # Optional for anonymous access
```

### Production Environment
```bash
# .env.production
DEVELOPMENT_MODE=false
API_BASE_URL=https://api.alligator.ai
LOG_LEVEL=INFO
COURTLISTENER_API_TOKEN=your_api_token_here
SECRET_KEY=your_production_secret_key
ENABLE_AUTH=true
```

## Performance Optimization

### Connection Pooling
```python
# mcp_server/config.py
class MCPServerSettings(BaseSettings):
    MAX_CONCURRENT_REQUESTS: int = 20
    DEFAULT_REQUEST_TIMEOUT: int = 30
    CONNECTION_POOL_SIZE: int = 10
    MAX_KEEPALIVE_CONNECTIONS: int = 5
```

### Caching
```python
# Add Redis caching for expensive operations
CACHE_TTL: int = 3600  # 1 hour
REDIS_URL: str = "redis://localhost:6379"
```

### Rate Limiting
```python
# Rate limiting per client
RATE_LIMIT_PER_HOUR: int = 1000
RATE_LIMIT_BURST: int = 50
```

## Monitoring and Logging

### Health Check Endpoint
```bash
# Check MCP server health
curl http://localhost:8000/health
```

### Logging Configuration
```python
# mcp_server/config.py
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
ENABLE_REQUEST_LOGGING: bool = True
```

### Metrics Collection
```python
# Add metrics for monitoring
ENABLE_METRICS: bool = True
METRICS_PORT: int = 9090
```

## Security Considerations

### Authentication (Optional)
```python
# Enable JWT authentication for production
ENABLE_AUTH: bool = True
SECRET_KEY: str = "your-secret-key"
API_KEY_HEADER: str = "X-API-Key"
```

### HTTPS/TLS
```bash
# Use HTTPS in production
API_BASE_URL=https://api.alligator.ai
ENABLE_TLS=true
```

### Firewall Rules
```bash
# Allow only necessary ports
sudo ufw allow 8000/tcp  # MCP server
sudo ufw allow 8001/tcp  # API Gateway
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if API Gateway is running
   curl http://localhost:8001/health
   
   # Check if services are up
   docker compose ps
   ```

2. **Permission Denied**
   ```bash
   # Fix file permissions
   chmod +x mcp_server/server.py
   chown -R alligator:alligator /opt/alligator-ai
   ```

3. **Import Errors**
   ```bash
   # Verify PYTHONPATH
   export PYTHONPATH=/path/to/citation_graph
   python -c "import mcp_server; print('OK')"
   ```

4. **Database Connection Issues**
   ```bash
   # Test database connections
   poetry run python test_mcp_server.py --check-db
   ```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
export MCP_DEBUG=true
python -m mcp_server.server
```

### Performance Testing

```bash
# Run performance tests
poetry run python test_mcp_server.py --performance

# Load testing with multiple clients
for i in {1..10}; do
  curl -X POST http://localhost:8000/mcp/tool/search_legal_cases \
    -H "Content-Type: application/json" \
    -d '{"query": "constitutional law test '$i'"}' &
done
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Update Dependencies**
   ```bash
   poetry update
   poetry run python test_mcp_server.py
   ```

2. **Database Maintenance**
   ```bash
   # Clean up old research sessions
   # Optimize database indexes
   # Backup databases
   ```

3. **Log Rotation**
   ```bash
   # Configure logrotate for MCP server logs
   sudo logrotate -f /etc/logrotate.d/alligator-ai-mcp
   ```

### Backup Strategy

```bash
# Backup configuration
tar -czf mcp-config-backup-$(date +%Y%m%d).tar.gz \
  mcp_server/ test_mcp_server.py .env

# Backup databases (separate process)
# Neo4j, ChromaDB, PostgreSQL backups
```

The MCP server is now ready for production deployment and integration with Claude Desktop! 🚀