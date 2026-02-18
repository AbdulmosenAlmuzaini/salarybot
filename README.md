# Smart AI Accounting Telegram Bot

A personal accounting assistant powered by Groq LLM. It understands natural language in Arabic and English to record income and expenses automatically.

## 🚀 Features
- **Smart AI Extraction**: Just type "Paid 50 for pizza" or "استلمت راتب 8000" and the bot handles the rest.
- **Language Support**: Seamlessly switch between Arabic and English.
- **Automatic Budgeting**: Set a daily limit and get alerts if you exceed it.
- **Reports**: Daily, weekly, and monthly summaries with category breakdowns.
- **Data Export**: Export your transactions to Excel.

## 🛠 Tech Stack
- **AI Engine**: Groq (Llama 3.1)
- **Framework**: python-telegram-bot
- **Database**: SQLAlchemy (SQLite by default)
- **Data Analysis**: Pandas

## 📋 Setup Guide

### 1. Requirements
- Python 3.10+
- Telegram Bot Token ([BotFather](https://t.me/botfather))
- Groq API Key ([Groq Console](https://console.groq.com/))

### 2. Installation
```bash
git clone <repo-url>
cd smart-mezan
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file based on `.env.example`:
```env
TELEGRAM_BOT_TOKEN=your_token
GROQ_API_KEY=your_groq_key
DATABASE_URL=sqlite:///./accounting_bot.db
DEFAULT_MODEL=llama-3.1-70b-versatile
```

### 4. Running the Bot
```bash
python main.py
```

### 5. Database Backups
You can manually trigger a backup or set up a cron job to run:
```bash
python src/backup.py
```
Backups will be stored in the `backups/` directory.

## 🐳 Docker Deployment
```bash
docker-compose up -d --build
```

## 📜 Commands
- `/start`: Start the bot and select language.
- `/setlimit <amount>`: Set your daily spending limit.
- `/today`: Today's summary.
- `/week`: Weekly report.
- `/month`: Monthly report.
- `/export`: Export transactions to Excel.
