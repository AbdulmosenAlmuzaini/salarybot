from src.database import SessionLocal, User
from src.reports import get_report_data, generate_summary_text, export_to_excel
import io

async def today_report(update, context):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    lang = user.language if user else 'en'
    df = get_report_data(user.id, days=1)
    
    # Check if this is a callback query or a message
    if update.message:
        await update.message.reply_text(generate_summary_text(df, lang), parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(generate_summary_text(df, lang), parse_mode='Markdown')
    db.close()

async def week_report(update, context):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    lang = user.language if user else 'en'
    df = get_report_data(user.id, days=7)
    
    if update.message:
        await update.message.reply_text(generate_summary_text(df, lang), parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(generate_summary_text(df, lang), parse_mode='Markdown')
    db.close()

async def month_report(update, context):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    lang = user.language if user else 'en'
    df = get_report_data(user.id, days=30)
    
    if update.message:
        await update.message.reply_text(generate_summary_text(df, lang), parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(generate_summary_text(df, lang), parse_mode='Markdown')
    db.close()

async def export_excel_cmd(update, context):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    df = get_report_data(user.id, days=365) # Export last year
    
    msg_obj = update.message if update.message else update.callback_query.message
    
    if not df.empty:
        excel_file = export_to_excel(df)
        await msg_obj.reply_document(document=excel_file, filename=f"report_{user_id}.xlsx")
    else:
        await msg_obj.reply_text("No data to export." if user.language == 'en' else "لا توجد بيانات للتصدير.")
    db.close()
