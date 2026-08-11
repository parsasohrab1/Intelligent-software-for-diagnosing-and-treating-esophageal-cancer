# INEsCape MVP - Deployment Guide

## 🚀 Production Deployment

### Pre-Deployment

1. **Review Checklist**
   ```bash
   # Run go-live checklist
   python scripts/go_live_checklist.py
   ```

2. **Verify Services**
   ```bash
   # Check all services
   python scripts/check_services.py
   ```

3. **Run Tests**
   ```bash
   # Run full test suite
   pytest
   ```

### Deployment Steps

#### Option 1: Docker Compose (Recommended for MVP)

```bash
# 1. Set production environment variables
cp .env.example .env.prod
# Edit .env.prod with production values

# 2. Deploy
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 3. Initialize
docker-compose -f docker-compose.prod.yml exec app python scripts/init_database.py
docker-compose -f docker-compose.prod.yml exec app python scripts/create_admin_user.py \
  --username admin --email admin@example.com --password SecurePassword123

# 4. Verify
curl http://localhost/api/v1/health
```

#### Option 2: Manual Deployment

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start databases
docker-compose up -d postgres mongodb redis

# 3. Initialize database
python scripts/init_database.py

# 4. Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 5. Start frontend (separate terminal)
cd frontend
npm install
npm run build
npm run preview
```

### Post-Deployment

1. **Verify Deployment**
   ```bash
   # Health check
   curl http://localhost:8000/api/v1/health
   
   # Check services
   docker-compose ps
   ```

2. **Monitor System**
   ```bash
   # Start monitoring
   python scripts/monitor_system.py --interval 60
   ```

3. **Check Logs**
   ```bash
   # Application logs
   docker-compose logs -f app
   
   # Database logs
   docker-compose logs -f postgres
   ```

## 🔧 Configuration

### Environment Variables

Required variables in `.env`:

```env
# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Database
POSTGRES_PASSWORD=secure-password
MONGODB_PASSWORD=secure-password
REDIS_PASSWORD=secure-password

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### SSL Configuration

1. Obtain SSL certificates
2. Place in `nginx/ssl/`:
   - `cert.pem`
   - `key.pem`
3. Update `nginx/nginx.conf` to enable HTTPS
4. Restart nginx

## 📊 Monitoring

### Access Dashboards

- **Grafana:** http://localhost:3001
  - Default: admin/admin
  - Change password on first login

- **Prometheus:** http://localhost:9090

### Key Metrics

- System health
- API response times
- Error rates
- Resource usage
- User activity

## 🔄 Updates

### Application Update

```bash
# 1. Pull latest code
git pull

# 2. Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# 3. Run migrations (if any)
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
```

### Database Migration

```bash
# Create migration
docker-compose -f docker-compose.prod.yml exec app alembic revision --autogenerate -m "description"

# Apply migration
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
```

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs app

# Check resources
docker stats

# Restart service
docker-compose restart app
```

### Database Issues

```bash
# Check connection
python scripts/test_db_connection.py

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Performance Issues

```bash
# Check bottlenecks
curl "http://localhost:8000/api/v1/maintenance/performance/bottlenecks" \
  -H "Authorization: Bearer <token>"

# Get recommendations
curl "http://localhost:8000/api/v1/maintenance/performance/recommendations" \
  -H "Authorization: Bearer <token>"
```

## 📦 Backup & Recovery

### Backup

```bash
# PostgreSQL backup
docker-compose exec postgres pg_dump -U inescape_user inescape > backup_$(date +%Y%m%d).sql

# MongoDB backup
docker-compose exec mongodb mongodump --out /backup/$(date +%Y%m%d)
```

### Restore

```bash
# PostgreSQL restore
docker-compose exec -T postgres psql -U inescape_user inescape < backup_20241219.sql

# MongoDB restore
docker-compose exec mongodb mongorestore /backup/20241219
```

## ✅ Deployment Verification

```bash
# Run verification script
python scripts/go_live_checklist.py --url http://localhost:8000

# Expected output:
# ✅ Health Check: System is healthy
# ✅ Database Connection: Connected
# ✅ MongoDB Connection: Connected
# ✅ Redis Connection: Connected
# ✅ API Documentation: Available
# ✅ Environment Variables: All set
```

## 🎯 Success Criteria

- [x] All services running
- [x] Health checks passing
- [x] API accessible
- [x] Frontend accessible
- [x] Database connected
- [x] Monitoring active
- [x] Backups configured

---

**Deployment Complete!** 🎉

