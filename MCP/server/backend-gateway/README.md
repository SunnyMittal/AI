# Kong Gateway for MCP Servers

This directory contains the Kong Gateway configuration for routing traffic to MCP servers (py-calculator, go-calculator), Arize Phoenix observability platform, and Ollama LLM server.

## Quick Start

1. **Start Kong Gateway**
   ```bash
   docker-compose up -d
   ```

2. **Verify Kong is running**
   ```bash
   curl http://localhost:8001/status
   ```

3. **Access services through Kong**
   - Python Calculator: `http://localhost:8000/py-calculator`
   - Go Calculator: `http://localhost:8000/go-calculator`
   - Phoenix: `http://localhost:8000/phoenix`
   - Ollama: `http://localhost:8000/ollama`

## Prerequisites

Before starting Kong Gateway, ensure your backend services are running:

1. **Python Calculator MCP Server** on port 8100
2. **Go Calculator MCP Server** on port 8200
3. **Arize Phoenix** on port 6006 (locally or Docker)
4. **Ollama** on port 11434 (optional)

## Directory Structure

```
backend-gateway/
├── docker-compose.yml          # Docker Compose configuration
├── declarative/
│   └── kong.yml               # Kong declarative configuration
├── tmp_volume/                # Temporary files (auto-created)
├── prefix_volume/             # Kong runtime data (auto-created)
├── docs/
│   └── backend-gateway.md     # Comprehensive documentation
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Configuration

### Updating Routes

Since Kong is running in read-only mode, you cannot use the Admin API or decK to modify routes. All changes must be made to `declarative/kong.yml`.

After modifying `kong.yml`:
```bash
docker-compose restart kong-gateway
```

### Port Configuration

Default ports exposed by Kong:
- `8000` - Proxy HTTP
- `8443` - Proxy HTTPS
- `8001` - Admin API HTTP
- `8002` - Admin GUI HTTP
- `9080` - Prometheus metrics

## Monitoring

- **Kong Admin GUI**: http://localhost:8002
- **Prometheus Metrics**: http://localhost:9080/metrics
- **Status Endpoint**: http://localhost:8001/status

## Troubleshooting

1. **Kong fails to start**
   - Check logs: `docker-compose logs kong-gateway`
   - Verify `declarative/kong.yml` syntax
   - Ensure backend services are running

2. **502 Bad Gateway**
   - Verify backend service is running on the configured port
   - Check firewall rules
   - Review upstream health checks in logs

3. **Connection refused**
   - Ensure `host.docker.internal` resolves correctly
   - On Linux, you may need to add `--add-host=host.docker.internal:host-gateway`

## Cleanup

```bash
# Stop Kong Gateway
docker-compose down

# Remove volumes
docker-compose down -v
```

Restart docker

```powershell
docker-compose -f D:/AI/MCP/server/backend-gateway/docker-compose.yml restart kong-gateway
```

For detailed documentation, see [backend-gateway.md](docs/backend-gateway.md).
