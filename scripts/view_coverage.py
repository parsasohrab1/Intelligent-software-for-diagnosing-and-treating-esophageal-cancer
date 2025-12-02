#!/usr/bin/env python3
"""
Script to view coverage dashboard with live data
"""
import os
import sys
import json
import http.server
import socketserver
import webbrowser
from pathlib import Path

def generate_coverage_report():
    """Generate coverage report if not exists"""
    htmlcov_dir = Path("htmlcov")
    coverage_json = Path("coverage.json")
    
    if not htmlcov_dir.exists() or not (htmlcov_dir / "index.html").exists():
        print("📊 Generating coverage report...")
        os.system("python -m pytest --cov=app --cov-report=html:htmlcov --cov-report=json:coverage.json -q")
    
    if coverage_json.exists():
        with open(coverage_json) as f:
            data = json.load(f)
            totals = data.get("totals", {})
            coverage = totals.get("percent_covered", 0)
            print(f"✅ Coverage: {coverage:.2f}%")
            print(f"   Lines: {totals.get('num_statements', 0)} total")
            print(f"   Covered: {totals.get('covered_lines', 0)}")
            print(f"   Missing: {totals.get('missing_lines', 0)}")

def serve_dashboard(port=8000):
    """Serve coverage dashboard"""
    htmlcov_dir = Path("htmlcov")
    
    if not htmlcov_dir.exists():
        print("❌ Coverage report not found. Generating...")
        generate_coverage_report()
    
    os.chdir(str(htmlcov_dir))
    
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), Handler)
    
    url = f"http://localhost:{port}"
    print(f"\n{'='*50}")
    print(f"📊 Coverage Dashboard")
    print(f"{'='*50}")
    print(f"🌐 URL: {url}")
    print(f"📁 Directory: {htmlcov_dir.absolute()}")
    print(f"{'='*50}\n")
    
    try:
        webbrowser.open(url)
        print("✅ Dashboard opened in browser")
        print("Press Ctrl+C to stop\n")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped")
        httpd.shutdown()

if __name__ == "__main__":
    generate_coverage_report()
    serve_dashboard()

