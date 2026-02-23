from src.database import SessionLocal, Transaction, User
from datetime import datetime, timedelta, date
import sqlalchemy as sa
import pandas as pd
import io

def get_report_data(user_id: int, days: int = 1):
    db = SessionLocal()
    start_date = date.today() - timedelta(days=days-1)
    
    txns = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date
    ).all()
    
    df = pd.DataFrame([{
        'Type': t.type,
        'Category': t.category,
        'Amount': t.amount,
        'Description': t.description,
        'Date': t.date
    } for t in txns])
    
    db.close()
    return df

# Category translation mapping
CATEGORY_MAP = {
    'food': {'en': 'Food', 'ar': 'طعام'},
    'bills': {'en': 'Bills', 'ar': 'فواتير'},
    'salary': {'en': 'Salary', 'ar': 'راتب'},
    'transport': {'en': 'Transport', 'ar': 'مواصلات'},
    'other': {'en': 'Other', 'ar': 'أخرى'},
    'health': {'en': 'Health', 'ar': 'صحة/طب'},
    'entertainment': {'en': 'Entertainment', 'ar': 'ترفيه'},
    'shopping': {'en': 'Shopping', 'ar': 'تسوق'},
    'fuel': {'en': 'Fuel', 'ar': 'وقود'},
    'rent': {'en': 'Rent', 'ar': 'إيجار'},
    'income': {'en': 'Income', 'ar': 'دخل'},
    'expense': {'en': 'Expense', 'ar': 'مصروف'}
}

HEADER_MAP = {
    'Type': {'en': 'Type', 'ar': 'النوع'},
    'Category': {'en': 'Category', 'ar': 'الفئة'},
    'Amount': {'en': 'Amount', 'ar': 'المبلغ'},
    'Description': {'en': 'Description', 'ar': 'الوصف'},
    'Date': {'en': 'Date', 'ar': 'التاريخ'}
}

def translate(key, lang='en'):
    if not key: return key
    key_lower = key.lower()
    if key_lower in CATEGORY_MAP:
        return CATEGORY_MAP[key_lower].get(lang, key)
    return key

def generate_summary_text(df, lang='en'):
    if df.empty:
        return "No transactions found." if lang == 'en' else "لا توجد معاملات."
    
    income = df[df['Type'] == 'income']['Amount'].sum()
    expense = df[df['Type'] == 'expense']['Amount'].sum()
    balance = income - expense
    
    category_summary = df[df['Type'] == 'expense'].groupby('Category')['Amount'].sum()
    
    cat_lines = []
    for cat, amt in category_summary.items():
        translated_cat = translate(cat, lang)
        cat_lines.append(f"- {translated_cat}: {amt:.2f}")
    cat_text = "\n".join(cat_lines)
    
    if lang == 'en':
        text = (f"📊 *Summary Report*\n\n"
                f"💰 Total Income: {income:.2f}\n"
                f"💸 Total Expense: {expense:.2f}\n"
                f"⚖️ Balance: {balance:.2f}\n\n"
                f"📂 *Category Breakdown (Expenses):*\n{cat_text}")
    else:
        text = (f"📊 *تقرير ملخص*\n\n"
                f"💰 إجمالي الدخل: {income:.2f}\n"
                f"💸 إجمالي المصاريف: {expense:.2f}\n"
                f"⚖️ الرصيد: {balance:.2f}\n\n"
                f"📂 *تصنيف المصاريف:*\n{cat_text}")
    return text

def export_to_excel(df, lang='en'):
    if df.empty:
        return None
        
    # Create a copy for translation
    pdf = df.copy()
    
    # Translate values
    pdf['Type'] = pdf['Type'].apply(lambda x: translate(x, lang))
    pdf['Category'] = pdf['Category'].apply(lambda x: translate(x, lang))
    
    # Translate headers
    pdf.columns = [HEADER_MAP.get(c, {}).get(lang, c) for c in pdf.columns]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pdf.to_excel(writer, index=False, sheet_name='Transactions')
    output.seek(0)
    return output
