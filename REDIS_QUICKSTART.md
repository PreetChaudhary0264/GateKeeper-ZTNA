# Redis Quick Start Guide

## 🚀 Starting Your ZTNA System with Redis

### Step 1: Rebuild Services (if already running)
```bash
# Stop existing services
docker-compose down

# Rebuild with Redis support
docker-compose up -d --build
```

### Step 2: Verify Redis is Running
```bash
# Check all services
docker-compose ps

# Should see:
# ztna-redis    running    6379/tcp

# Test Redis connection
docker exec -it ztna-redis redis-cli ping
# Expected output: PONG
```

### Step 3: Check Service Logs
```bash
# Auth service should show "✓ Redis connected successfully"
docker logs ztna-auth

# Gateway should show "✓ Redis connected successfully!"
docker logs ztna-gateway
```

### Step 4: Test Redis Functionality

#### Test 1: Rate Limiting
```bash
# Try 6 failed logins (should get rate limited)
for i in {1..6}; do
  curl -X POST http://localhost:8001/login \
    -H "Content-Type: application/json" \
    -d '{"email":"ramesh@company.com","password":"WRONG","device_id":"DEVICE-HR-001"}'
  echo ""
done
```

#### Test 2: Login & Logout
```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ramesh@company.com","password":"pass123","device_id":"DEVICE-HR-001"}' \
  | jq -r '.token')

echo "Token: $TOKEN"

# 2. Access HR Portal (should work)
curl -k https://localhost:8080/hr-portal \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Device-ID: DEVICE-HR-001" \
  -H "X-Device-OS: Windows 11"

# 3. Logout
curl -X POST http://localhost:8001/logout \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOKEN\"}"

# 4. Try to access again (should fail - token blacklisted)
curl -k https://localhost:8080/hr-portal \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Device-ID: DEVICE-HR-001" \
  -H "X-Device-OS: Windows 11"
```

#### Test 3: Run Automated Tests
```bash
# Install Python dependencies (if not already installed)
pip install requests

# Run Redis tests
python test_redis.py
```

### Step 5: Monitor Redis

#### View Redis Keys
```bash
docker exec -it ztna-redis redis-cli

# Inside Redis CLI:
127.0.0.1:6379> KEYS *
127.0.0.1:6379> GET blacklist:YOUR_TOKEN
127.0.0.1:6379> GET failed_login:ramesh@company.com
127.0.0.1:6379> KEYS session:*
127.0.0.1:6379> TTL blacklist:YOUR_TOKEN
127.0.0.1:6379> exit
```

#### Monitor Redis in Real-time
```bash
# Watch Redis commands as they happen
docker exec -it ztna-redis redis-cli MONITOR
```

## 🔧 Troubleshooting

### Redis Not Starting
```bash
# Check Redis logs
docker logs ztna-redis

# Check if port 6379 is already in use
netstat -an | grep 6379

# Restart Redis
docker-compose restart redis
```

### Auth Service Can't Connect to Redis
```bash
# Check network connectivity
docker exec ztna-auth ping ztna-redis

# Check environment variables
docker exec ztna-auth env | grep REDIS

# Restart auth service
docker-compose restart auth-service
```

### Gateway Can't Connect to Redis
```bash
# Check environment variables
docker exec ztna-gateway env | grep REDIS

# Restart gateway
docker-compose restart gateway
```

## 📊 Redis Data Persistence

Your Redis data is stored in a Docker volume:
```bash
# View volumes
docker volume ls | grep redis

# Inspect volume
docker volume inspect ztna_redis_data

# Backup Redis data
docker exec ztna-redis redis-cli BGSAVE
```

## 🧹 Cleanup

### Clear All Redis Data
```bash
docker exec -it ztna-redis redis-cli FLUSHALL
```

### Remove Redis Volume
```bash
# Stop services
docker-compose down

# Remove volume
docker volume rm ztna_redis_data

# Restart
docker-compose up -d
```

## ✅ Success Indicators

Your Redis is working correctly if:

1. ✓ `docker logs ztna-auth` shows "✓ Redis connected successfully"
2. ✓ `docker logs ztna-gateway` shows "✓ Redis connected successfully!"
3. ✓ Failed login attempts are rate limited after 5 tries
4. ✓ Logout invalidates tokens immediately
5. ✓ `python test_redis.py` passes all tests

## 🎯 Next Steps

1. Test logout functionality with your frontend
2. Monitor failed login attempts for security
3. Set up Redis monitoring (optional)
4. Configure Redis backup strategy for production

---

**Your ZTNA system now has production-grade Redis integration! 🎉**
