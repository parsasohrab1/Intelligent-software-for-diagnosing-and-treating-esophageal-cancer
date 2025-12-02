# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- Domain name (optional)
- SSL certificates (for HTTPS)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd Intelligent-software-for-diagnosing-and-treating-esophageal-cancer
```

### 2. Configure Environment

```bash
cp .env.example .env.prod
# Edit .env.prod with your values
```

### 3. Deploy

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### 4. Initialize

```bash
# Initialize database
docker-compose -f docker-compose.prod.yml exec app python scripts/init_database.py

# Create admin user
docker-compose -f docker-compose.prod.yml exec app python scripts/create_admin_user.py \
  --username admin \
  --email admin@example.com \
  --password secure_password
```

### 5. Verify

```bash
curl http://localhost/api/v1/health
```

## Production Checklist

- [ ] All environment variables set
- [ ] SSL certificates configured
- [ ] Database backups scheduled
- [ ] Monitoring configured
- [ ] Logging configured
- [ ] Security audit completed
- [ ] Performance testing completed
- [ ] Documentation reviewed

## Scaling

### Horizontal Scaling

```bash
docker-compose -f docker-compose.prod.yml up -d --scale app=4
```

### Database Scaling

- Use read replicas for PostgreSQL
- Shard MongoDB if needed
- Use Redis cluster for high availability

## Monitoring

- **Grafana:** http://localhost:3001
- **Prometheus:** http://localhost:9090

## Backup and Recovery

See `DEPLOYMENT.md` for detailed backup procedures.

## Troubleshooting

See main `DEPLOYMENT.md` for troubleshooting guide.

