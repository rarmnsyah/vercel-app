from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse
import httpx
import json
import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# FastAPI app instance
app = FastAPI(title="Telegram Bot Webhook", version="1.0.0")

# Configuration - Use environment variables
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://your-app.vercel.app/api/telegram_webhook')

# Telegram API base URL
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Pydantic models for type validation
class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None

class TelegramChat(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    first_name: Optional[str] = None

class TelegramMessage(BaseModel):
    message_id: int
    from_: Optional[TelegramUser] = None
    chat: TelegramChat
    date: int
    text: Optional[str] = None
    
    class Config:
        fields = {'from_': 'from'}

class CallbackQuery(BaseModel):
    id: str
    from_: TelegramUser
    message: Optional[TelegramMessage] = None
    data: Optional[str] = None
    
    class Config:
        fields = {'from_': 'from'}

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    callback_query: Optional[CallbackQuery] = None

# HTTP client for making requests
async def get_http_client():
    return httpx.AsyncClient()

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "Telegram Bot Webhook API",
        "status": "active",
        "endpoints": {
            "webhook": "/webhook",
            "setup": "/setup",
            "docs": "/docs"
        }
    }

@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Main webhook endpoint for receiving Telegram updates
    """
    try:
        # Parse the request body
        body = await request.json()
        update = TelegramUpdate(**body)
        
        # Process the update
        await process_telegram_update(update)
        
        return JSONResponse(
            status_code=200,
            content={"status": "ok"}
        )
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=400, detail="Bad request")

@app.get("/setup")
async def webhook_setup(
    action: str = Query("info", description="Action: set, delete, or info")
):
    """
    Setup webhook endpoint
    - action=set: Set the webhook
    - action=delete: Delete the webhook  
    - action=info: Get webhook information
    """
    try:
        async with httpx.AsyncClient() as client:
            if action == "set":
                # Set webhook
                url = f"{TELEGRAM_API_BASE}/setWebhook"
                data = {
                    "url": f"{WEBHOOK_URL}/webhook",
                    "allowed_updates": ["message", "callback_query"]
                }
                
                response = await client.post(url, json=data)
                result = response.json()
                
                if result.get("ok"):
                    return {
                        "status": "Webhook set successfully",
                        "webhook_url": f"{WEBHOOK_URL}/webhook",
                        "result": result
                    }
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to set webhook: {result}"
                    )
            
            elif action == "delete":
                # Delete webhook
                url = f"{TELEGRAM_API_BASE}/deleteWebhook"
                response = await client.post(url)
                result = response.json()
                
                return {
                    "status": "Webhook deleted",
                    "result": result
                }
            
            else:
                # Get webhook info
                url = f"{TELEGRAM_API_BASE}/getWebhookInfo"
                response = await client.get(url)
                result = response.json()
                
                return {
                    "webhook_info": result.get("result", {}),
                    "instructions": {
                        "set_webhook": f"{WEBHOOK_URL}/setup?action=set",
                        "delete_webhook": f"{WEBHOOK_URL}/setup?action=delete"
                    }
                }
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_telegram_update(update: TelegramUpdate):
    """
    Process incoming Telegram updates
    """
    try:
        if update.message:
            await handle_message(update.message)
        elif update.callback_query:
            await handle_callback_query(update.callback_query)
            
    except Exception as e:
        print(f"Error processing update: {e}")

async def handle_message(message: TelegramMessage):
    """
    Handle text messages
    """
    chat_id = message.chat.id
    text = message.text or ""
    user_name = message.from_.first_name if message.from_ else "User"
    
    # Process different commands
    if text.startswith('/start'):
        response_text = f"🤖 Hello {user_name}! Welcome to the bot!\n\nUse /help to see available commands."
        await send_message(chat_id, response_text)
        
    elif text.startswith('/help'):
        response_text = """
📋 <b>Available Commands:</b>

/start - Start the bot
/help - Show this help message  
/echo [text] - Echo your message
/status - Check bot status
/keyboard - Show sample keyboard
/info - Get your user info
        """
        await send_message(chat_id, response_text)
        
    elif text.startswith('/echo'):
        echo_text = text.replace('/echo', '').strip()
        response_text = f"🔄 You said: <i>{echo_text}</i>" if echo_text else "Please provide text to echo!\n\nExample: <code>/echo Hello World</code>"
        await send_message(chat_id, response_text)
        
    elif text.startswith('/status'):
        response_text = "✅ Bot is running perfectly!\n\n🚀 FastAPI + Vercel deployment active"
        await send_message(chat_id, response_text)
        
    elif text.startswith('/keyboard'):
        keyboard = create_sample_keyboard()
        await send_message_with_keyboard(
            chat_id, 
            "🎛️ <b>Sample Keyboard</b>\n\nChoose an option below:",
            keyboard
        )
        
    elif text.startswith('/info'):
        if message.from_:
            info_text = f"""
👤 <b>Your Information:</b>

🆔 User ID: <code>{message.from_.id}</code>
👋 Name: {message.from_.first_name}
💬 Chat ID: <code>{chat_id}</code>
            """
            if message.from_.username:
                info_text += f"📝 Username: @{message.from_.username}\n"
        else:
            info_text = "ℹ️ User information not available"
            
        await send_message(chat_id, info_text)
        
    else:
        response_text = f"👋 Hello {user_name}!\n\n💬 You sent: <i>{text}</i>\n\nUse /help to see available commands."
        await send_message(chat_id, response_text)

async def handle_callback_query(callback_query: CallbackQuery):
    """
    Handle callback queries from inline keyboards
    """
    chat_id = callback_query.message.chat.id if callback_query.message else callback_query.from_.id
    data = callback_query.data
    
    # Process different callback data
    if data == "btn1":
        response_text = "🔵 You clicked Button 1!"
    elif data == "btn2":
        response_text = "🟢 You clicked Button 2!"
    elif data == "help":
        response_text = "❓ This is the help section from inline keyboard!"
    elif data == "about":
        response_text = "ℹ️ This bot is built with FastAPI and deployed on Vercel!"
    else:
        response_text = f"🎯 You clicked: {data}"
    
    await send_message(chat_id, response_text)
    await answer_callback_query(callback_query.id, "✅ Action completed!")

async def send_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None):
    """
    Send a message to Telegram chat
    """
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

async def send_message_with_keyboard(chat_id: int, text: str, keyboard_buttons: List[List[Dict]]):
    """
    Send message with inline keyboard
    """
    reply_markup = {
        "inline_keyboard": keyboard_buttons
    }
    return await send_message(chat_id, text, reply_markup)

async def answer_callback_query(callback_query_id: str, text: Optional[str] = None):
    """
    Answer callback query from inline keyboard
    """
    url = f"{TELEGRAM_API_BASE}/answerCallbackQuery"
    data = {"callback_query_id": callback_query_id}
    
    if text:
        data["text"] = text
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            return response.json()
    except Exception as e:
        print(f"Error answering callback query: {e}")
        return None

def create_sample_keyboard():
    """
    Create a sample inline keyboard
    """
    return [
        [
            {"text": "🔵 Button 1", "callback_data": "btn1"},
            {"text": "🟢 Button 2", "callback_data": "btn2"}
        ],
        [
            {"text": "❓ Help", "callback_data": "help"},
            {"text": "ℹ️ About", "callback_data": "about"}
        ]
    ]

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "telegram-bot-webhook"}

# For Vercel deployment
handler = app