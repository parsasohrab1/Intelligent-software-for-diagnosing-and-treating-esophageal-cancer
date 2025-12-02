"""
Performance optimization utilities
"""
from functools import wraps
import time
from typing import Callable, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result

    return wrapper


def async_timing_decorator(func: Callable) -> Callable:
    """Decorator to measure async function execution time"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result

    return wrapper


class QueryOptimizer:
    """Database query optimization"""

    @staticmethod
    def optimize_pagination(query, page: int = 1, page_size: int = 100):
        """Optimize paginated queries"""
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)

    @staticmethod
    def add_indexes_hints(query, indexes: list):
        """Add index hints to query"""
        # This is database-specific
        # For PostgreSQL, you might use .with_hint()
        return query

    @staticmethod
    def use_select_related(query, relations: list):
        """Use select_related for eager loading"""
        # SQLAlchemy equivalent: joinedload or selectinload
        from sqlalchemy.orm import joinedload
        for relation in relations:
            query = query.options(joinedload(relation))
        return query


class BatchProcessor:
    """Batch processing utilities"""

    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size

    def process_in_batches(self, items: list, processor: Callable):
        """Process items in batches"""
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            processor(batch)

    async def process_in_batches_async(self, items: list, processor: Callable):
        """Process items in batches asynchronously"""
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            await processor(batch)


class ConnectionPool:
    """Connection pooling utilities"""

    def __init__(self, max_workers: int = 4):
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)

    def execute_in_thread(self, func: Callable, *args, **kwargs):
        """Execute function in thread pool"""
        future = self.thread_pool.submit(func, *args, **kwargs)
        return future.result()

    def execute_in_process(self, func: Callable, *args, **kwargs):
        """Execute function in process pool"""
        future = self.process_pool.submit(func, *args, **kwargs)
        return future.result()

    def shutdown(self):
        """Shutdown pools"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

