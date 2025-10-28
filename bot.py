import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("Please set the BOT_TOKEN environment variable")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_text = """
# TITAN VELVIERX  
**bot**

---

### WELCOME TO TITAN'S OSINT BOT

- **Available Services:**  
- Number Search - Mobile number information  
- Vehicle Search - RC vehicle details  
- Aadhaar Search - Aadhaar family data  
- IFSC Search - Bank branch information  

---

### **Need Help?**  
Use 'Contact Admin' to reach out for support!
    """
    
    # Create custom keyboard
    keyboard = [
        [KeyboardButton("Number Search"), KeyboardButton("Vehicle Search")],
        [KeyboardButton("Aadhaar Family Search"), KeyboardButton("IFSC Code Search")],
        [KeyboardButton("Contact Admin"), KeyboardButton("Help")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# Handle button responses
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    
    if text == "Number Search":
        response = """
🔍 **Number Search Service**
        
Please provide the mobile number you want to search in the format:
`+91XXXXXXXXXX` or `XXXXXXXXXX`
        
*Note: This service provides carrier information and basic details.*
        """
        await update.message.reply_text(response)
    
    elif text == "Vehicle Search":
        response = """
🚗 **Vehicle Search Service**
        
Please provide the vehicle registration number you want to search.
Format: `DL01AB1234` or `KA51MX1234`
        
*This service provides RC vehicle details including owner information.*
        """
        await update.message.reply_text(response)
    
    elif text == "Aadhaar Family Search":
        response = """
🆔 **Aadhaar Family Search Service**
        
Please provide the Aadhaar number you want to search.
Format: `1234 5678 9012`
        
*Note: This service provides family data linked to the Aadhaar number.*
        """
        await update.message.reply_text(response)
    
    elif text == "IFSC Code Search":
        response = """
🏦 **IFSC Code Search Service**
        
Please provide the IFSC code you want to search.
Format: `SBIN0000123` or `HDFC0000123`
        
*This service provides bank branch information.*
        """
        await update.message.reply_text(response)
    
    elif text == "Contact Admin":
        response = """
📞 **Contact Admin**
        
For support, queries, or assistance:
        
**Email:** admin@titanvelvierx.com
**Telegram:** @TitanAdmin
**Response Time:** 24-48 hours
        
Please describe your issue in detail for faster resolution.
        """
        await update.message.reply_text(response)
    
    elif text == "Help":
        response = """
❓ **Help & Support**
        
**Available Commands:**
• /start - Start the bot
• Number Search - Mobile number lookup
• Vehicle Search - Vehicle registration details
• Aadhaar Family Search - Aadhaar linked family data
• IFSC Code Search - Bank branch information
        
**How to use:**
1. Select any service from the menu
2. Follow the format instructions
3. Receive your results
        
**Privacy Policy:** We don't store your search data.
        """
        await update.message.reply_text(response)
    
    else:
        # Handle actual search queries
        if update.message.text.replace(" ", "").isdigit() and len(update.message.text.replace(" ", "")) == 10:
            # Simulate number search result
            result = f"""
📱 **Number Search Result**
            
**Number:** {update.message.text}
**Carrier:** Jio
**Circle:** Delhi
**Status:** Active
**Type:** Prepaid
            
*This is simulated data for demonstration purposes.*
            """
            await update.message.reply_text(result)
        
        elif len(update.message.text) in [10, 11] and update.message.text.isalnum():
            # Simulate vehicle search result
            result = f"""
🚗 **Vehicle Search Result**
            
**Registration:** {update.message.text.upper()}
**Owner:** Rajesh Kumar
**Model:** Hyundai i20
**Fuel Type:** Petrol
**Registration Year:** 2020
            
*This is simulated data for demonstration purposes.*
            """
            await update.message.reply_text(result)
        
        elif len(update.message.text.replace(" ", "")) == 12 and update.message.text.replace(" ", "").isdigit():
            # Simulate Aadhaar search result
            result = f"""
🆔 **Aadhaar Family Search Result**
            
**Aadhaar:** {update.message.text}
**Name:** Priya Sharma
**Family Members:** 4
**Address:** Mumbai, Maharashtra
            
*This is simulated data for demonstration purposes.*
            """
            await update.message.reply_text(result)
        
        elif len(update.message.text) == 11:
            # Simulate IFSC search result
            result = f"""
🏦 **IFSC Search Result**
            
**IFSC:** {update.message.text.upper()}
**Bank:** State Bank of India
**Branch:** Connaught Place
**Address:** New Delhi, 110001
            
*This is simulated data for demonstration purposes.*
            """
            await update.message.reply_text(result)
        
        else:
            await update.message.reply_text("Please select an option from the menu or provide valid input format.")

# Error handler
async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Exception while handling an update: {context.error}")

def main() -> None:
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)

    # Start the bot
    print("🤖 Bot is running on Railway...")
    application.run_polling()

if __name__ == '__main__':
    main()
