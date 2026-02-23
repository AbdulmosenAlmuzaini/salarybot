import shutil
import os
from datetime import datetime
from src.config import Config

def backup_db():
    db_path = Config.DATABASE_URL.replace("sqlite:///./", "./")
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found.")
        return

    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/accounting_bot_{timestamp}.db"
    
    shutil.copy2(db_path, backup_file)
    print(f"Backup created: {backup_file}")

if __name__ == "__main__":
    backup_db()
