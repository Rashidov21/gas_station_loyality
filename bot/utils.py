"""
Core utility functions for processing fiscal checks
"""
import requests
from io import BytesIO
from datetime import datetime, timezone
from decimal import Decimal
from PIL import Image
from pyzbar import pyzbar
import json

from django.conf import settings
from django.utils import timezone as django_timezone
from django.db import transaction

from bot.models import Check, Visit
from users.models import User
from cashback.models import Settings
from cashback.utils import calculate_cashback


def read_qr_code_from_image(image_file):
    """
    Extract QR code URL from uploaded image file.
    
    Args:
        image_file: Django uploaded file or file-like object
        
    Returns:
        str: URL extracted from QR code, or None if not found
    """
    try:
        # Read image
        if hasattr(image_file, 'read'):
            image_data = image_file.read()
        else:
            image_data = image_file
        
        # Open image with PIL
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary (pyzbar requires RGB)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Decode QR codes
        qr_codes = pyzbar.decode(image)
        
        if not qr_codes:
            return None
        
        # Return the first QR code data (assuming it's the fiscal check URL)
        qr_data = qr_codes[0].data.decode('utf-8')
        return qr_data
        
    except Exception as e:
        print(f"Error reading QR code: {e}")
        return None


def fetch_fiscal_check_data(url):
    """
    Fetch fiscal check data from the URL extracted from QR code.
    
    Args:
        url: URL from QR code pointing to fiscal check API
        
    Returns:
        dict: Contains 'amount', 'datetime', 'fiskal_id', 'source_url', 'raw_data'
              Returns None if fetch fails
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse JSON response (adjust based on actual API format)
        data = response.json()
        
        # Extract required fields (adjust field names based on actual API)
        # This is a template - adjust based on your fiscal check API structure
        fiskal_id = data.get('RRN') or data.get('FISKAL_NO') or data.get('fiskal_id') or data.get('id')
        amount_str = data.get('amount') or data.get('total') or data.get('sum')
        datetime_str = data.get('datetime') or data.get('date') or data.get('created_at')
        
        # Convert amount to Decimal
        try:
            amount = Decimal(str(amount_str))
        except (ValueError, TypeError):
            return None
        
        # Parse datetime (adjust format based on API)
        try:
            if isinstance(datetime_str, str):
                # Try common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%d.%m.%Y %H:%M:%S']:
                    try:
                        check_datetime = datetime.strptime(datetime_str, fmt)
                        if check_datetime.tzinfo is None:
                            check_datetime = django_timezone.make_aware(check_datetime)
                        break
                    except ValueError:
                        continue
                else:
                    return None
            else:
                check_datetime = django_timezone.now()
        except Exception:
            check_datetime = django_timezone.now()
        
        return {
            'amount': amount,
            'datetime': check_datetime,
            'fiskal_id': str(fiskal_id),
            'source_url': url,
            'raw_data': data,
        }
        
    except Exception as e:
        print(f"Error fetching fiscal check data: {e}")
        return None


def validate_fiscal_check(fiskal_id, check_datetime, telegram_id):
    """
    Validate fiscal check against business rules.
    
    Args:
        fiskal_id: Unique fiscal check ID
        check_datetime: DateTime of the check
        telegram_id: Telegram ID of the user
        
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    # 1. Duplicate Check: Verify the Unique Fiscal ID
    if Check.objects.filter(fiskal_id=fiskal_id).exists():
        return False, "Этот чек уже был обработан ранее."
    
    # 2. Date Check: Reject if the check date is not today
    today = django_timezone.now().date()
    check_date = check_datetime.date() if hasattr(check_datetime, 'date') else check_datetime.date()
    
    if check_date != today:
        return False, f"Чек должен быть сегодняшним. Дата чека: {check_date}."
    
    # 3. Limits Check: Enforce daily max checks per user
    try:
        user = User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        # User will be created later, so we can't check limits yet
        # We'll check after user creation
        pass
    else:
        # Get daily limit from settings
        try:
            daily_limit_setting = Settings.objects.get(key='daily_check_limit')
            daily_limit = int(daily_limit_setting.value)
        except Settings.DoesNotExist:
            daily_limit = 10  # Default limit
        
        # Count today's checks for this user
        today_start = django_timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_checks_count = Check.objects.filter(
            user=user,
            created_at__gte=today_start
        ).count()
        
        if today_checks_count >= daily_limit:
            return False, f"Достигнут лимит чеков на сегодня ({daily_limit}). Попробуйте завтра."
    
    return True, None


@transaction.atomic
def process_fiscal_check(image_file, telegram_id):
    """
    Main function to process fiscal check from QR code image.
    
    Steps:
    1. QR Read (Pyzbar) -> Extract URL
    2. URL Fetch -> Get fiscal check data
    3. Data Extraction -> Parse amount, datetime, fiscal ID
    4. Validation -> Duplicate check, date check, limits check
    5. Model Save -> Update User, Check, Visit models
    6. Cashback Calculation -> Apply loyalty rules
    7. Return result for Telegram confirmation
    
    Args:
        image_file: Django uploaded file containing QR code image
        telegram_id: Telegram user ID (int or str)
        
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'check': Check instance or None,
            'cashback': Decimal or None,
        }
    """
    telegram_id = int(telegram_id)
    
    # Step 1: Read QR code from image
    qr_url = read_qr_code_from_image(image_file)
    if not qr_url:
        return {
            'success': False,
            'message': 'Не удалось распознать QR-код на изображении. Пожалуйста, убедитесь, что фото четкое и содержит QR-код чека.',
            'check': None,
            'cashback': None,
        }
    
    # Step 2: Fetch fiscal check data from URL
    check_data = fetch_fiscal_check_data(qr_url)
    if not check_data:
        return {
            'success': False,
            'message': 'Не удалось получить данные чека по QR-коду. Проверьте, что чек действителен.',
            'check': None,
            'cashback': None,
        }
    
    # Step 3: Validation
    is_valid, error_message = validate_fiscal_check(
        check_data['fiskal_id'],
        check_data['datetime'],
        telegram_id
    )
    
    if not is_valid:
        return {
            'success': False,
            'message': error_message,
            'check': None,
            'cashback': None,
        }
    
    # Step 4: Get or create user
    user, created = User.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'registration_date': django_timezone.now(),
        }
    )
    
    # Re-check daily limit after user creation (if user was just created)
    if created:
        try:
            daily_limit_setting = Settings.objects.get(key='daily_check_limit')
            daily_limit = int(daily_limit_setting.value)
        except Settings.DoesNotExist:
            daily_limit = 10
        
        today_start = django_timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_checks_count = Check.objects.filter(
            user=user,
            created_at__gte=today_start
        ).count()
        
        if today_checks_count >= daily_limit:
            return {
                'success': False,
                'message': f'Достигнут лимит чеков на сегодня ({daily_limit}). Попробуйте завтра.',
                'check': None,
                'cashback': None,
            }
    
    # Step 5: Calculate cashback
    cashback_amount = calculate_cashback(check_data['amount'])
    
    # Step 6: Save Check
    check = Check.objects.create(
        user=user,
        fiskal_id=check_data['fiskal_id'],
        amount=check_data['amount'],
        datetime=check_data['datetime'],
        source_url=check_data['source_url'],
        cashback_amount=cashback_amount,
        raw_data=check_data['raw_data'],
    )
    
    # Step 7: Create Visit
    visit = Visit.objects.create(
        user=user,
        check=check,
    )
    
    # Step 8: Update user's total cashback
    user.total_cashback += cashback_amount
    user.save()
    
    # Step 9: Prepare success message
    message = (
        f"✅ Чек успешно обработан!\n\n"
        f"💰 Сумма чека: {check_data['amount']} руб.\n"
        f"🎁 Кэшбэк: {cashback_amount} руб.\n"
        f"📊 Ваш общий кэшбэк: {user.total_cashback} руб.\n\n"
        f"Спасибо за покупку!"
    )
    
    return {
        'success': True,
        'message': message,
        'check': check,
        'cashback': cashback_amount,
    }

