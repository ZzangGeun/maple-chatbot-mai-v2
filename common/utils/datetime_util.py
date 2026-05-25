# common/utils/datetime_util.py
"""
날짜/시간 관련 유틸리티

프로젝트 전역에서 사용하는 날짜/시간 포매팅 함수를 모아둡니다.
"""

from datetime import datetime, timedelta


def get_yesterday_str(fmt: str = "%Y-%m-%d") -> str:
    """
    어제 날짜를 포매팅된 문자열로 반환합니다.

    Nexon API의 일부 엔드포인트(랭킹 등)는 date 파라미터에
    전일 날짜를 요구하므로 이 유틸을 사용합니다.

    Args:
        fmt: 날짜 포맷 문자열. 기본값 "%Y-%m-%d".

    Returns:
        포매팅된 어제 날짜 문자열.
    """
    return (datetime.now() - timedelta(days=1)).strftime(fmt)


def format_datetime_kr(dt: datetime | None) -> str:
    """
    datetime 객체를 한국어 표기 형태로 포매팅합니다.

    Args:
        dt: 변환할 datetime 객체. None이면 빈 문자열 반환.

    Returns:
        "2026-05-25 21:00" 형태의 문자열.
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M")


def is_cache_expired(
    file_modified_time: float,
    duration: timedelta = timedelta(hours=1),
) -> bool:
    """
    파일의 수정 시간이 캐시 유효 기간을 초과했는지 확인합니다.

    Args:
        file_modified_time: 파일의 os.path.getmtime() 결과값.
        duration: 캐시 유효 기간. 기본 1시간.

    Returns:
        캐시가 만료되었으면 True.
    """
    modified_dt = datetime.fromtimestamp(file_modified_time)
    return (datetime.now() - modified_dt) >= duration
