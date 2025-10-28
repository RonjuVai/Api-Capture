import os
import logging
import requests
import json
import re
from urllib.parse import urljoin, urlparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Railway environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8292852232:AAGk47XqZKocBTT3je-gco0NOPUr1I3TrC0')

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class StableAPICaptureBot:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        welcome_text = f"""
🔍 **API Capture Bot**

Welcome {user.first_name}!

I can help you discover APIs from websites.

**How to Use:**
1. Send any website URL
2. I'll analyze it for APIs
3. Get discovered endpoints

**Example URLs:**
• https://ivasms.com
• https://jsonplaceholder.typicode.com
• https://api.github.com

**Commands:**
/start - Start bot
/capture - Capture APIs from URL  
/examples - Show examples
/help - Get help
        """
        
        keyboard = [
            [InlineKeyboardButton("🌐 Capture APIs", callback_data="capture_apis")],
            [InlineKeyboardButton("📋 Examples", callback_data="show_examples")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def capture_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Capture APIs command"""
        await update.message.reply_text(
            "🌐 **Send Website URL**\n\n"
            "Please send the website URL you want to analyze:\n\n"
            "Examples:\n"
            "• https://ivasms.com\n"
            "• https://api.github.com\n"
            "• https://jsonplaceholder.typicode.com\n\n"
            "I'll discover any available APIs."
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        text = update.message.text.strip()
        
        # Check if it's a URL
        if self.is_valid_url(text):
            await self.process_url(update, text)
        else:
            await update.message.reply_text(
                "❌ Please send a valid URL starting with http:// or https://\n\n"
                "Example: https://ivasms.com"
            )
    
    async def process_url(self, update: Update, url: str):
        """Process URL and discover APIs"""
        processing_msg = await update.message.reply_text(f"🔍 Analyzing {url}...")
        
        try:
            # Discover APIs
            results = await self.discover_apis(url)
            
            if results['success']:
                await self.send_results(update, results, url)
            else:
                await update.message.reply_text(
                    f"❌ Could not analyze {url}\n\n"
                    f"Error: {results['error']}\n\n"
                    "Please check the URL and try again."
                )
                
        except Exception as e:
            logger.error(f"Error processing URL: {e}")
            await update.message.reply_text(
                "❌ An error occurred while processing the URL.\n"
                "Please try again later."
            )
        
        # Delete processing message
        try:
            await processing_msg.delete()
        except:
            pass
    
    async def discover_apis(self, url: str) -> dict:
        """Discover APIs from URL"""
        try:
            # Fetch the webpage
            response = self.session.get(url, timeout=15, verify=False)
            response.raise_for_status()
            
            endpoints = []
            
            # Method 1: Find API endpoints in HTML
            html_endpoints = self.find_in_html(response.text, url)
            endpoints.extend(html_endpoints)
            
            # Method 2: Check common API paths
            common_endpoints = self.check_common_paths(url)
            endpoints.extend(common_endpoints)
            
            # Remove duplicates
            unique_endpoints = []
            seen = set()
            for endpoint in endpoints:
                if endpoint['url'] not in seen:
                    unique_endpoints.append(endpoint)
                    seen.add(endpoint['url'])
            
            return {
                'success': True,
                'endpoints': unique_endpoints,
                'total': len(unique_endpoints)
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Analysis error: {str(e)}"
            }
    
    def find_in_html(self, html: str, base_url: str) -> list:
        """Find API endpoints in HTML content"""
        endpoints = []
        
        # Patterns to search for in HTML
        patterns = [
            r'["\'](/api/v\d+/[^"\']*)["\']',
            r'["\'](/api/[^"\']*)["\']',
            r'["\'](/v\d+/[^"\']*)["\']',
            r'["\'](https?://[^"\']*?/api/[^"\']*)["\']',
            r'["\'](https?://[^"\']*?/v\d+/[^"\']*)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    full_url = match
                else:
                    full_url = urljoin(base_url, match)
                
                endpoints.append({
                    'url': full_url,
                    'method': 'GET',
                    'source': 'HTML'
                })
        
        return endpoints
    
    def check_common_paths(self, base_url: str) -> list:
        """Check common API paths"""
        common_paths = [
            '/api/v1/send-sms',
            '/api/v2/send-sms', 
            '/api/v3/send-sms',
            '/api/send-sms',
            '/api/sms/send',
            '/api/otp/send',
            '/api/verify',
            '/api/check-balance',
            '/api/balance',
            '/api/users',
            '/api/data',
            '/api/info',
            '/v1/users',
            '/v2/users',
            '/v1/data',
            '/v2/data',
        ]
        
        endpoints = []
        for path in common_paths:
            full_url = urljoin(base_url, path)
            endpoints.append({
                'url': full_url,
                'method': 'GET/POST',
                'source': 'Common path'
            })
        
        return endpoints
    
    def is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    async def send_results(self, update: Update, results: dict, original_url: str):
        """Send discovery results to user"""
        endpoints = results['endpoints']
        
        if not endpoints:
            await update.message.reply_text(
                f"🔍 **Analysis Complete**\n\n"
                f"🌐 URL: {original_url}\n"
                f"📊 APIs Found: 0\n\n"
                f"No API endpoints discovered.\n"
                f"Try a different URL or check the website manually."
            )
            return
        
        # Send summary
        summary = f"""
🔍 **Analysis Complete**

🌐 URL: {original_url}
📊 APIs Found: {results['total']}

**Discovered Endpoints:**
"""
        
        for i, endpoint in enumerate(endpoints[:8], 1):
            summary += f"\n{i}. `{endpoint['url']}`"
            summary += f"\n   Method: {endpoint['method']} | Source: {endpoint['source']}"
        
        if len(endpoints) > 8:
            summary += f"\n\n... and {len(endpoints) - 8} more endpoints"
        
        await update.message.reply_text(summary)
        
        # Send usage example
        if endpoints:
            example = self.generate_example(endpoints[0])
            await update.message.reply_text(example)
    
    def generate_example(self, endpoint: dict) -> str:
        """Generate Python code example"""
        return f"""
🐍 **Usage Example:**

```python
import requests

# Test the discovered API
url = "{endpoint['url']}"

try:
    response = requests.get(url, timeout=10)
    print(f"Status: {{response.status_code}}")
    print(f"Response: {{response.text}}")
except Exception as e:
    print(f"Error: {{e}}")
