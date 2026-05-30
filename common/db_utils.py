# -*- coding: utf-8 -*-
"""
공통 데이터베이스 유틸리티 모듈

SQLAlchemy 연결 주소 등 다양한 형태의 데이터베이스 연결 주소를 
psycopg가 직접 이해할 수 있는 표준 postgresql 규격으로 정규화하여 제공합니다.
"""

import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def get_clean_db_connection_str() -> str:
    """
    환경 변수에서 DB_CONNECTION 연결 문자열을 가져와 psycopg 형식에 맞게 변환합니다.

    SQLAlchemy가 사용하는 'postgresql+psycopg://...' 형태를
    psycopg3에서 표준 커넥션으로 이해할 수 있는 'postgresql://...' 형태로 정제합니다.

    Returns:
        정제된 PostgreSQL 연결 문자열.

    Raises:
        ValueError: DB_CONNECTION 환경 변수가 설정되지 않은 경우 발생합니다.
    """
    load_dotenv()
    db_conn = os.getenv("DB_CONNECTION")
    if not db_conn:
        logger.error("DB_CONNECTION 환경 변수가 누락되었습니다.")
        raise ValueError("DB_CONNECTION 환경 변수가 설정되지 않았습니다.")

    # psycopg3 직접 연결을 지원하기 위해 SQLAlchemy의 어댑터 접두사(+psycopg)를 표준 접두사로 통일합니다.
    clean_conn = db_conn.replace("postgresql+psycopg", "postgresql")
    return clean_conn
