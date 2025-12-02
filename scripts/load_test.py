"""
Load testing script
"""
import asyncio
import aiohttp
import time
from typing import List, Dict
import statistics


class LoadTester:
    """Simple load testing utility"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict] = []

    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET", **kwargs):
        """Make a single request"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            if method == "GET":
                async with session.get(url, **kwargs) as response:
                    status = response.status
                    await response.read()
            elif method == "POST":
                async with session.post(url, **kwargs) as response:
                    status = response.status
                    await response.read()
            else:
                raise ValueError(f"Unsupported method: {method}")

            elapsed = time.time() - start_time

            return {
                "status": status,
                "elapsed": elapsed,
                "success": 200 <= status < 300,
            }

        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "status": 0,
                "elapsed": elapsed,
                "success": False,
                "error": str(e),
            }

    async def run_load_test(
        self,
        endpoint: str,
        num_requests: int = 100,
        concurrency: int = 10,
        method: str = "GET",
        **kwargs
    ):
        """Run load test"""
        print(f"Running load test: {num_requests} requests, {concurrency} concurrent")
        print(f"Endpoint: {endpoint}")

        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(concurrency)

            async def bounded_request():
                async with semaphore:
                    return await self.make_request(session, endpoint, method, **kwargs)

            tasks = [bounded_request() for _ in range(num_requests)]
            results = await asyncio.gather(*tasks)

        self.results = results
        return self.analyze_results()

    def analyze_results(self) -> Dict:
        """Analyze test results"""
        if not self.results:
            return {}

        successful = [r for r in self.results if r.get("success")]
        failed = [r for r in self.results if not r.get("success")]

        elapsed_times = [r["elapsed"] for r in self.results]

        analysis = {
            "total_requests": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.results) * 100 if self.results else 0,
            "avg_response_time": statistics.mean(elapsed_times) if elapsed_times else 0,
            "min_response_time": min(elapsed_times) if elapsed_times else 0,
            "max_response_time": max(elapsed_times) if elapsed_times else 0,
            "median_response_time": statistics.median(elapsed_times) if elapsed_times else 0,
            "p95_response_time": statistics.quantiles(elapsed_times, n=20)[18] if len(elapsed_times) > 20 else 0,
            "p99_response_time": statistics.quantiles(elapsed_times, n=100)[98] if len(elapsed_times) > 100 else 0,
        }

        return analysis

    def print_results(self, analysis: Dict):
        """Print test results"""
        print("\n" + "=" * 50)
        print("Load Test Results")
        print("=" * 50)
        print(f"Total Requests: {analysis['total_requests']}")
        print(f"Successful: {analysis['successful']}")
        print(f"Failed: {analysis['failed']}")
        print(f"Success Rate: {analysis['success_rate']:.2f}%")
        print(f"\nResponse Times:")
        print(f"  Average: {analysis['avg_response_time']:.3f}s")
        print(f"  Median: {analysis['median_response_time']:.3f}s")
        print(f"  Min: {analysis['min_response_time']:.3f}s")
        print(f"  Max: {analysis['max_response_time']:.3f}s")
        print(f"  P95: {analysis['p95_response_time']:.3f}s")
        print(f"  P99: {analysis['p99_response_time']:.3f}s")
        print("=" * 50)


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Load testing tool")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="Base URL")
    parser.add_argument("--endpoint", type=str, default="/api/v1/health", help="Endpoint to test")
    parser.add_argument("--requests", type=int, default=100, help="Number of requests")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrency level")
    parser.add_argument("--method", type=str, default="GET", help="HTTP method")

    args = parser.parse_args()

    tester = LoadTester(base_url=args.url)
    analysis = await tester.run_load_test(
        endpoint=args.endpoint,
        num_requests=args.requests,
        concurrency=args.concurrency,
        method=args.method,
    )

    tester.print_results(analysis)


if __name__ == "__main__":
    asyncio.run(main())

