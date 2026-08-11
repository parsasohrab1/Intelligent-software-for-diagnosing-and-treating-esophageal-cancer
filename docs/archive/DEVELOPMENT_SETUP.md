# راهنمای راه‌اندازی محیط Development

## 🚀 راه‌اندازی سریع

### گام 1: راه‌اندازی Docker Desktop

**Windows:**
1. Docker Desktop را باز کنید
2. منتظر بمانید تا Docker engine شروع شود
3. بررسی کنید که Docker در حال اجرا است

```bash
docker ps
```

### گام 2: راه‌اندازی Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### گام 3: Setup Development Environment

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env file (if not exists)
# Copy from .env.example or create manually

# Initialize database
python scripts/init_database.py

# Create admin user
python scripts/create_admin_user.py \
  --username admin \
  --email admin@example.com \
  --password admin123
```

### گام 4: Start Development Server

```bash
# Option 1: Using script
python scripts/run_server.py

# Option 2: Direct uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 3: With auto-reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### گام 5: Start Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

## 🔧 Development Tools

### Hot Reload

Server با `--reload` flag به صورت خودکار reload می‌شود وقتی فایل‌ها تغییر می‌کنند.

### API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_health.py -v

# Watch mode (requires pytest-watch)
ptw
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Quality

```bash
# Format code
black app/ scripts/

# Lint
flake8 app/

# Type check
mypy app/
```

## 🐛 Troubleshooting

### Docker not running

```bash
# Start Docker Desktop manually
# Then check:
docker ps
```

### Port already in use

```bash
# Find process using port
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <PID> /F

# Or change port in .env
API_PORT=8001
```

### Database connection error

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart PostgreSQL
docker-compose restart postgres

# Check connection
python scripts/test_db_connection.py
```

### Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
python -c "import sys; print(sys.path)"
```

## 📝 Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code
- Add tests
- Update documentation

### 3. Test

```bash
pytest
pytest --cov=app
```

### 4. Commit

```bash
git add .
git commit -m "feat: your feature description"
```

### 5. Push

```bash
git push origin feature/your-feature-name
```

## 🎯 Development Checklist

- [ ] Docker Desktop running
- [ ] Services started (`docker-compose up -d`)
- [ ] Database initialized
- [ ] Admin user created
- [ ] Server running
- [ ] Tests passing
- [ ] API docs accessible

## 🔗 Useful Commands

```bash
# Check services
python scripts/check_services.py

# Generate synthetic data
python scripts/generate_synthetic_data.py --n-patients 100

# Train model
python scripts/train_model.py --data data.csv --target has_cancer

# Monitor system
python scripts/monitor_system.py --interval 60

# Load test
python scripts/load_test.py --url http://localhost:8000
```

## 📚 Resources

- [Quick Start](QUICK_START_MVP.md)
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Architecture](ARCHITECTURE.md)

---

**Happy Coding!** 🚀

