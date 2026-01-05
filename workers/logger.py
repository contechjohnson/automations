"""
Execution Logger
================
Ultra-simple logging to Supabase for testing and debugging.
Every run gets captured with raw input/output.

Usage:
    from workers.logger import ExecutionLogger

    log = ExecutionLogger("scrapers.permits", input_params)
    log.note("testing new endpoint")
    log.tag("test", "permits")
    
    try:
        result = do_work()
        log.success(result)
    except Exception as e:
        log.fail(e)
"""

import os
import traceback
from datetime import datetime
from typing import Optional, Any
from supabase import create_client


class ExecutionLogger:
    """Simple execution logger for testing."""
    
    def __init__(
        self,
        worker_name: str,
        input_data: dict,
        automation_slug: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[list] = None
    ):
        self.supabase = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        )
        self.worker_name = worker_name
        self.automation_slug = automation_slug
        self.start_time = datetime.utcnow()
        self.log_id = None
        self._notes = notes
        self._tags = tags or []
        self._metadata = {}
        
        # Create log entry
        self._create_entry(input_data)
    
    def _create_entry(self, input_data: dict):
        """Create initial log entry."""
        result = self.supabase.table("execution_logs").insert({
            "worker_name": self.worker_name,
            "automation_slug": self.automation_slug,
            "input": input_data,
            "notes": self._notes,
            "tags": self._tags,
            "status": "running"
        }).execute()
        
        if result.data:
            self.log_id = result.data[0]["id"]
    
    def note(self, text: str):
        """Add or update notes."""
        self._notes = text
        if self.log_id:
            self.supabase.table("execution_logs").update({
                "notes": text
            }).eq("id", self.log_id).execute()
    
    def tag(self, *tags: str):
        """Add tags."""
        self._tags.extend(tags)
        if self.log_id:
            self.supabase.table("execution_logs").update({
                "tags": list(set(self._tags))
            }).eq("id", self.log_id).execute()
    
    def meta(self, key: str, value: Any):
        """Add metadata (progress, stats, etc.)."""
        self._metadata[key] = value
        if self.log_id:
            self.supabase.table("execution_logs").update({
                "metadata": self._metadata
            }).eq("id", self.log_id).execute()
    
    def success(self, output: Any):
        """Mark as successful with output."""
        runtime = (datetime.utcnow() - self.start_time).total_seconds()
        
        if self.log_id:
            self.supabase.table("execution_logs").update({
                "status": "success",
                "completed_at": datetime.utcnow().isoformat(),
                "runtime_seconds": round(runtime, 2),
                "output": output if isinstance(output, dict) else {"result": output},
                "metadata": self._metadata
            }).eq("id", self.log_id).execute()
        
        return output
    
    def fail(self, error: Exception):
        """Mark as failed with error details."""
        runtime = (datetime.utcnow() - self.start_time).total_seconds()
        
        error_data = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc()
        }
        
        if self.log_id:
            self.supabase.table("execution_logs").update({
                "status": "failed",
                "completed_at": datetime.utcnow().isoformat(),
                "runtime_seconds": round(runtime, 2),
                "error": error_data,
                "metadata": self._metadata
            }).eq("id", self.log_id).execute()
        
        raise error  # Re-raise so the job fails properly


def logged(worker_name: str, automation_slug: Optional[str] = None):
    """
    Decorator for automatic logging.
    
    Usage:
        @logged("scrapers.permits", "va-loudoun-permits")
        def my_worker(config, geography):
            return {"records": [...]}
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            log = ExecutionLogger(
                worker_name=worker_name,
                automation_slug=automation_slug,
                input_data={"args": args, "kwargs": kwargs}
            )
            try:
                result = func(*args, **kwargs)
                return log.success(result)
            except Exception as e:
                log.fail(e)
        return wrapper
    return decorator
