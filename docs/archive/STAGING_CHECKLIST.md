# ✅ Staging Deployment Checklist

## Pre-Deployment

- [ ] `.env.staging` فایل ایجاد شده
- [ ] تمام passwords تغییر کرده‌اند
- [ ] `STAGING_SECRET_KEY` تنظیم شده
- [ ] `STAGING_ENCRYPTION_KEY` تنظیم شده
- [ ] Docker Desktop در حال اجرا است
- [ ] Ports آزاد هستند (8001, 9091, 3002, 9002, 9003)

## Deployment

- [ ] Docker images build شده‌اند
- [ ] Services start شده‌اند
- [ ] Database initialized شده
- [ ] Migrations اجرا شده‌اند
- [ ] Admin user ایجاد شده

## Post-Deployment

- [ ] Health check پاس شده
- [ ] API accessible است (http://localhost:8001)
- [ ] API docs accessible است (http://localhost:8001/docs)
- [ ] Grafana accessible است (http://localhost:3002)
- [ ] Prometheus accessible است (http://localhost:9091)
- [ ] Database connections OK
- [ ] Logs در حال نوشتن هستند

## Testing

- [ ] Unit tests پاس شده
- [ ] Integration tests پاس شده
- [ ] API endpoints کار می‌کنند
- [ ] Authentication کار می‌کند
- [ ] Database operations کار می‌کنند

## Security

- [ ] Passwords قوی هستند
- [ ] Secret keys تغییر کرده‌اند
- [ ] CORS settings صحیح هستند
- [ ] Firewall rules تنظیم شده‌اند
- [ ] SSL/TLS برای production آماده است

## Monitoring

- [ ] Prometheus metrics جمع‌آوری می‌شوند
- [ ] Grafana dashboards کار می‌کنند
- [ ] Alerts تنظیم شده‌اند
- [ ] Logs قابل دسترسی هستند

## Documentation

- [ ] Deployment guide به‌روز است
- [ ] API documentation به‌روز است
- [ ] Runbooks آماده هستند

---

**تاریخ:** ___________  
**تایید شده توسط:** ___________

