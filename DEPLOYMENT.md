# Deployment Guide

## Production Deployment

### Prerequisites

- Docker and Docker Compose
- Domain name (optional, for SSL)
- SSL certificates (for HTTPS)

### Environment Variables

Create a `.env.prod` file:

```env
# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Database
POSTGRES_PASSWORD=secure-postgres-password
MONGODB_PASSWORD=secure-mongodb-password
REDIS_PASSWORD=secure-redis-password

# Monitoring
GRAFANA_PASSWORD=secure-grafana-password

# External APIs (if needed)
TCGA_API_KEY=your-tcga-key
GEO_API_KEY=your-geo-key
KAGGLE_USERNAME=your-kaggle-username
KAGGLE_KEY=your-kaggle-key
```

### Deployment Steps

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer
   ```

2. **Set environment variables**
   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with your values
   ```

3. **Build and start services**
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
   ```

4. **Initialize database**
   ```bash
   docker-compose -f docker-compose.prod.yml exec app python scripts/init_database.py
   ```

5. **Create admin user**
   ```bash
   docker-compose -f docker-compose.prod.yml exec app python scripts/create_admin_user.py \
     --username admin \
     --email admin@example.com \
     --password secure_password
   ```

6. **Verify deployment**
   ```bash
   curl http://localhost/api/v1/health
   ```

### SSL Configuration

1. **Obtain SSL certificates** (Let's Encrypt recommended)
2. **Place certificates** in `nginx/ssl/`:
   - `cert.pem` - Certificate
   - `key.pem` - Private key

3. **Update nginx.conf** to enable HTTPS server block

4. **Restart nginx**:
   ```bash
   docker-compose -f docker-compose.prod.yml restart nginx
   ```

### Monitoring

- **Grafana**: http://localhost:3001 (default: admin/admin)
- **Prometheus**: http://localhost:9090

### Scaling

To scale the application:

```bash
docker-compose -f docker-compose.prod.yml up -d --scale app=4
```

### Backup

#### Database Backup

```bash
# PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U inescape_user inescape > backup.sql

# MongoDB
docker-compose -f docker-compose.prod.yml exec mongodb mongodump --out /backup
```

#### Restore

```bash
# PostgreSQL
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U inescape_user inescape < backup.sql

# MongoDB
docker-compose -f docker-compose.prod.yml exec mongodb mongorestore /backup
```

### Updates

1. **Pull latest changes**
   ```bash
   git pull
   ```

2. **Rebuild and restart**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

3. **Run migrations** (if any)
   ```bash
   docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
   ```

### Troubleshooting

#### Check logs
```bash
docker-compose -f docker-compose.prod.yml logs -f app
```

#### Check service status
```bash
docker-compose -f docker-compose.prod.yml ps
```

#### Restart service
```bash
docker-compose -f docker-compose.prod.yml restart <service-name>
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- kubectl configured
- Helm (optional)

### Deploy with kubectl

```bash
kubectl apply -f k8s/
```

### Deploy with Helm

```bash
helm install inescape ./helm/inescape
```

## Performance Tuning

### Application

- Adjust worker count in `Dockerfile.prod` (currently 4)
- Enable caching in Redis
- Optimize database queries

### Database

- Tune PostgreSQL settings
- Add appropriate indexes
- Configure connection pooling

### Nginx

- Adjust worker processes
- Tune buffer sizes
- Configure rate limiting

## Security Checklist

- [ ] Change all default passwords
- [ ] Set strong SECRET_KEY
- [ ] Set ENCRYPTION_KEY
- [ ] Enable HTTPS
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up monitoring alerts
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Access control review

