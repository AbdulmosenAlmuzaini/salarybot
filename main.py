import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from src.config import Config
from src.database import init_db
from src.handlers import start, language_choice, set_limit_handler, handle_message, admin_approve, admin_deny, admin_list_users
from src.reports import get_report_data, generate_summary_text, export_to_excel
from src.database import SessionLocal, User
import io

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

from src.main_logic import today_report, week_report, month_report, export_excel_cmd

async def report_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'rep_today':
        await today_report(update, context)
    elif query.data == 'rep_week':
        await week_report(update, context)
    elif query.data == 'rep_month':
        await month_report(update, context)
    elif query.data == 'nav_limit':
        from src.handlers import set_limit_handler
        await set_limit_handler(update, context)
    elif query.data == 'nav_export':
        await export_excel_cmd(update, context)

if __name__ == '__main__':
    # Initialize DB
    init_db()
    
    # Build application
    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(language_choice, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(report_callback, pattern='^(rep_|nav_)'))
    application.add_handler(CommandHandler('setlimit', set_limit_handler))
    application.add_handler(CommandHandler('today', today_report))
    application.add_handler(CommandHandler('week', week_report))
    application.add_handler(CommandHandler('month', month_report))
    application.add_handler(CommandHandler('report', month_report))
    application.add_handler(CommandHandler('export', export_excel_cmd))
    
    # Admin commands
    application.add_handler(CommandHandler('approve', admin_approve))
    application.add_handler(CommandHandler('deny', admin_deny))
    application.add_handler(CommandHandler('users', admin_list_users))
    
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is running...")
    application.run_polling()
