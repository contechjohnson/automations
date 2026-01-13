"""
Simplified repository for v2 tables - used by Make.com API endpoints
"""
import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client


def get_supabase() -> Client:
    """Get Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)


class V2Repository:
    """Simplified repository for Make.com API endpoints"""
    
    def __init__(self, client: Optional[Client] = None):
        self.client = client or get_supabase()
    
    # ---------- Clients ----------
    
    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get a client by ID"""
        result = self.client.table("v2_clients").select("*").eq("id", client_id).single().execute()
        return result.data if result.data else None
    
    def get_client_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a client by slug"""
        result = self.client.table("v2_clients").select("*").eq("slug", slug).single().execute()
        return result.data if result.data else None
    
    # ---------- Prompts ----------
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a prompt by prompt_id"""
        result = self.client.table("v2_prompts").select("*").eq("prompt_id", prompt_id).single().execute()
        return result.data if result.data else None
    
    def get_prompt_version(self, prompt_id: str, version_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get a prompt version - if version_number is None, get current version"""
        if version_number is None:
            # Get current version from prompt record
            prompt = self.get_prompt(prompt_id)
            if not prompt:
                return None
            version_number = prompt.get("current_version", 1)
        
        result = self.client.table("v2_prompt_versions").select("*").eq("prompt_id", prompt_id).eq("version_number", version_number).single().execute()
        return result.data if result.data else None
    
    def get_prompt_with_content(self, prompt_id: str, version_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get prompt metadata with content from version"""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None
        
        version = self.get_prompt_version(prompt_id, version_number)
        if version:
            prompt["content"] = version["content"]
            prompt["system_prompt"] = version.get("system_prompt")
        
        return prompt

