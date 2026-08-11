# راهنمای Testing - INEsCape

## 🧪 انواع تست‌ها

### 1. Unit Tests
تست‌های واحد برای functions و classes

```bash
pytest tests/ -m unit -v
```

### 2. Integration Tests
تست‌های integration برای API endpoints

```bash
pytest tests/integration/ -v
```

### 3. End-to-End Tests
تست‌های E2E برای complete workflows

```bash
pytest tests/e2e/ -v
```

### 4. Performance Tests
تست‌های performance

```bash
pytest tests/performance/ -m performance -v
```

### 5. Security Tests
تست‌های امنیتی

```bash
pytest tests/security/ -m security -v
```

### 6. Usability Tests
تست‌های usability

```bash
pytest tests/usability/ -m usability -v
```

## 🚀 اجرای تست‌ها

### تمام تست‌ها

```bash
# Run all tests
pytest

# With verbose output
pytest -v

# Stop on first failure
pytest -x

# Run specific test file
pytest tests/test_health.py -v
```

### با Coverage

```bash
# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# View HTML report
# Open htmlcov/index.html in browser
```

### با Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only fast tests (exclude slow)
pytest -m "not slow"
```

## 📊 Coverage Report

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View report
# Open htmlcov/index.html
```

### Coverage Goals

- **Overall:** > 80%
- **Critical paths:** > 90%
- **Security:** 100%

## 🔧 Test Configuration

فایل `pytest.ini` شامل:
- Test paths
- Markers
- Coverage settings
- Output options

## 📝 نوشتن تست جدید

### مثال Unit Test

```python
def test_function_name():
    """Test description"""
    # Arrange
    input_value = 10
    
    # Act
    result = function_to_test(input_value)
    
    # Assert
    assert result == expected_value
```

### مثال Integration Test

```python
def test_api_endpoint(client):
    """Test API endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## 🐛 Troubleshooting

### Import errors

```bash
# Install missing dependencies
pip install -r requirements.txt
```

### Database connection errors

```bash
# Make sure services are running
docker-compose up -d
python scripts/check_services.py
```

### Coverage too low

```bash
# Run specific tests to increase coverage
pytest tests/test_health.py --cov=app
```

## 📈 Test Results

### Current Status

- ✅ Unit tests: Passing
- ✅ Integration tests: Passing
- ⚠️ Coverage: 30% (Target: 80%)

### Improving Coverage

1. Add more unit tests
2. Test edge cases
3. Test error handling
4. Test all API endpoints

## 🎯 Best Practices

1. **Write tests first** (TDD)
2. **Test edge cases**
3. **Keep tests fast**
4. **Use fixtures**
5. **Mock external dependencies**
6. **Test error handling**

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**برای اجرای تست‌ها:** `pytest -v`

