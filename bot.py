import asyncio
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests
import time
import re

# বট টোকেন
BOT_TOKEN = "8292852232:AAGk47XqZKocBTT3je-gco0NOPUr1I3TrC0"

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class APICaptureBot:
    def __init__(self):
        self.user_sessions = {}
        self.drivers = {}
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        welcome_text = f"""
🔍 **Advanced API Capture Bot**

Welcome {user.first_name}!

I can capture APIs from any website automatically.

**How to Use:**
1. Send website URL
2. I'll analyze and capture all APIs
3. Get complete API documentation

**Supported Sites:**
• IVASMS
• Any SMS Gateway
• Payment Gateways  
• Social Media APIs
• Custom Websites

**Features:**
✅ Automatic API Discovery
✅ Request/Response Capture
✅ Parameter Extraction
✅ Ready-to-use Code
        """
        
        keyboard = [
            [InlineKeyboardButton("🌐 Capture APIs", callback_data="capture_apis")],
            [InlineKeyboardButton("📋 Examples", callback_data="show_examples")],
            [InlineKeyboardButton("🆘 Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def handle_capture_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """API capture request handle"""
        await update.message.reply_text(
            "🌐 **Send Website URL**\n\n"
            "Please send the website URL you want to capture APIs from:\n\n"
            "📋 **Examples:**\n"
            "• https://ivasms.com\n"
            "• https://panel.ivasms.com\n"
            "• https://any-website.com\n\n"
            "⚠️ Make sure the site is accessible and has API functionality."
        )
    
    async def handle_url_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle URL input and start API capture"""
        url = update.message.text.strip()
        user_id = update.effective_user.id
        
        # URL validation
        if not self.is_valid_url(url):
            await update.message.reply_text(
                "❌ Invalid URL!\n\n"
                "Please send a valid URL starting with http:// or https://\n\n"
                "Example: https://ivasms.com"
            )
            return
        
        # Start capture process
        processing_msg = await update.message.reply_text(
            f"🔄 Starting API capture for:\n{url}\n\n"
            "This may take 1-2 minutes..."
        )
        
        try:
            # Capture APIs
            api_data = await self.capture_apis_from_url(url, user_id)
            
            if api_data:
                await self.send_api_results(update, api_data, url)
            else:
                await update.message.reply_text(
                    "❌ No APIs found!\n\n"
                    "Possible reasons:\n"
                    "• Site uses heavy JavaScript\n"
                    "• APIs are hidden/encrypted\n"
                    "• Site requires login\n"
                    "• Try a different URL"
                )
                
        except Exception as e:
            logger.error(f"API capture error: {e}")
            await update.message.reply_text(
                f"❌ Capture failed: {str(e)}\n\n"
                "Please try again or contact support."
            )
        
        try:
            await processing_msg.delete()
        except:
            pass
    
    async def capture_apis_from_url(self, url: str, user_id: int) -> dict:
        """Capture APIs from given URL using Selenium"""
        driver = None
        try:
            # Setup Chrome with logging enabled
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Remove for debugging
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Enable performance logging
            caps = DesiredCapabilities.CHROME
            caps['goog:loggingPrefs'] = {'performance': 'ALL'}
            
            driver = webdriver.Chrome(options=chrome_options, desired_capabilities=caps)
            self.drivers[user_id] = driver
            
            # Navigate to URL
            driver.get(url)
            
            # Wait for page load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Capture initial network requests
            initial_logs = self.get_network_logs(driver)
            
            # Try to find and click common elements to trigger APIs
            self.interact_with_page(driver)
            
            # Wait for additional requests
            time.sleep(5)
            
            # Capture final network requests
            final_logs = self.get_network_logs(driver)
            
            # Combine and analyze logs
            all_logs = initial_logs + final_logs
            api_data = self.analyze_network_logs(all_logs, url)
            
            return api_data
            
        except Exception as e:
            logger.error(f"Selenium error: {e}")
            return {}
        finally:
            if driver:
                driver.quit()
                if user_id in self.drivers:
                    del self.drivers[user_id]
    
    def get_network_logs(self, driver):
        """Get network logs from browser"""
        try:
            logs = driver.get_log('performance')
            return logs
        except:
            return []
    
    def interact_with_page(self, driver):
        """Interact with page to trigger API calls"""
        try:
            # Try to find and click buttons that might trigger APIs
            click_selectors = [
                "button",
                "a[href*='api']",
                "input[type='submit']",
                ".btn",
                "[onclick*='ajax']",
                "[data-action*='api']"
            ]
            
            for selector in click_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:2]:  # Click first 2 elements
                        try:
                            element.click()
                            time.sleep(1)
                        except:
                            continue
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Page interaction error: {e}")
    
    def analyze_network_logs(self, logs, base_url):
        """Analyze network logs and extract API information"""
        api_endpoints = []
        
        for log in logs:
            try:
                log_message = json.loads(log['message'])
                message = log_message.get('message', {})
                
                if message.get('method') == 'Network.requestWillBeSent':
                    request = message.get('params', {}).get('request', {})
                    url = request.get('url', '')
                    
                    # Filter API-like URLs
                    if self.is_api_url(url, base_url):
                        api_info = {
                            'url': url,
                            'method': request.get('method'),
                            'headers': request.get('headers', {}),
                            'post_data': request.get('postData'),
                            'timestamp': log.get('timestamp')
                        }
                        api_endpoints.append(api_info)
                        
            except Exception as e:
                continue
        
        # Remove duplicates
        unique_apis = []
        seen_urls = set()
        
        for api in api_endpoints:
            if api['url'] not in seen_urls:
                unique_apis.append(api)
                seen_urls.add(api['url'])
        
        return {
            'base_url': base_url,
            'apis_found': len(unique_apis),
            'endpoints': unique_apis
        }
    
    def is_api_url(self, url, base_url):
        """Check if URL looks like an API endpoint"""
        api_indicators = [
            '/api/', '/v1/', '/v2/', '/v3/', '/json', '/xml',
            '/sms', '/send', '/otp', '/verify', '/auth',
            'api.', 'gateway.', 'rest.', 'graphql'
        ]
        
        # Exclude common non-API URLs
        exclude_patterns = [
            '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico',
            'fonts.', 'analytics', 'google', 'facebook', 'twitter'
        ]
        
        url_lower = url.lower()
        base_domain = self.extract_domain(base_url)
        
        # Check if it's from the same domain and contains API indicators
        if base_domain in url_lower:
            if any(indicator in url_lower for indicator in api_indicators):
                if not any(pattern in url_lower for pattern in exclude_patterns):
                    return True
        
        return False
    
    def extract_domain(self, url):
        """Extract domain from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def is_valid_url(self, url):
        """Validate URL format"""
        import re
        pattern = re.compile(
            r'^(https?://)'  # http:// or https://
            r'([a-zA-Z0-9.-]+)'  # domain
            r'(\.[a-zA-Z]{2,})'  # top-level domain
            r'(:\d+)?'  # port
            r'(/.*)?$'  # path
        )
        return pattern.match(url) is not None
    
    async def send_api_results(self, update: Update, api_data: dict, original_url: str):
        """Send captured API results to user"""
        if not api_data.get('endpoints'):
            await update.message.reply_text("❌ No APIs found on this site.")
            return
        
        # Send summary
        summary_text = f"""
🔍 **API Capture Results**

🌐 **Website:** {original_url}
📊 **APIs Found:** {api_data['apis_found']}

📋 **Discovered Endpoints:**
"""
        
        for i, endpoint in enumerate(api_data['endpoints'][:10], 1):  # Show first 10
            summary_text += f"\n{i}. `{endpoint['method']} {endpoint['url']}`"
        
        if api_data['apis_found'] > 10:
            summary_text += f"\n\n... and {api_data['apis_found'] - 10} more endpoints"
        
        await update.message.reply_text(summary_text)
        
        # Send detailed information for each endpoint
        for i, endpoint in enumerate(api_data['endpoints'][:5], 1):  # Details for first 5
            endpoint_text = f"""
🔧 **Endpoint {i}**

🔗 **URL:** `{endpoint['url']}`
📡 **Method:** `{endpoint['method']}`

📝 **Headers:**
```json
{json.dumps(endpoint['headers'], indent=2)}