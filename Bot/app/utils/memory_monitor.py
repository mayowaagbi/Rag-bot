"""
Memory monitoring utilities for the RAG bot deployment.
"""

import psutil
import logging
import os
from typing import Dict, Any
from functools import wraps
import time

logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Monitor memory usage and provide optimization recommendations."""

    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.get_memory_usage()

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()

        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
            "percent": memory_percent,
            "available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "total_mb": psutil.virtual_memory().total / 1024 / 1024,
        }

    def get_system_info(self) -> Dict[str, Any]:
        """Get system resource information."""
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_cores": cpu_count,
            "memory_total_gb": memory.total / 1024 / 1024 / 1024,
            "memory_available_gb": memory.available / 1024 / 1024 / 1024,
            "disk_total_gb": disk.total / 1024 / 1024 / 1024,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024,
        }

    def check_memory_pressure(self) -> Dict[str, Any]:
        """Check if the system is under memory pressure."""
        current = self.get_memory_usage()
        system = self.get_system_info()

        # Calculate memory pressure indicators
        pressure_indicators = {
            "high_memory_usage": current["percent"] > 80,
            "low_available_memory": current["available_mb"]
            < 512,  # Less than 512MB available
            "memory_growth": current["rss_mb"] > (self.initial_memory["rss_mb"] * 1.5),
            "recommendation": [],
        }

        # Generate recommendations
        if pressure_indicators["high_memory_usage"]:
            pressure_indicators["recommendation"].append("Reduce MAX_CHUNKS in config")
            pressure_indicators["recommendation"].append(
                "Enable model unloading after use"
            )

        if pressure_indicators["low_available_memory"]:
            pressure_indicators["recommendation"].append(
                "Increase chunk size to reduce total chunks"
            )
            pressure_indicators["recommendation"].append("Enable compression")

        if pressure_indicators["memory_growth"]:
            pressure_indicators["recommendation"].append("Check for memory leaks")
            pressure_indicators["recommendation"].append("Restart the application")

        return {
            "current_usage": current,
            "system_info": system,
            "pressure_indicators": pressure_indicators,
        }

    def log_memory_status(self, context: str = ""):
        """Log current memory status."""
        usage = self.get_memory_usage()
        context_str = f" ({context})" if context else ""

        logger.info(
            f"Memory Usage{context_str}: "
            f"RSS={usage['rss_mb']:.1f}MB, "
            f"Percent={usage['percent']:.1f}%, "
            f"Available={usage['available_mb']:.1f}MB"
        )


def monitor_memory(func):
    """Decorator to monitor memory usage of a function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        monitor = MemoryMonitor()

        # Log memory before
        monitor.log_memory_status(f"Before {func.__name__}")
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Log memory after
            end_time = time.time()
            monitor.log_memory_status(f"After {func.__name__}")

            # Check for memory pressure
            pressure = monitor.check_memory_pressure()
            if any(pressure["pressure_indicators"].values()):
                logger.warning(f"Memory pressure detected after {func.__name__}")
                for rec in pressure["pressure_indicators"]["recommendation"]:
                    logger.warning(f"Recommendation: {rec}")

            logger.info(f"{func.__name__} completed in {end_time - start_time:.2f}s")

    return wrapper


# Memory management utilities
def force_garbage_collection():
    """Force garbage collection and log memory freed."""
    import gc

    monitor = MemoryMonitor()
    before = monitor.get_memory_usage()

    # Force garbage collection
    collected = gc.collect()

    after = monitor.get_memory_usage()
    freed_mb = before["rss_mb"] - after["rss_mb"]

    logger.info(
        f"Garbage collection: freed {freed_mb:.1f}MB, collected {collected} objects"
    )

    return freed_mb


def get_deployment_recommendations() -> Dict[str, Any]:
    """Get deployment recommendations based on current system."""
    monitor = MemoryMonitor()
    system = monitor.get_system_info()

    recommendations = {
        "platform_suitability": {},
        "config_recommendations": {},
        "warnings": [],
    }

    # Platform suitability based on available memory
    memory_gb = system["memory_total_gb"]

    if memory_gb < 0.5:  # Less than 512MB
        recommendations["platform_suitability"]["render_free"] = "Not recommended"
        recommendations["platform_suitability"][
            "vercel"
        ] = "Suitable with heavy optimization"
        recommendations["platform_suitability"]["railway"] = "Not recommended"
        recommendations["warnings"].append(
            "Very low memory - consider serverless deployment"
        )
    elif memory_gb < 1:  # Less than 1GB
        recommendations["platform_suitability"][
            "render_free"
        ] = "Suitable with optimization"
        recommendations["platform_suitability"]["vercel"] = "Suitable"
        recommendations["platform_suitability"][
            "railway"
        ] = "Suitable with optimization"
    else:  # 1GB or more
        recommendations["platform_suitability"]["render_free"] = "Suitable"
        recommendations["platform_suitability"]["vercel"] = "Suitable"
        recommendations["platform_suitability"]["railway"] = "Suitable"

    # Configuration recommendations
    if memory_gb < 0.5:
        recommendations["config_recommendations"]["max_chunks"] = 200
        recommendations["config_recommendations"]["max_tokens_per_chunk"] = 600
        recommendations["config_recommendations"]["batch_size"] = 10
    elif memory_gb < 1:
        recommendations["config_recommendations"]["max_chunks"] = 500
        recommendations["config_recommendations"]["max_tokens_per_chunk"] = 400
        recommendations["config_recommendations"]["batch_size"] = 25
    else:
        recommendations["config_recommendations"]["max_chunks"] = 1000
        recommendations["config_recommendations"]["max_tokens_per_chunk"] = 300
        recommendations["config_recommendations"]["batch_size"] = 50

    return recommendations
