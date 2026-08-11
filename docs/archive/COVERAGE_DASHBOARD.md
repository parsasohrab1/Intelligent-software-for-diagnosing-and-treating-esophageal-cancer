# Coverage Dashboard - INEsCape

## 📊 Coverage Summary

### Live Dashboard
- **HTML Report:** `htmlcov/index.html` (opened in browser)
- **HTTP Server:** http://localhost:8000 (running in background)
- **JSON Report:** `coverage.json`

## 🎯 Coverage Goals

- **Current Target:** 50%
- **Long-term Target:** 80%
- **Critical Paths:** > 90%

## 📈 Coverage by Module

### High Coverage (>80%)
- `app/core/config.py`: ~95%
- `app/services/synthetic_data_generator.py`: ~90%
- `app/services/data_validator.py`: ~79%

### Medium Coverage (40-80%)
- `app/core/database.py`: ~60%
- `app/core/mongodb.py`: ~80%
- `app/core/redis_client.py`: ~70%

### Low Coverage (<40%)
- `app/services/cds/`: 11-24%
- `app/services/data_collectors/`: 18-23%
- `app/services/ml_models/`: 28-34%
- `app/api/v1/endpoints/`: 30-40%

## 🔧 Running Coverage Dashboard

### Generate and View Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html:htmlcov --cov-report=term

# Open in browser
# Windows:
start htmlcov/index.html

# Or serve via HTTP
python -m http.server 8000 --directory htmlcov
```

### Live Monitoring

```bash
# Run tests with live coverage
pytest --cov=app --cov-report=term-missing -v

# Watch mode (requires pytest-watch)
ptw -- --cov=app --cov-report=term-missing
```

## 📝 Coverage Improvements

### Recently Added
- ✅ MongoDB mocks in `tests/conftest.py`
- ✅ PostgreSQL mocks in `tests/conftest.py`
- ✅ Redis mocks in `tests/conftest.py`
- ✅ Model registry tests with mocks
- ✅ ML models tests with proper fixtures
- ✅ Data services tests with mocks

### Next Steps
1. Add tests for CDS services
2. Add tests for data collectors
3. Add tests for API endpoints
4. Add integration tests with mocks
5. Add E2E tests with test database

## 🚀 Quick Commands

```bash
# Quick coverage check
pytest --cov=app --cov-report=term -q

# Full coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# Coverage for specific module
pytest --cov=app.services.ml_models --cov-report=term-missing

# Coverage threshold (fail if below 50%)
pytest --cov=app --cov-fail-under=50
```

## 📊 Test Statistics

- **Total Tests:** 107
- **Passing:** 76
- **Failing:** 31 (mostly integration/E2E requiring services)
- **Skipped:** 5
- **Coverage:** ~40-50% (target: 50%)

## 🔍 Viewing Coverage

1. **HTML Report:** Open `htmlcov/index.html` in browser
2. **Terminal:** Run `pytest --cov=app --cov-report=term-missing`
3. **Live Server:** http://localhost:8000 (if running)

## 📌 Notes

- Some tests require Docker services (PostgreSQL, MongoDB, Redis)
- Integration tests may fail if services are not running
- Use mocks for unit tests to avoid service dependencies
- Coverage increases as more tests are added

