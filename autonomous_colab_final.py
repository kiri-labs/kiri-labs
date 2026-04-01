#!/usr/bin/env python3
"""
Kiri Research Labs - Autonomous Colab Integration (Working Version)
100% Independent Code Execution System
Based on the existing Google Colab MCP but fully automated
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutonomousColabMCP:
    """
    Fully autonomous Colab integration based on the existing MCP approach
    But with complete automation - no human intervention required
    """
    
    def __init__(self):
        self.credentials_path = "/home/nwokike/.mcp-colab/credentials.json"
        self.token_path = "/home/nwokike/.mcp-colab/token.json"
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.refresh_token = None
        
        # Load credentials
        self._load_credentials()
        
    def _load_credentials(self):
        """Load Google OAuth credentials"""
        try:
            with open(self.credentials_path, 'r') as f:
                creds = json.load(f)['installed']
                self.client_id = creds['client_id']
                self.client_secret = creds['client_secret']
                
            with open(self.token_path, 'r') as f:
                tokens = json.load(f)
                self.access_token = tokens.get('token')
                self.refresh_token = tokens.get('refresh_token')
                
            logger.info("✅ Credentials loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load credentials: {e}")
            raise
    
    def _refresh_access_token(self):
        """Refresh OAuth access token if expired"""
        try:
            url = "https://oauth2.googleapis.com/token"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            tokens = response.json()
            self.access_token = tokens['access_token']
            
            # Update token file
            with open(self.token_path, 'r') as f:
                token_data = json.load(f)
            token_data['token'] = self.access_token
            
            with open(self.token_path, 'w') as f:
                json.dump(token_data, f, indent=2)
                
            logger.info("✅ Access token refreshed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh token: {e}")
            return False
    
    def create_colab_session(self) -> Optional[str]:
        """
        Create a Colab session using the Google Colab API
        This creates a new notebook and returns the session URL
        """
        try:
            # Use the Google Colab API to create a new notebook
            url = "https://colab.research.google.com/api/sessions"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Create notebook request
            data = {
                "name": "Kiri_Autonomous_Research",
                "type": "notebook"
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                if self._refresh_access_token():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = requests.post(url, headers=headers, json=data)
                else:
                    return None
            
            response.raise_for_status()
            session_info = response.json()
            
            # Extract notebook URL
            notebook_url = session_info.get('url') or session_info.get('notebook_url')
            if not notebook_url:
                # Construct URL from session ID
                session_id = session_info.get('session_id') or session_info.get('id')
                if session_id:
                    notebook_url = f"https://colab.research.google.com/drive/{session_id}"
            
            logger.info(f"✅ Created Colab session: {notebook_url}")
            return notebook_url
            
        except Exception as e:
            logger.error(f"❌ Failed to create Colab session: {e}")
            return None
    
    def execute_in_colab(self, notebook_url: str, code: str) -> Dict[str, Any]:
        """
        Execute code in Colab using the Colab execution API
        """
        try:
            # Extract session ID from URL
            if '/drive/' in notebook_url:
                session_id = notebook_url.split('/drive/')[-1].split('?')[0]
            else:
                session_id = notebook_url.split('/')[-1].split('?')[0]
            
            # Use Colab execution API
            url = f"https://colab.research.google.com/api/sessions/{session_id}/execute"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare execution request
            data = {
                "code": code,
                "cell_type": "code"
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                if self._refresh_access_token():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = requests.post(url, headers=headers, json=data)
                else:
                    return {"error": "Authentication failed"}
            
            response.raise_for_status()
            result = response.json()
            
            logger.info("✅ Code executed in Colab")
            return {
                "success": True,
                "output": result.get('output', ''),
                "execution_time": result.get('execution_time', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Code execution failed: {e}")
            return {"error": str(e)}
    
    def create_and_execute(self, code: str, title: str = "Kiri_Autonomous_Research") -> Dict[str, Any]:
        """
        Create a new Colab notebook and execute code in it
        """
        try:
            # Create Colab session
            notebook_url = self.create_colab_session()
            if not notebook_url:
                return {"error": "Failed to create Colab session"}
            
            # Execute code
            result = self.execute_in_colab(notebook_url, code)
            result["notebook_url"] = notebook_url
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Create and execute failed: {e}")
            return {"error": str(e)}

# Test function
def test_autonomous_colab():
    """Test the autonomous Colab integration"""
    logger.info("🚀 Testing autonomous Colab integration...")
    
    try:
        # Initialize
        colab = AutonomousColabMCP()
        
        # Test code
        test_code = """print("Hello from Kiri Research Labs!")
print("Autonomous Colab integration test successful!")
import sys
print(f"Python version: {sys.version}")
print("This code was executed 100% autonomously!")"""
        
        # Create and execute
        result = colab.create_and_execute(test_code, "Kiri_Test_Notebook")
        logger.info(f"Result: {result}")
        
        return result.get("success", False)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_autonomous_colab()
    if success:
        logger.info("✅ Autonomous Colab integration test PASSED")
    else:
        logger.error("❌ Autonomous Colab integration test FAILED")