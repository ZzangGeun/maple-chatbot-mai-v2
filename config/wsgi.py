"""
WSGI config for MAI project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from django.core.wsgi import get_wsgi_application

# env/.env.local 파일을 우선적으로 로드하고, 없을 경우 루트 .env를 로드합니다.
base_dir = Path(__file__).resolve().parent.parent
env_local = base_dir / "env" / ".env.local"
env_root = base_dir / ".env"

if env_local.exists():
    load_dotenv(dotenv_path=env_local, override=True)
elif env_root.exists():
    load_dotenv(dotenv_path=env_root, override=True)
else:
    load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

application = get_wsgi_application()
