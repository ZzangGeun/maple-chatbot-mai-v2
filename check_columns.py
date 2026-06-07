import os
from pathlib import Path
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent
env_local = base_dir / "env" / ".env.local"
env_root = base_dir / ".env"
if env_local.exists():
    load_dotenv(dotenv_path=env_local, override=True)
elif env_root.exists():
    load_dotenv(dotenv_path=env_root, override=True)
else:
    load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.db import connection

def check():
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'chat_chatmessage';")
        columns = cursor.fetchall()
        print("Columns in chat_chatmessage:", [col[0] for col in columns])

if __name__ == '__main__':
    check()
