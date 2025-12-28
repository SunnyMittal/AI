# Backend Gateway Configuration Updates

## Summary of Changes

All configuration files have been updated to ensure **all application traffic routes through Kong Gateway** for centralized monitoring, security, and observability.

---

## Files Updated

### 1. Frontend Client: `D:\AI\MCP\client\py-calculator\.env`

**Changed:**
```env
# BEFORE (Direct connections)
MCP_SERVER_URL=http://127.0.0.1:8000/mcp
OLLAMA_HOST=http://localhost:11434
# Missing: PHOENIX_ENDPOINT

# AFTER (Through Kong Gateway)
MCP_SERVER_URL=http://localhost:8000/py-calculator/mcp
OLLAMA_HOST=http://localhost:8000/ollama
PHOENIX_ENDPOINT=http://localhost:8000/phoenix/v1/traces
PHOENIX_PROJECT_NAME=calculator-frontend
OTEL_SERVICE_NAME=ollama-client
ENVIRONMENT=development
SERVICE_VERSION=1.0.0
```

**Impact:**
- Frontend now routes MCP requests through Kong Gateway
- Ollama LLM requests go through Kong Gateway
- OpenTelemetry traces sent to Phoenix via Kong Gateway

### 2. Python MCP Server: `D:\AI\MCP\server\py-calculator\.env`

**Changed:**
```env
# BEFORE (Direct to Phoenix)
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces

# AFTER (Through Kong Gateway)
PHOENIX_ENDPOINT=http://localhost:8000/phoenix/v1/traces
PHOENIX_METRICS_ENDPOINT=http://localhost:8000/phoenix/v1/metrics
```

**Impact:**
- All telemetry from py-calculator MCP server routes through Kong Gateway

### 3. Go MCP Server: `D:\AI\MCP\server\go-calculator\.env`

**Changed:**
```env
# BEFORE (Direct to Phoenix, incomplete path)
PHOENIX_ENDPOINT=http://localhost:6006

# AFTER (Through Kong Gateway)
PHOENIX_ENDPOINT=http://localhost:8000/phoenix/v1/traces
```

**Impact:**
- All telemetry from go-calculator routes through Kong Gateway
- Fixed missing `/v1/traces` path

### 4. Frontend Client Template: `D:\AI\MCP\client\py-calculator\.env.example`

**Changed:**
- Updated to match the corrected `.env` file
- Serves as template for new deployments

---

## Architecture Change

### Before (Incorrect - Direct Connections)
```
┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Phoenix   │
│   Client    │     │    :6006    │
└─────────────┘     └─────────────┘
                          ▲
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
  ┌──────────┐                        ┌──────────┐
  │Py-Calc   │                        │Go-Calc   │
  │  :8100   │                        │  :8200   │
  └──────────┘                        └──────────┘

  ❌ All services send telemetry directly to Phoenix
  ❌ No centralized monitoring
  ❌ No rate limiting on telemetry
```

### After (Correct - Through Kong Gateway)
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│    Kong     │────▶│   Phoenix   │
│   Client    │     │   Gateway   │     │    :6006    │
└─────────────┘     │    :8000    │     └─────────────┘
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
  ┌──────────┐       ┌──────────┐      ┌──────────┐
  │Py-Calc   │       │Go-Calc   │      │  Ollama  │
  │  :8100   │       │  :8200   │      │  :11434  │
  └──────────┘       └──────────┘      └──────────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
              All telemetry to Kong:8000

  ✅ All services route through Kong Gateway
  ✅ Centralized monitoring and logging
  ✅ Rate limiting protection
  ✅ Single point for security policies
```

---

## Next Steps

### 1. Start Kong Gateway (if not running)

```powershell
cd D:\AI\MCP\server\backend-gateway
docker-compose up -d
```

Wait 30 seconds for Kong to fully start.

### 2. Verify Kong is Running

```powershell
# Check Kong status
curl http://localhost:8001/status

# Check Kong routes
curl http://localhost:8000/py-calculator/health
curl http://localhost:8000/go-calculator/
curl http://localhost:8000/ollama/api/version
```

### 3. Restart Backend Services

Since `.env` files were updated, restart all backend services to load new configuration:

**Python MCP Server:**
```powershell
cd D:\AI\MCP\server\py-calculator
# Stop current process (Ctrl+C if running)
# Restart with:
fastmcp run calculator/server.py --transport streamable-http --port 8100
```

**Go Calculator Server:**
```powershell
cd D:\AI\MCP\server\go-calculator
# Stop current process (Ctrl+C if running)
# Restart with:
go run cmd/server/main.go
```

**Frontend Client:**
```powershell
cd D:\AI\MCP\client\py-calculator
# Stop current process (Ctrl+C if running)
# Restart with:
uvicorn app.api.main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Run Verification Script

```powershell
cd D:\AI\MCP\server\backend-gateway
.\verify-setup.ps1
```

This script will verify:
- ✓ All backend services are running
- ✓ Kong Gateway is running and healthy
- ✓ All routes through Kong are working
- ✓ Configuration files use Kong Gateway endpoints
- ✓ Upstream health checks are passing

### 5. Test Telemetry Flow

1. **Open Phoenix UI:** http://localhost:6006
2. **Make a test request** through the frontend: http://localhost:8001
3. **Verify traces appear** in Phoenix with:
   - Service names: `ollama-client`, `py-calculator`, `go-calculator`
   - Project names: `calculator-frontend`, `py-calculator`, `go-calculator`
4. **Check Kong logs** for telemetry traffic:
   ```powershell
   docker logs -f kong-gateway-readonly
   ```

---

## Verification Checklist

- [ ] Kong Gateway is running (port 8000, 8001, 8002, 9080)
- [ ] All backend services restarted with new config
- [ ] `verify-setup.ps1` script passes all checks
- [ ] Can access services through Kong routes
- [ ] Telemetry appears in Phoenix UI
- [ ] Traces show correct service and project names

---

## Benefits of This Architecture

### Centralized Monitoring
- All traffic visible in Kong logs and metrics
- Single point to monitor all API and telemetry traffic

### Security
- Rate limiting prevents telemetry floods
- Single point for authentication and authorization
- CORS policies enforced at gateway level

### Observability
- Kong metrics show telemetry pipeline health
- Prometheus metrics available at http://localhost:9080/metrics
- Request/response logging for debugging

### Scalability
- Easy to add load balancing across multiple Phoenix instances
- Can scale backend services independently
- Kong handles connection pooling and health checks

### Consistency
- Same routing pattern for all services
- Easier to manage and troubleshoot
- Clear separation of concerns

---

## Troubleshooting

### Kong Not Starting

```powershell
# Check logs
docker-compose logs kong-gateway

# Validate kong.yml
docker run --rm -v "$PWD/declarative:/kong/declarative" kong/kong-gateway:3.13.0.0 kong config parse /kong/declarative/kong.yml

# Recreate container
docker-compose down -v
docker-compose up -d
```

### Services Can't Reach Kong

```powershell
# Verify Kong is listening
netstat -an | findstr "8000"

# Check Kong routes
curl http://localhost:8001/routes

# Test connectivity
curl -v http://localhost:8000/phoenix/v1/traces
```

### Telemetry Not Appearing in Phoenix

1. **Verify Phoenix is running:** http://localhost:6006
2. **Check Kong can reach Phoenix:**
   ```powershell
   curl http://localhost:8000/phoenix/
   ```
3. **Verify .env files are correct:**
   ```powershell
   .\verify-setup.ps1
   ```
4. **Check application logs** for telemetry initialization messages
5. **Restart services** after .env changes

---

## Documentation Reference

For complete documentation, see:
- `docs/backend-gateway.md` - Full Kong Gateway documentation
- `README.md` - Quick start guide
- `verify-setup.ps1` - Verification script

---

**Last Updated:** 2025-12-27
**Status:** ✅ All services configured to route through Kong Gateway
