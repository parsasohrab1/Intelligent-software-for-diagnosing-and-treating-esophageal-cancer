# معماری سیستم INEsCape

## نمای کلی

INEsCape یک پلتفرم میکروسرویس برای مدیریت و تحلیل داده‌های سرطان مری است که از معماری لایه‌ای استفاده می‌کند.

## معماری لایه‌ای

```
┌─────────────────────────────────────────────────┐
│         Application Layer (Frontend)             │
│  - Web Dashboard (React)                        │
│  - Mobile App (Future)                           │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│            Service Layer (API Gateway)           │
│  - RESTful API (FastAPI)                        │
│  - Authentication & Authorization               │
│  - Rate Limiting                                │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│          Processing Layer (Business Logic)      │
│  - Data Generation Service                      │
│  - Data Collection Service                      │
│  - ML Training Service                          │
│  - CDS Service                                  │
└─────────────────────────────────────────────────┘
                      │
┌─────────────────────────────────────────────────┐
│              Data Layer (Storage)               │
│  - PostgreSQL (Structured Data)                 │
│  - MongoDB (Metadata)                           │
│  - Redis (Cache)                                │
│  - MinIO/S3 (Object Storage)                    │
└─────────────────────────────────────────────────┘
```

## میکروسرویس‌ها

### 1. Data Generation Service
- **مسئولیت:** تولید داده‌های سنتتیک
- **تکنولوژی:** Python, FastAPI
- **پورت:** 8001

### 2. Data Collection Service
- **مسئولیت:** جمع‌آوری داده‌های واقعی از منابع خارجی
- **تکنولوژی:** Python, Celery, Redis
- **پورت:** 8002

### 3. ML Training Service
- **مسئولیت:** آموزش مدل‌های یادگیری ماشین
- **تکنولوژی:** Python, TensorFlow/PyTorch
- **پورت:** 8003

### 4. CDS Service
- **مسئولیت:** سیستم پشتیبانی تصمیم‌گیری بالینی
- **تکنولوژی:** Python, FastAPI
- **پورت:** 8004

### 5. API Gateway
- **مسئولیت:** مسیریابی، احراز هویت، rate limiting
- **تکنولوژی:** FastAPI
- **پورت:** 8000

## پایگاه داده‌ها

### PostgreSQL
- **استفاده:** داده‌های ساختاریافته (patients, clinical data, etc.)
- **Schema:** Relational database با foreign keys

### MongoDB
- **استفاده:** Metadata، logs، unstructured data
- **Collections:** dataset_metadata, audit_logs, etc.

### Redis
- **استفاده:** Caching، session management، task queues
- **Data Types:** Strings, Hashes, Lists, Sets

### MinIO/S3
- **استفاده:** ذخیره فایل‌های بزرگ (images, models, datasets)
- **Buckets:** images, models, datasets

## API Contracts

### RESTful API Design
- **Base URL:** `/api/v1`
- **Authentication:** JWT Bearer Token
- **Response Format:** JSON
- **Error Format:** 
  ```json
  {
    "detail": "Error message",
    "status_code": 400
  }
  ```

### Endpoints

#### Health
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with service status

#### Patients
- `GET /patients` - List patients
- `GET /patients/{id}` - Get patient by ID
- `POST /patients` - Create patient

## Security Architecture

### Authentication Flow
1. User login → JWT token issued
2. Token included in Authorization header
3. Token validated on each request
4. RBAC checks permissions

### Data Protection
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- De-identification for patient data
- Audit logging for all accesses

## Deployment Architecture

### Development
- Docker Compose for local services
- Hot reload enabled
- Debug mode active

### Production
- Kubernetes orchestration
- Horizontal pod autoscaling
- Load balancing
- Service mesh (optional)

## Monitoring & Observability

### Metrics
- Prometheus for metrics collection
- Custom metrics for business logic
- Infrastructure metrics

### Logging
- Structured logging (JSON)
- Centralized log aggregation
- Log levels: DEBUG, INFO, WARNING, ERROR

### Tracing
- Distributed tracing (future)
- Request ID tracking
- Performance monitoring

## Scalability

### Horizontal Scaling
- Stateless services
- Database connection pooling
- Load balancing

### Caching Strategy
- Redis for frequently accessed data
- Cache invalidation policies
- CDN for static assets

## Disaster Recovery

### Backup Strategy
- Daily database backups
- Point-in-time recovery
- Offsite backup storage

### High Availability
- Multi-region deployment (future)
- Database replication
- Failover mechanisms

