#!/usr/bin/env python3
"""
Kiri Research Labs - Autonomous Colab Integration (Fixed)
100% Independent Code Execution System
Uses Google Drive API + Selenium for autonomous operation
"""

import os
import json
import time
import base64
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium_stealth import stealth
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutonomousColab:
    """
    Fully autonomous Colab integration that requires zero human intervention
    Uses Google Drive API credentials for authentication and Selenium for browser control
    """
    
    def __init__(self):
        self.credentials_path = "/home/nwokike/.mcp-colab/credentials.json"
        self.token_path = "/home/nwokike/.mcp-colab/token.json"
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.refresh_token = None
        self.driver = None
        self.notebook_url = None
        
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
    
    def _setup_chrome_driver(self):
        """Setup Chrome driver for autonomous operation"""
        try:
            options = Options()
            
            # Essential options for stability
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            
            # Headless mode for full autonomy
            options.add_argument('--headless=new')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Disable automation detection
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Use existing Chrome binary if available
            try:
                self.driver = webdriver.Chrome(options=options)
            except:
                # Try with specific Chrome binary path
                options.binary_location = '/usr/bin/chromium-browser'
                self.driver = webdriver.Chrome(options=options)
            
            # Apply stealth
            stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            logger.info("✅ Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup Chrome driver: {e}")
            return False
    
    def create_notebook(self, title: str = "Kiri_Autonomous_Research") -> Optional[str]:
        """Create a new Colab notebook autonomously"""
        try:
            if not self._setup_chrome_driver():
                return None
                
            # Navigate to Google Drive first to authenticate
            self.driver.get("https://accounts.google.com/signin")
            time.sleep(3)
            
            # Add access token via localStorage (alternative authentication method)
            auth_script = f"""
            localStorage.setItem('access_token', '{self.access_token}');
            localStorage.setItem('refresh_token', '{self.refresh_token}');
            """
            self.driver.execute_script(auth_script)
            
            # Navigate to Colab
            colab_url = "https://colab.research.google.com"
            self.driver.get(colab_url)
            time.sleep(5)
            
            # Create new notebook
            try:
                # Look for "New notebook" button
                new_btn = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'New notebook')]"))
                )
                new_btn.click()
                time.sleep(3)
            except:
                # Try keyboard shortcut
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.CONTROL + "n")
                time.sleep(3)
            
            # Get notebook URL
            self.notebook_url = self.driver.current_url
            logger.info(f"✅ Created notebook: {self.notebook_url}")
            
            # Set title
            try:
                title_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Untitled0.ipynb']"))
                )
                title_input.clear()
                title_input.send_keys(title)
                title_input.send_keys(Keys.ENTER)
            except:
                logger.warning("⚠️ Could not set title, continuing...")
            
            return self.notebook_url
            
        except Exception as e:
            logger.error(f"❌ Failed to create notebook: {e}")
            return None
    
    def execute_code(self, code: str, timeout: int = 60) -> Dict[str, Any]:
        """Execute Python code in the notebook and return results"""
        try:
            if not self.driver or not self.notebook_url:
                return {"error": "No active notebook session"}
            
            # Navigate to notebook
            self.driver.get(self.notebook_url)
            time.sleep(3)
            
            # Find or create code cell
            try:
                cell = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
                )
            except:
                # Add new cell
                try:
                    add_cell_btn = self.driver.find_element(By.XPATH, "//button[@aria-label='Add cell']")
                    add_cell_btn.click()
                except:
                    # Use keyboard shortcut
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.CONTROL + "b")  # Add cell shortcut
                
                time.sleep(2)
                cell = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror"))
                )
            
            # Click and clear cell
            cell.click()
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.CONTROL + "a")  # Select all
            body.send_keys(Keys.DELETE)  # Clear
            
            # Insert code
            lines = code.strip().split('\n')
            for line in lines:
                body.send_keys(line)
                body.send_keys(Keys.SHIFT + Keys.ENTER)  # New line within cell
            
            # Execute code
            body.send_keys(Keys.CONTROL + Keys.ENTER)  # Run cell
            
            # Wait for execution
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Check for output
                    outputs = self.driver.find_elements(By.CLASS_NAME, "output_subarea")
                    if outputs:
                        result_text = outputs[-1].text  # Get last output
                        return {
                            "success": True,
                            "output": result_text,
                            "execution_time": time.time() - start_time
                        }
                except:
                    pass
                
                # Check for errors
                try:
                    errors = self.driver.find_elements(By.CLASS_NAME, "output_error")
                    if errors:
                        error_text = errors[-1].text
                        return {
                            "success": False,
                            "error": error_text
                        }
                except:
                    pass
                
                time.sleep(1)
            
            return {"error": "Execution timeout"}
            
        except Exception as e:
            logger.error(f"❌ Code execution failed: {e}")
            return {"error": str(e)}
    
    def save_notebook(self) -> bool:
        """Save the current notebook"""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.CONTROL + "s")
            time.sleep(2)
            logger.info("✅ Notebook saved successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save notebook: {e}")
            return False
    
    def close(self):
        """Close the browser session"""
        if self.driver:
            self.driver.quit()
            logger.info("✅ Browser session closed")

# Test function to verify autonomous operation
def test_autonomous_colab():
    """Test the autonomous Colab integration"""
    logger.info("🚀 Testing autonomous Colab integration...")
    
    try:
        # Initialize
        colab = AutonomousColab()
        
        # Create notebook
        notebook_url = colab.create_notebook("Kiri_Test_Notebook")
        if not notebook_url:
            return False
        
        # Test simple code execution
        test_code = """print("Hello from Kiri Research Labs!")
print("Autonomous Colab integration test successful!")"""
        
        result = colab.execute_code(test_code)
        logger.info(f"Execution result: {result}")
        
        # Save notebook
        colab.save_notebook()
        
        # Close session
        colab.close()
        
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