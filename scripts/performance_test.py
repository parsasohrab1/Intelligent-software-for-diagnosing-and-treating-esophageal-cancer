"""
Performance testing script
"""
import time
import requests
import statistics
from typing import List, Dict
import concurrent.futures


class PerformanceTester:
    """Performance testing utility"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict] = []

    def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        num_requests: int = 100,
        concurrency: int = 10,
        **kwargs
    ) -> Dict:
        """Test endpoint performance"""
        print(f"Testing {endpoint} with {num_requests} requests, {concurrency} concurrent")

        def make_request():
            url = f"{self.base_url}{endpoint}"
            start = time.time()
            try:
                if method == "GET":
                    response = requests.get(url, timeout=30, **kwargs)
                elif method == "POST":
                    response = requests.post(url, timeout=30, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                elapsed = time.time() - start
                return {
                    "status": response.status_code,
                    "elapsed": elapsed,
                    "success": 200 <= response.status_code < 300,
                }
            except Exception as e:
                elapsed = time.time() - start
                return {
                    "status": 0,
                    "elapsed": elapsed,
                    "success": False,
                    "error": str(e),
                }

        # Run concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        self.results = results
        return self.analyze_results()

    def analyze_results(self) -> Dict:
        """Analyze test results"""
        if not self.results:
            return {}

        successful = [r for r in self.results if r.get("success")]
        failed = [r for r in self.results if not r.get("success")]

        elapsed_times = [r["elapsed"] for r in self.results]

        if not elapsed_times:
            return {}

        analysis = {
            "total_requests": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.results) * 100,
            "avg_response_time": statistics.mean(elapsed_times),
            "min_response_time": min(elapsed_times),
            "max_response_time": max(elapsed_times),
            "median_response_time": statistics.median(elapsed_times),
        }

        if len(elapsed_times) > 20:
            analysis["p95_response_time"] = statistics.quantiles(elapsed_times, n=20)[18]
        if len(elapsed_times) > 100:
            analysis["p99_response_time"] = statistics.quantiles(elapsed_times, n=100)[98]

        return analysis

    def print_results(self, analysis: Dict):
        """Print test results"""
        print("\n" + "=" * 50)
        print("Performance Test Results")
        print("=" * 50)
        for key, value in analysis.items():
            if isinstance(value, float):
                print(f"{key}: {value:.3f}")
            else:
                print(f"{key}: {value}")
        print("=" * 50)


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Performance testing")
    parser.add_argument("--url", type=str, default="http://localhost:8000")
    parser.add_argument("--endpoint", type=str, default="/api/v1/health")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)

    args = parser.parse_args()

    tester = PerformanceTester(base_url=args.url)
    analysis = tester.test_endpoint(
        endpoint=args.endpoint,
        num_requests=args.requests,
        concurrency=args.concurrency,
    )

    tester.print_results(analysis)


if __name__ == "__main__":
    main()

