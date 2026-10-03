#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from config.env_loader import load_project_env


def main():
    """Run administrative tasks."""
    # OS 환경변수(docker-compose environment)를 우선하고, 없을 때만 env 파일 값을 사용합니다.
    load_project_env()

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
