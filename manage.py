#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def main():
    """Run administrative tasks."""
    # env/.env.local 파일을 우선적으로 로드하고, 없을 경우 루트 .env를 로드합니다.
    base_dir = Path(__file__).resolve().parent
    env_local = base_dir / "env" / ".env.local"
    env_root = base_dir / ".env"

    if env_local.exists():
        load_dotenv(dotenv_path=env_local, override=True)
    elif env_root.exists():
        load_dotenv(dotenv_path=env_root, override=True)
    else:
        load_dotenv()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
