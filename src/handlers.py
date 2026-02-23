from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from src.database import SessionLocal, User, Transaction
from src.ai_service import AIService
from src.config import Config
from datetime import datetime, date
import sqlalchemy as sa
import re

ai_service = AIService()

# Multi-language strings for buttons
STRINGS = {
    'en': {
        'main_menu': "Main Menu 🏠",
        'add_btn': "➕ Add Transaction",
        'today_btn': "📊 Today's Summary",
        'reports_btn': "📅 History & Reports",
        'limit_btn': "⚙️ Set Daily Limit",
        'export_btn': "📥 Export Excel",
        'lang_msg': "Language set to English! I'm your AI financial assistant. How can I help you today?",
        'choose_report': "Choose a report period:",
        'today_rep': "Today",
        'week_rep': "Weekly",
        'month_rep': "Monthly",
        'back_btn': "🔙 Back",
        'welcome': "Welcome! I'm your smart accounting assistant. Use the buttons below or just type your transaction naturally.",
        'pending': "⚠️ Your account is pending approval. Please wait for the administrator to authorize you.\nYour ID: {user_id}",
        'not_authorized': "❌ You are not authorized to use this bot.",
        'approved': "✅ You have been approved! You can now use the bot.",
        'admin_only': "⛔ This command is for administrators only.",
        'user_not_found': "User not found.",
        'users_list': "Registered Users:",
        'invalid_number': "Please enter a valid number (e.g., 300 or 150.5)."
    },
    'ar': {
        'main_menu': "القائمة الرئيسية 🏠",
        'add_btn': "➕ إضافة عملية",
        'today_btn': "📊 ملخص اليوم",
        'reports_btn': "📅 التقارير والسجلات",
        'limit_btn': "⚙️ ضبط الحد اليومي",
        'export_btn': "📥 تصدير Excel",
        'lang_msg': "تم ضبط اللغة إلى العربية! أنا مساعدك المالي الذكي. كيف يمكنني مساعدتك اليوم؟",
        'choose_report': "اختر فترة التقرير:",
        'today_rep': "اليوم",
        'week_rep': "أسبوعي",
        'month_rep': "شهري",
        'back_btn': "🔙 عودة",
        'welcome': "مرحباً بك! أنا مساعدك المحاسبي الذكي. ابدأ باستخدام الأزرار أدناه أو اكتب عمليتك بشكل طبيعي.",
        'pending': "⚠️ حسابك قيد الانتظار للموافقة. يرجى الانتظار حتى يقوم المسؤول بتفعيلك.\nرقم التعريف الخاص بك: {user_id}",
        'not_authorized': "❌ غير مسموح لك باستخدام هذا البوت.",
        'approved': "✅ تم تفعيل حسابك بنجاح! يمكنك الآن استخدام البوت.",
        'admin_only': "⛔ هذا الأمر مخصص للمسؤولين فقط.",
        'user_not_found': "المستخدم غير موجود.",
        'users_list': "المستخدمين المسجلين:",
        'invalid_number': "يرجى إدخال رقم صحيح (مثلاً: 300 أو 150.5)."
    }
}

def get_main_menu_keyboard(lang):
    s = STRINGS[lang]
    keyboard = [
        [s['add_btn'], s['today_btn']],
        [s['reports_btn'], s['export_btn']],
        [s['limit_btn']]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    
    if not user:
        # Automatic registration
        is_active = True
        user = User(
            telegram_id=user_id, 
            username=username,
            full_name=full_name,
            language='ar',
            is_active=is_active
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    keyboard = [
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data='lang_ar'),
            InlineKeyboardButton("🇬🇧 English", callback_data='lang_en'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "مرحباً بك! يرجى اختيار اللغة المفضلة:\n\n"
        "Welcome! Please choose your preferred language:",
        reply_markup=reply_markup
    )
    db.close()

async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    lang = 'ar' if query.data == 'lang_ar' else 'en'
    user_id = query.from_user.id
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if user:
        user.language = lang
        db.commit()
    
    s = STRINGS[lang]
    await query.message.reply_text(s['lang_msg'], reply_markup=get_main_menu_keyboard(lang))
    db.close()

async def set_limit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    lang = user.language if user else 'en'
    
    msg = "Please send the daily limit amount (e.g., 300):" if lang == 'en' else "يرجى إرسال قيمة الحد اليومي (مثلاً 300):"
    await update.message.reply_text(msg)
    context.user_data['awaiting_limit'] = True
    db.close()

def get_smart_suggestions(user, extracted_txn):
    lang = user.language
    s = STRINGS[lang]
    keyboard = []
    
    # Context 1: Just added an expense
    if extracted_txn['type'] == 'expense':
        keyboard.append([InlineKeyboardButton(s['today_rep'], callback_data='rep_today')])
        # If expense is large (e.g. > 20% of limit or > 200), suggest limit check
        if extracted_txn['amount'] > 100:
             keyboard.append([InlineKeyboardButton(s['limit_btn'], callback_data='nav_limit')])
             
    # Context 2: Just added income
    elif extracted_txn['type'] == 'income':
        keyboard.append([InlineKeyboardButton(s['month_rep'], callback_data='rep_month')])
        keyboard.append([InlineKeyboardButton(s['export_btn'], callback_data='nav_export')])

    return InlineKeyboardMarkup(keyboard) if keyboard else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        user = User(
            telegram_id=user_id, 
            username=update.effective_user.username,
            full_name=update.effective_user.full_name,
            language='ar',
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    lang = user.language
    s = STRINGS[lang]

    # CHECK IF BUTTON PRESSED (Interrupts any input state)
    all_buttons = []
    for l in STRINGS.values():
        all_buttons.extend([l['add_btn'], l['today_btn'], l['reports_btn'], l['limit_btn'], l['export_btn']])
    
    if text in all_buttons:
        context.user_data['awaiting_limit'] = False # Reset state if button pressed

    # Handle Special Button Actions
    if text == s['today_btn']:
        from src.main_logic import today_report
        await today_report(update, context)
        db.close()
        return

    if text == s['reports_btn']:
        keyboard = [
            [InlineKeyboardButton(s['today_rep'], callback_data='rep_today')],
            [InlineKeyboardButton(s['week_rep'], callback_data='rep_week')],
            [InlineKeyboardButton(s['month_rep'], callback_data='rep_month')]
        ]
        await update.message.reply_text(s['choose_report'], reply_markup=InlineKeyboardMarkup(keyboard))
        db.close()
        return

    if text == s['export_btn']:
        from src.main_logic import export_excel_cmd
        await export_excel_cmd(update, context)
        db.close()
        return

    if text == s['limit_btn']:
        await set_limit_handler(update, context)
        db.close()
        return

    if text == s['add_btn']:
        msg = "Ready! Just describe your transaction (e.g., 'Spent 50 for fuel')" if lang == 'en' else "أنا مستعد! فقط اكتب العملية (مثلاً: 'دفعت 50 بنزين')"
        await update.message.reply_text(msg)
        db.close()
        return

    # Handle "Set Limit" value input
    if context.user_data.get('awaiting_limit'):
        # Clean input: allow commas and dots, remove spaces
        clean_text = text.replace(',', '.').strip()
        try:
            limit = float(clean_text)
            user.daily_limit = limit
            db.commit()
            msg = f"✅ Daily limit set to {limit}" if lang == 'en' else f"✅ تم ضبط الحد اليومي بـ {limit}"
            await update.message.reply_text(msg, reply_markup=get_main_menu_keyboard(lang))
            context.user_data['awaiting_limit'] = False
        except ValueError:
            await update.message.reply_text(s['invalid_number'])
        db.close()
        return

    # Default: Natural Language Processing
    status_msg = await update.message.reply_text("Processing... ⏳" if lang == 'en' else "جاري المعالجة... ⏳")

    extracted = ai_service.parse_transaction(text, lang)
    
    if extracted:
        try:
            txn_date = datetime.strptime(extracted['date'], '%Y-%m-%d').date()
            new_txn = Transaction(
                user_id=user.id,
                type=extracted['type'],
                category=extracted['category'],
                amount=float(extracted['amount']),
                description=extracted['description'],
                date=txn_date
            )
            db.add(new_txn)
            db.commit()

            # Logic for over-limit alert
            alert_text = None
            if extracted['type'] == 'expense' and user.daily_limit > 0:
                today_date = date.today()
                total_spent = db.query(sa.func.sum(Transaction.amount)).filter(
                    Transaction.user_id == user.id,
                    Transaction.type == 'expense',
                    Transaction.date == today_date
                ).scalar() or 0.0
                
                if total_spent > user.daily_limit:
                    diff = total_spent - user.daily_limit
                    alert_text = f"\n⚠️ You exceeded your daily limit by {diff:.2f}" if lang == 'en' else f"\n⚠️ لقد تجاوزت حدك اليومي بـ {diff:.2f}"

            # Prepare confirmation message
            from src.reports import translate
            translated_cat = translate(extracted['category'], lang)
            conf_msg = (f"✅ Recorded: {extracted['type'].capitalize()} - {extracted['amount']} "
                       f"({translated_cat})\n{extracted['description']}") if lang == 'en' else \
                       (f"✅ تم تسجيل: {translate(extracted['type'], lang)} - {extracted['amount']} "
                       f"({translated_cat})\n{extracted['description']}")
            
            if alert_text:
                conf_msg += alert_text

            # SMART PREDICTION: Suggest next steps
            suggestions = get_smart_suggestions(user, extracted)
            
            await status_msg.edit_text(conf_msg, reply_markup=suggestions)
        except Exception as e:
            print(f"DEBUG - Error saving txn: {e}")
            await status_msg.edit_text("Error processing entry." if lang == 'en' else "حدث خطأ أثناء المعالجة.")
    else:
        print(f"DEBUG - Parsing failed for: {text}")
        await status_msg.edit_text("I didn't understand. Please be more specific." if lang == 'en' else "لم أفهم العملية. يرجى التوضيح أكثر.")
    
    db.close()

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != Config.ADMIN_ID:
        await update.message.reply_text(STRINGS['ar']['admin_only'])
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /approve <telegram_id>")
        return
    
    try:
        target_id = int(context.args[0])
        db = SessionLocal()
        user = db.query(User).filter(User.telegram_id == target_id).first()
        if user:
            user.is_active = True
            db.commit()
            await update.message.reply_text(f"✅ User {target_id} approved.")
            # Notify user
            try:
                await context.bot.send_message(chat_id=target_id, text=STRINGS[user.language]['approved'], reply_markup=get_main_menu_keyboard(user.language))
            except Exception:
                pass
        else:
            await update.message.reply_text("User not found.")
        db.close()
    except ValueError:
        await update.message.reply_text("Invalid ID.")

async def admin_deny(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != Config.ADMIN_ID:
        await update.message.reply_text(STRINGS['ar']['admin_only'])
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /deny <telegram_id>")
        return
    
    try:
        target_id = int(context.args[0])
        db = SessionLocal()
        user = db.query(User).filter(User.telegram_id == target_id).first()
        if user:
            user.is_active = False
            db.commit()
            await update.message.reply_text(f"❌ User {target_id} denied.")
        else:
            await update.message.reply_text("User not found.")
        db.close()
    except ValueError:
        await update.message.reply_text("Invalid ID.")

async def admin_list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != Config.ADMIN_ID:
        await update.message.reply_text(STRINGS['ar']['admin_only'])
        return
    
    db = SessionLocal()
    users = db.query(User).all()
    if not users:
        await update.message.reply_text("No users registered.")
    else:
        msg = "📋 Registered Users:\n\n"
        for u in users:
            status = "✅" if u.is_active else "⏳"
            msg += f"{status} {u.telegram_id} - @{u.username or 'N/A'} ({u.full_name or 'N/A'})\n"
        await update.message.reply_text(msg)
    db.close()
