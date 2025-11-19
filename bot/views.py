"""
Telegram Bot Webhook Views
"""
import json
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO

from .utils import process_fiscal_check
from users.models import User


def send_telegram_message(chat_id, text, parse_mode='HTML'):
    """
    Send message to user via Telegram Bot API.
    
    Args:
        chat_id: Telegram chat ID
        text: Message text
        parse_mode: Parse mode (HTML, Markdown, etc.)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        print(f"[Telegram] Bot token not configured. Would send to {chat_id}: {text}")
        return False
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"[Telegram] Error sending message: {e}")
        return False


def get_file_from_telegram(file_id):
    """
    Download file from Telegram by file_id.
    
    Args:
        file_id: Telegram file_id
        
    Returns:
        bytes: File content, or None if failed
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        return None
    
    # Get file path from Telegram
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getFile"
    response = requests.get(url, params={'file_id': file_id}, timeout=5)
    
    if not response.ok:
        return None
    
    file_path = response.json().get('result', {}).get('file_path')
    if not file_path:
        return None
    
    # Download file
    file_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getFile?file_path={file_path}"
    file_response = requests.get(file_url, timeout=10)
    
    if file_response.ok:
        # Actually download the file content
        download_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
        file_content = requests.get(download_url, timeout=10)
        if file_content.ok:
            return file_content.content
    
    return None


@csrf_exempt
@require_http_methods(["POST"])
def telegram_webhook(request):
    """
    Main Telegram webhook handler.
    
    Handles incoming updates from Telegram:
    - Text messages (commands)
    - Photos (QR code images)
    - Document uploads (alternative QR code image format)
    """
    try:
        update_data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
    
    # Extract update information
    update = update_data.get('message') or update_data.get('edited_message')
    if not update:
        # Handle other update types (callback_query, etc.) if needed
        return JsonResponse({'ok': True})
    
    chat_id = update.get('chat', {}).get('id')
    telegram_id = update.get('from', {}).get('id')
    
    if not chat_id or not telegram_id:
        return JsonResponse({'ok': False, 'error': 'Missing chat_id or user_id'}, status=400)
    
    # Handle text messages (commands)
    if 'text' in update:
        text = update['text'].strip()
        
        if text.startswith('/start'):
            welcome_message = (
                "👋 Добро пожаловать в систему лояльности AYOQSH!\n\n"
                "📸 Отправьте фото QR-кода с чека для получения кэшбэка.\n\n"
                "Команды:\n"
                "/balance - ваш баланс кэшбэка\n"
                "/help - помощь"
            )
            send_telegram_message(chat_id, welcome_message)
            return JsonResponse({'ok': True})
        
        elif text.startswith('/balance'):
            try:
                user = User.objects.get(telegram_id=telegram_id)
                balance_message = f"💰 Ваш баланс кэшбэка: {user.total_cashback} руб."
            except User.DoesNotExist:
                balance_message = "Вы еще не зарегистрированы. Отправьте фото чека для регистрации."
            
            send_telegram_message(chat_id, balance_message)
            return JsonResponse({'ok': True})
        
        elif text.startswith('/help'):
            help_message = (
                "📖 Помощь\n\n"
                "Отправьте фото QR-кода с чека для автоматического начисления кэшбэка.\n\n"
                "Команды:\n"
                "/start - начать\n"
                "/balance - баланс кэшбэка\n"
                "/help - эта справка"
            )
            send_telegram_message(chat_id, help_message)
            return JsonResponse({'ok': True})
        
        else:
            # Unknown text message
            send_telegram_message(chat_id, "Пожалуйста, отправьте фото QR-кода с чека или используйте команды /start, /balance, /help")
            return JsonResponse({'ok': True})
    
    # Handle photo messages (QR code images)
    if 'photo' in update:
        photos = update['photo']
        if not photos:
            send_telegram_message(chat_id, "Не удалось получить изображение. Попробуйте еще раз.")
            return JsonResponse({'ok': True})
        
        # Get the largest photo (last in the array)
        photo = photos[-1]
        file_id = photo.get('file_id')
        
        if not file_id:
            send_telegram_message(chat_id, "Не удалось получить файл изображения.")
            return JsonResponse({'ok': True})
        
        # Send "Processing..." message
        send_telegram_message(chat_id, "⏳ Обрабатываю чек...")
        
        # Download image from Telegram
        image_content = get_file_from_telegram(file_id)
        if not image_content:
            send_telegram_message(chat_id, "❌ Не удалось загрузить изображение. Попробуйте еще раз.")
            return JsonResponse({'ok': True})
        
        # Create a file-like object from the downloaded content
        image_file = BytesIO(image_content)
        
        # Process the fiscal check
        result = process_fiscal_check(image_file, telegram_id)
        
        # Send result message to user
        send_telegram_message(chat_id, result['message'])
        
        return JsonResponse({'ok': True})
    
    # Handle document uploads (alternative format for images)
    if 'document' in update:
        document = update['document']
        mime_type = document.get('mime_type', '')
        
        # Only process image documents
        if mime_type.startswith('image/'):
            file_id = document.get('file_id')
            
            if not file_id:
                send_telegram_message(chat_id, "Не удалось получить файл изображения.")
                return JsonResponse({'ok': True})
            
            send_telegram_message(chat_id, "⏳ Обрабатываю чек...")
            
            # Download image from Telegram
            image_content = get_file_from_telegram(file_id)
            if not image_content:
                send_telegram_message(chat_id, "❌ Не удалось загрузить изображение. Попробуйте еще раз.")
                return JsonResponse({'ok': True})
            
            # Create a file-like object
            image_file = BytesIO(image_content)
            
            # Process the fiscal check
            result = process_fiscal_check(image_file, telegram_id)
            
            # Send result message to user
            send_telegram_message(chat_id, result['message'])
            
            return JsonResponse({'ok': True})
    
    # Unknown message type
    send_telegram_message(chat_id, "Пожалуйста, отправьте фото QR-кода с чека.")
    return JsonResponse({'ok': True})



