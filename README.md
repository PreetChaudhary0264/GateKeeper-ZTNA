# Zero Trust Network Access (ZTNA) System

A production-ready Zero Trust Network Access implementation with **SSL-level mTLS**, role-based access control, device trust verification, and comprehensive audit logging.

## 🔒 Security Features

- **Mutual TLS (mTLS)** - SSL-level client certificate verification using Nginx
- **JWT Authentication** - Secure token-based authentication
- **Role-Based Access Control (RBAC)** - Fine-grained authorization
- **Device Trust** - Device ID and OS verification
- **Redis Integration** - Token blacklisting, rate limiting, session tracking
- **Audit Logging** - Complete access tracking with PostgreSQL
- **Network Isolation** - Docker container segmentation
- **Zero Trust Architecture** - Never trust, always verify

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTPS + JWT
       ▼
┌─────────────────┐
│  ZTNA Gateway   │ ← Go-based, mTLS client
│   (Port 8080)   │
└────────┬────────┘
         │
    ┌────┴────┬────────┬─────────┬─────────┐
    │         │        │         │         │
    ▼         ▼        ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│  Auth  │ │   HR   │ │Finance │ │ Admin  │ │ Redis  │
│Service │ │Service │ │Service │ │Service │ │ Cache  │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
             ▲ Nginx (mTLS server)        ▲ Blacklist
             │ Hypercorn (FastAPI)        │ Sessions
```

## 📋 Prerequisites

- Docker & Docker Compose
- OpenSSL (for certificate generation)
- Python 3.11+ (for testing)
- Go 1.22+ (for gateway development)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd ZTNA
```

### 2. Generate Certificates

```bash
# Generate CA certificate
openssl genrsa -out certs/ca.key 4096
openssl req -new -x509 -days 3650 -key certs/ca.key -out certs/ca.crt \
  -subj "/C=IN/ST=Delhi/L=Delhi/O=ZTNA/OU=CA/CN=ZTNA-CA"

# Generate Gateway certificate
openssl genrsa -out certs/gateway.key 2048
openssl req -new -key certs/gateway.key -out certs/gateway.csr \
  -subj "/C=IN/ST=Delhi/O=ZTNA/CN=ztna-gateway"
openssl x509 -req -in certs/gateway.csr -CA certs/ca.crt -CAkey certs/ca.key \
  -CAcreateserial -out certs/gateway.crt -days 365

# Generate service certificates (HR, Finance, Admin)
for service in hr finance admin; do
  openssl genrsa -out certs/${service}-service.key 2048
  openssl req -new -key certs/${service}-service.key -out certs/${service}-service.csr \
    -subj "/C=IN/ST=Delhi/O=ZTNA/CN=ztna-${service}"
  openssl x509 -req -in certs/${service}-service.csr -CA certs/ca.crt -CAkey certs/ca.key \
    -CAcreateserial -out certs/${service}-service.crt -days 365 \
    -extfile <(printf "subjectAltName=DNS:ztna-${service},DNS:localhost,IP:127.0.0.1")
done
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and change default passwords
```

### 4. Start Services

```bash
docker-compose up -d
```

### 5. Verify mTLS

```bash
# Without client certificate (should fail)
openssl s_client -connect localhost:9001 -CAfile certs/ca.crt

# With client certificate (should succeed)
openssl s_client -connect localhost:9001 \
  -cert certs/gateway.crt \
  -key certs/gateway.key \
  -CAfile certs/ca.crt
```

## 🧪 Testing

### Run Comprehensive Tests

```bash
# Full system test
python test_final.py

# Redis functionality test
python test_redis.py
```

### Test Users

| Email | Password | Role | Device ID |
|-------|----------|------|-----------|
| ramesh@company.com | pass123 | hr | DEVICE-HR-001 |
| priya@company.com | pass456 | finance | DEVICE-FIN-002 |
| admin@company.com | admin789 | admin | DEVICE-ADM-003 |

### Manual API Testing

```bash
# 1. Login
curl -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ramesh@company.com",
    "password": "pass123",
    "device_id": "DEVICE-HR-001"
  }'

# 2. Access HR Portal (use token from step 1)
curl -k https://localhost:8080/hr-portal \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Device-ID: DEVICE-HR-001" \
  -H "X-Device-OS: Windows 11"

# 3. Logout (blacklist token)
curl -X POST http://localhost:8001/logout \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_TOKEN"}'
```

## 📊 Services

| Service | Port | Description |
|---------|------|-------------|
| Gateway | 8080 | Main entry point with mTLS client |
| Auth | 8001 | JWT authentication service |
| HR Portal | 9001 | HR management (mTLS protected) |
| Finance | 9002 | Financial data (mTLS protected) |
| Admin | 9003 | Admin panel (mTLS protected) |
| Audit | 9999 | Audit logging service |
| Redis | 6379 | Token blacklist & session cache |
| Dashboard | 5173 | Web UI for monitoring |

## 🔴 Redis Features

### Token Blacklisting
- Logout functionality adds tokens to Redis blacklist
- Blacklisted tokens are rejected by gateway
- Automatic expiry based on token TTL

### Rate Limiting
- Failed login attempts tracked per user
- 5 failed attempts = 5 minute lockout
- Automatic reset on successful login

### Session Tracking
- Active sessions stored in Redis
- Device tracking per user
- 15-minute session expiry

### Testing Redis

```bash
# Test rate limiting
python test_redis.py

# Check Redis directly
docker exec -it ztna-redis redis-cli
> KEYS *
> GET blacklist:YOUR_TOKEN
> GET failed_login:user@example.com
```

## 🔐 mTLS Implementation

### Architecture

- **Nginx** - SSL-level mTLS enforcement (requests client certificates)
- **Hypercorn** - FastAPI application server (internal)
- **Gateway** - Go-based mTLS client (presents certificate to services)

### Verification

```bash
# Check if server requests client certificate
openssl s_client -connect localhost:9001 -CAfile certs/ca.crt | grep "Acceptable"
# Should show: "Acceptable client certificate CA names"
```

## 📁 Project Structure

```
ZTNA/
├── gateway/              # Go-based API gateway
├── auth-service/         # JWT authentication
├── hr-service/          # HR portal (mTLS)
├── finance-service/     # Finance service (mTLS)
├── admin-service/       # Admin panel (mTLS)
├── audit-service/       # Audit logging
├── dashboard/           # React monitoring UI
├── certs/              # SSL certificates (gitignored)
├── docker-compose.yml  # Service orchestration
└── .env.example        # Environment template
```

## 🛡️ Security Best Practices

1. **Never commit private keys** - Already in .gitignore
2. **Change default passwords** - Update .env file
3. **Rotate certificates** - Regenerate before expiry
4. **Use strong JWT secrets** - Update JWT_SECRET in .env
5. **Redis is mandatory** - Required for token blacklisting and rate limiting
6. **Review audit logs** - Monitor access patterns
7. **Monitor failed logins** - Check Redis for attack patterns

## 🔧 Configuration

### Environment Variables

See `.env.example` for all configuration options.

### Access Policies

Edit `gateway/middleware.go` to modify role-based access rules:

```go
var Policies = map[string][]string{
    "/hr-portal": {"hr", "admin"},
    "/finance":   {"finance", "admin"},
    "/admin":     {"admin"},
}
```

## 📈 Monitoring

Access the dashboard at `http://localhost:5173` to view:
- Real-time access logs
- Service health status
- Access statistics
- Block rate metrics

## 🐛 Troubleshooting

### mTLS Not Working

```bash
# Check if Nginx is requesting client certificates
docker logs ztna-hr

# Verify certificate chain
openssl verify -CAfile certs/ca.crt certs/gateway.crt
```

### Services Not Starting

```bash
# Check logs
docker-compose logs

# Restart specific service
docker-compose restart hr-service
```

### Database Connection Issues

```bash
# Check PostgreSQL health
docker exec ztna-postgres pg_isready -U ztna
```

### Redis Connection Issues

```bash
# Check Redis health
docker exec -it ztna-redis redis-cli ping
# Should return: PONG

# Check Redis logs
docker logs ztna-redis
```

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📧 Support

For issues and questions, please open a GitHub issue.

## 🎯 Roadmap

- [x] Redis integration for token blacklisting
- [x] Rate limiting for failed login attempts
- [x] Session tracking with Redis
- [ ] Multi-factor authentication (MFA)
- [ ] IP-based geofencing
- [ ] Advanced threat detection
- [ ] Kubernetes deployment manifests
- [ ] Prometheus metrics export

---

**Built with ❤️ for Zero Trust Security**
