# AYOQSH Gas Station Loyalty System

A robust, fully automated loyalty and cashback system for Gas Station Network (AYOQSH) built with Django.

## Features

- 🤖 **Telegram Bot Integration**: Customers send QR code photos from fiscal checks via Telegram
- 🔍 **QR Code Recognition**: Automated QR code scanning using Pyzbar
- ✅ **Fiscal Check Validation**: Duplicate detection, date validation, and daily limits
- 💰 **Automated Cashback Calculation**: Flexible rule-based cashback system
- 📊 **Admin Dashboard**: Real-time statistics and monitoring (HTML/Tailwind CSS)
- 🔒 **SQLite3 Database**: Reliable data storage (default, can be switched to PostgreSQL)

## Tech Stack

- **Backend**: Django 5.0+
- **Frontend (Admin)**: Django Templates + Tailwind CSS (CDN)
- **Database**: SQLite3 (default)
- **Bot**: Telegram Bot API (via requests)
- **QR Scanning**: Pyzbar
- **Image Processing**: Pillow (PIL)

## Project Structure

```
gas_station_loyalty/
├── core/               # Django project settings and configs
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/              # User management app
│   ├── models.py       # User model
│   └── admin.py
├── bot/                # Telegram bot integration
│   ├── views.py        # Webhook handler
│   ├── models.py       # Check, Visit models
│   └── utils.py        # Core processing logic
├── cashback/           # Cashback rules and calculation
│   ├── models.py       # CashbackRule, Settings models
│   └── utils.py        # Cashback calculation logic
├── admin_panel/        # Admin dashboard
│   ├── views.py        # Dashboard view
│   └── urls.py
├── templates/          # HTML templates
│   └── admin_panel/
└── manage.py
```

## Installation

### 1. Prerequisites

- Python 3.10+
- Telegram Bot Token (create bot via [@BotFather](https://t.me/BotFather))

**Note**: SQLite3 is included with Python, so no additional database setup is required. For production, you may want to switch to PostgreSQL.

### 2. Setup

```bash
# Clone the repository
git clone <repository-url>
cd gas_station_loyalty

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env file with your settings
# - Set SECRET_KEY
# - Configure database credentials
# - Add TELEGRAM_BOT_TOKEN
```

### 3. Database Setup

```bash
# Run migrations (SQLite3 database will be created automatically)
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

**Note**: The SQLite3 database file (`db.sqlite3`) will be created automatically in the project root directory.

### 4. Configure Telegram Webhook

```bash
# Set webhook URL (replace with your domain and token)
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/bot/webhook/"}'
```

### 5. Initial Settings

Create initial settings in Django admin:

1. Go to `/admin/`
2. Navigate to **Cashback > Settings**
3. Add setting with key `daily_check_limit` and value (e.g., `10`)

## Usage

### For Customers (Telegram Bot)

1. Fuel up at AYOQSH gas station
2. Receive fiscal check with QR code
3. Open Telegram bot
4. Send photo of QR code
5. Receive automatic cashback confirmation

**Bot Commands:**
- `/start` - Welcome message
- `/balance` - Check cashback balance
- `/help` - Help information

### For Admins

- **Admin Panel**: `/admin/` - Django admin interface
- **Dashboard**: `/` - Custom dashboard with statistics

## Core Workflow

1. **Customer sends QR code photo** → Telegram webhook receives update
2. **QR Code Extraction** → Pyzbar reads QR code, extracts URL
3. **Fiscal Check Data Fetch** → System fetches check data from URL
4. **Validation**:
   - Check for duplicate `fiskal_id`
   - Verify check date is today
   - Enforce daily check limit per user
5. **Cashback Calculation** → Apply active `CashbackRule` rules
6. **Database Update** → Save `Check`, create `Visit`, update `User.total_cashback`
7. **Confirmation** → Send message to user via Telegram

## Models

### User
- `telegram_id` (unique)
- `phone`, `car_name`, `car_number`
- `total_cashback`

### Check
- `user` (ForeignKey)
- `fiskal_id` (unique)
- `amount`, `datetime`
- `cashback_amount`
- `source_url`

### CashbackRule
- `rule_type`: fixed, percentage, tiered
- `threshold`, `cash_amount`, `percentage`
- `priority`, `is_active`

### Settings
- `key`, `value`, `description`

## Customization

### Fiscal Check API Integration

Edit `bot/utils.py` → `fetch_fiscal_check_data()` function to match your fiscal check API response format:

```python
# Adjust field names based on your API
fiskal_id = data.get('RRN') or data.get('FISKAL_NO')  # Your field
amount_str = data.get('amount')  # Your field
datetime_str = data.get('datetime')  # Your field
```

### Cashback Rules

Create rules in Django admin (`/admin/cashback/cashbackrule/`):

- **Fixed**: Give fixed amount (e.g., 50₽ per check)
- **Percentage**: Give percentage (e.g., 5% of check amount)
- **Tiered**: Apply rule only if check amount >= threshold

## Development

```bash
# Run development server
python manage.py runserver

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Configure `ALLOWED_HOSTS`
3. Consider switching to PostgreSQL for production (update `DATABASES` in `core/settings.py`)
4. Configure static files serving
5. Set up SSL certificate for webhook
6. Configure webhook URL in Telegram

## License

Proprietary - AYOQSH Gas Station Network

