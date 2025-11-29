"""Monitoring and performance tracking utilities"""
import time
import logging
from functools import wraps
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, Dict[str, float]] = {
            'translation': {'total_time': 0, 'calls': 0},
            'sentiment': {'total_time': 0, 'calls': 0},
            'chat': {'total_time': 0, 'calls': 0}
        }

    def track_time(self, category: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    if category in self.metrics:
                        self.metrics[category]['total_time'] += duration
                        self.metrics[category]['calls'] += 1
                        avg_time = self.metrics[category]['total_time'] / self.metrics[category]['calls']
                        logger.debug(f"{category} operation took {duration:.2f}s (avg: {avg_time:.2f}s)")
            return wrapper
        return decorator

    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        return {
            category: {
                'total_time': stats['total_time'],
                'calls': stats['calls'],
                'average_time': stats['total_time'] / stats['calls'] if stats['calls'] > 0 else 0
            }
            for category, stats in self.metrics.items()
        }

# Global monitor instance
monitor = PerformanceMonitor()