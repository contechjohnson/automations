"""
Base Worker
===========
All workers inherit from this to get progress updates, streaming, and logging.
"""

import os
from datetime import datetime
from typing import Any, Optional
from rq import get_current_job
from redis import Redis


class BaseWorker:
    """Base class for all automation workers."""
    
    def __init__(self):
        self.job = get_current_job()
        self.redis = Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))
        self.start_time = datetime.utcnow()
    
    def update_progress(
        self,
        message: str,
        percent: Optional[int] = None,
        data: Optional[dict] = None
    ):
        """
        Update job progress (visible in /jobs/{id} and /jobs/{id}/stream).
        
        Usage:
            self.update_progress("Starting research...", percent=0)
            self.update_progress("Found 5 sources", percent=50, data={"sources": 5})
            self.update_progress("Complete!", percent=100)
        """
        if not self.job:
            print(f"[PROGRESS] {message}")
            return
        
        meta = self.job.meta or {}
        meta.update({
            "message": message,
            "percent": percent,
            "timestamp": datetime.utcnow().isoformat(),
            "elapsed_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        })
        
        if data:
            meta["data"] = data
        
        self.job.meta = meta
        self.job.save_meta()
        
        print(f"[PROGRESS] {percent}% - {message}")
    
    def log(self, message: str, level: str = "info"):
        """Log a message."""
        timestamp = datetime.utcnow().isoformat()
        print(f"[{level.upper()}] {timestamp} - {message}")
    
    def publish_event(self, channel: str, event: dict):
        """
        Publish event to Redis pub/sub for real-time streaming.
        Your frontend can subscribe to these channels.
        """
        import json
        self.redis.publish(channel, json.dumps(event))


def with_progress(func):
    """
    Decorator to add progress tracking to any function.
    
    Usage:
        @with_progress
        def my_worker(param1, param2):
            job = get_current_job()
            job.meta = {"message": "Working...", "percent": 50}
            job.save_meta()
            return {"result": "done"}
    """
    def wrapper(*args, **kwargs):
        job = get_current_job()
        if job:
            job.meta = {"message": "Starting...", "percent": 0}
            job.save_meta()
        
        try:
            result = func(*args, **kwargs)
            if job:
                job.meta = {"message": "Complete", "percent": 100}
                job.save_meta()
            return result
        except Exception as e:
            if job:
                job.meta = {"message": f"Error: {str(e)}", "percent": -1}
                job.save_meta()
            raise
    
    return wrapper
