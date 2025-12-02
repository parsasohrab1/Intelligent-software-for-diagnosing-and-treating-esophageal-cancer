"""
System monitoring script
"""
import sys
import os
import time
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.maintenance.system_monitor import SystemMonitor
from app.services.maintenance.performance_analyzer import PerformanceAnalyzer


def main():
    parser = argparse.ArgumentParser(description="System monitoring script")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Monitoring interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit",
    )

    args = parser.parse_args()

    monitor = SystemMonitor()
    analyzer = PerformanceAnalyzer()

    print("Starting system monitoring...")
    print(f"Interval: {args.interval} seconds")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            # Collect metrics
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Collecting metrics...")
            metrics = monitor.collect_metrics()

            # Display health
            health = monitor.get_system_health(hours=1)
            print(f"  System Health: {health.get('status', 'unknown')}")
            print(f"  Health Percentage: {health.get('health_percentage', 0):.1f}%")

            # Performance analysis
            perf = analyzer.analyze_api_performance(hours=1)
            if "response_times" in perf:
                rt = perf["response_times"]
                print(f"  Avg Response Time: {rt.get('avg', 0):.3f}s")
                print(f"  P95 Response Time: {rt.get('p95', 0):.3f}s")

            # Bottlenecks
            bottlenecks = analyzer.identify_bottlenecks(days=1)
            if bottlenecks:
                print(f"  Bottlenecks: {len(bottlenecks)}")
                for b in bottlenecks[:3]:
                    print(f"    - {b['endpoint']}: {b['avg_response_time']:.3f}s")

            print()

            if args.once:
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    main()

