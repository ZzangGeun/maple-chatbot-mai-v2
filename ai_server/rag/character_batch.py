# -*- coding: utf-8 -*-
"""
캐릭터 데이터 배치 임베딩 모듈

매일 새벽 4시 character_data/ 디렉토리에 백업된 캐릭터 JSON 데이터 파일들을 가져와
캐릭터별 최신 스탯 정보를 추출한 후, pgvector 데이터베이스에 임베딩을 저장/갱신하고
성공한 파일들을 character_data/archived/ 디렉토리로 아카이빙합니다.
"""

import os
import re
import glob
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

import psycopg
from dotenv import load_dotenv
from langchain_core.documents import Document

from ai_server.rag.embeddings import QwenEmbeddings
from ai_server.rag.vectorstore import get_vectorstore
from ai_server.rag.document_loader import DocumentLoader

# 로그 설정 (독립 실행 및 스케줄러 실행 시 진행 상황 모니터링 목적)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("character_batch")

# 프로젝트 루트 디렉토리 계산
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHARACTER_DATA_DIR = BASE_DIR / "character_data"
ARCHIVE_DIR = CHARACTER_DATA_DIR / "archived"

# 파일명에서 캐릭터 이름과 타임스탬프를 분리하기 위한 패턴입니다.
# 캐릭터명 자체에 숫자, 특수문자, 공백이 포함될 수 있으므로, 
# 고정된 날짜 및 시간 포맷(YYYYMMDD_HHMMSS)을 가진 뒷부분을 기준으로 매칭합니다.
FILENAME_PATTERN = re.compile(r"^(?P<char_name>.+)_(?P<timestamp>\d{8}_\d{6})\.json$")


def scan_character_files(
    data_dir: Path
) -> Tuple[Dict[str, Tuple[Path, datetime]], Dict[str, List[Path]]]:
    """
    data_dir 내의 캐릭터 JSON 파일들을 스캔하여 캐릭터별 최신 파일 하나와
    모든 파일 목록(아카이빙용)을 함께 반환합니다.
    
    Args:
        data_dir: JSON 파일들이 저장된 디렉토리 경로
        
    Returns:
        튜플: (
            { 캐릭터명: (최신 파일 경로, 파일의 생성/수정 datetime) },
            { 캐릭터명: [해당 캐릭터의 모든 파일 경로 리스트] }
        )
    """
    if not data_dir.exists():
        logger.warning(f"캐릭터 데이터 디렉토리가 존재하지 않습니다: {data_dir.resolve()}")
        return {}, {}
        
    char_files: Dict[str, List[Tuple[Path, datetime]]] = {}
    
    # 디렉토리 내의 모든 .json 파일을 검색합니다.
    for file_path in data_dir.glob("*.json"):
        match = FILENAME_PATTERN.match(file_path.name)
        if not match:
            # 패턴과 일치하지 않는 파일(예: 메타정보 파일 등)은 무시합니다.
            continue
            
        char_name = match.group("char_name")
        timestamp_str = match.group("timestamp")
        
        try:
            # 파일명에 포함된 시간 정보를 datetime 객체로 변환하여 선후 관계를 비교할 수 있게 합니다.
            dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except ValueError:
            logger.warning(f"파일명의 타임스탬프 형식이 맞지 않습니다: {file_path.name}")
            continue
            
        if char_name not in char_files:
            char_files[char_name] = []
        char_files[char_name].append((file_path, dt))
        
    # 캐릭터별로 가장 최신의 파일 1개를 식별하고 전체 파일 리스트도 정리합니다.
    latest_files: Dict[str, Tuple[Path, datetime]] = {}
    all_files_by_char: Dict[str, List[Path]] = {}
    
    for char_name, files in char_files.items():
        # datetime 기준 내림차순 정렬
        files.sort(key=lambda x: x[1], reverse=True)
        latest_files[char_name] = files[0]
        all_files_by_char[char_name] = [f[0] for f in files]
        
    return latest_files, all_files_by_char


def convert_json_to_documents(
    char_name: str, 
    file_path: Path, 
    loader: DocumentLoader
) -> List[Document]:
    """
    개별 캐릭터 JSON 파일을 RAG에 사용할 수 있는 Document 청크 리스트로 변환합니다.
    
    Args:
        char_name: 캐릭터명
        file_path: 캐릭터 JSON 파일 경로
        loader: Markdown 변환 및 텍스트 분할에 사용할 DocumentLoader 인스턴스
        
    Returns:
        분할된 Document 객체 리스트
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 기존 RAG 문서와 규격을 맞추기 위해 DocumentLoader의 JSON to Markdown 변환 로직을 재사용합니다.
        md_content = loader._json_to_markdown(data)
        
        # pgvector 내에서 갱신 및 삭제 대상을 조회할 수 있도록 메타데이터에 식별자를 포함시킵니다.
        metadata = {
            "source": str(file_path),
            "character_name": char_name,
            "type": "character_info",
            "modified_time": os.path.getmtime(file_path),
            "format": "markdown"
        }
        
        doc = Document(page_content=md_content, metadata=metadata)
        
        # 텍스트 스플리터를 사용해 설정된 크기 단위로 쪼갭니다.
        splits = loader.text_splitter.split_documents([doc])
        return splits
        
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"파일을 읽고 Document로 변환하는 중 오류 발생 ({file_path}): {e}")
        return []


def delete_existing_character_embeddings(
    db_conn_str: str, 
    collection_name: str, 
    char_name: str
) -> None:
    """
    벡터 DB에서 특정 캐릭터명에 대한 기존 임베딩 문서들을 일괄 삭제합니다.
    캐릭터 스탯 정보 갱신 시 과거 정보와 섞여 RAG 답변이 왜곡되는 문제를 방지하기 위함입니다.
    
    Args:
        db_conn_str: 데이터베이스 연결 문자열
        collection_name: 벡터 컬렉션 이름
        char_name: 지우고자 하는 캐릭터명
    """
    # psycopg는 postgresql+psycopg 형식을 직접 파싱하지 못하므로 표준 postgresql 형식으로 변환합니다.
    clean_conn_str = db_conn_str.replace("postgresql+psycopg", "postgresql")
    
    query = """
        DELETE FROM langchain_pg_embedding
        WHERE collection_id = (
            SELECT uuid FROM langchain_pg_collection WHERE name = %s
        )
        AND cmetadata->>'character_name' = %s
    """
    
    try:
        # psycopg를 사용하여 DB에 직접 쿼리를 날려 삭제 작업을 수행합니다.
        with psycopg.connect(clean_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (collection_name, char_name))
                deleted_count = cur.rowcount
                conn.commit()
                logger.info(f"[{char_name}] 기존 임베딩 삭제 완료 (삭제된 레코드 수: {deleted_count})")
    except psycopg.Error as e:
        logger.error(f"[{char_name}] 기존 임베딩 삭제 중 DB 오류 발생: {e}")
        # 예외를 상위로 전파하여 실패한 캐릭터 데이터가 아카이빙되지 않도록 합니다.
        raise


def add_new_embeddings(vectorstore: Any, docs: List[Document]) -> None:
    """
    새로운 캐릭터 문서 조각(Document)들을 pgvector 저장소에 적재합니다.
    
    Args:
        vectorstore: PGVector 인스턴스
        docs: 추가할 Document 리스트
    """
    try:
        vectorstore.add_documents(docs)
        logger.info(f"{len(docs)}개의 새로운 캐릭터 문서 청크 추가 완료")
    except Exception as e:
        logger.error(f"임베딩 추가 중 오류 발생: {e}")
        raise


def archive_processed_file(file_path: Path, archive_dir: Path) -> None:
    """
    성공적으로 처리된 캐릭터 JSON 파일을 아카이브 디렉토리로 이동시킵니다.
    이를 통해 다음 배치 시 중복 처리되는 것을 방지합니다.
    
    Args:
        file_path: 원본 파일 경로
        archive_dir: 이동할 아카이브 디렉토리 경로
    """
    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
        dest_path = archive_dir / file_path.name
        
        # 대상 경로에 이미 동일한 이름의 파일이 존재한다면,
        # 과거에 실행되었던 백업본이므로 덮어씁니다.
        shutil.move(str(file_path), str(dest_path))
        logger.info(f"원본 파일 아카이빙 완료: {file_path.name} -> archived/")
    except OSError as e:
        logger.error(f"파일 아카이빙 중 오류 발생 ({file_path.name}): {e}")
        raise


def run_character_embedding_batch() -> None:
    """
    캐릭터 JSON 데이터를 읽어 RAG 시스템에 주기적으로 인덱싱하는 메인 배치 작업입니다.
    """
    logger.info("=== 캐릭터 데이터 배치 임베딩 시작 ===")
    
    load_dotenv()
    db_conn = os.getenv("DB_CONNECTION")
    coll_name = os.getenv("COLLECTION_NAME")
    
    if not db_conn or not coll_name:
        logger.error("DB_CONNECTION 또는 COLLECTION_NAME 환경 변수가 설정되지 않았습니다.")
        return
        
    # 캐릭터별 최신 파일 및 전체 파일 목록 수집
    latest_files, all_files_by_char = scan_character_files(CHARACTER_DATA_DIR)
    if not latest_files:
        logger.info("처리할 캐릭터 데이터 JSON 파일이 없습니다.")
        logger.info("=== 캐릭터 데이터 배치 임베딩 종료 ===")
        return
        
    logger.info(f"총 {len(latest_files)}명의 캐릭터에 대해 신규 데이터 처리를 시작합니다.")
    
    # 의존 모듈 초기화
    loader = DocumentLoader()
    try:
        vectorstore = get_vectorstore()
    except Exception as e:
        logger.error(f"VectorStore 초기화 실패로 배치를 중단합니다: {e}")
        return
        
    success_count = 0
    failure_count = 0
    
    for char_name, (file_path, dt) in latest_files.items():
        logger.info(f"[{char_name}] 처리 시작 - 파일명: {file_path.name} (생성일: {dt})")
        
        try:
            # 1. JSON을 Document 리스트로 로드 및 청킹 (가장 최신 파일 1개만 임베딩)
            docs = convert_json_to_documents(char_name, file_path, loader)
            if not docs:
                logger.warning(f"[{char_name}] 유효한 데이터 청크가 생성되지 않아 건너뜁니다.")
                failure_count += 1
                continue
                
            # 2. 기존 DB 임베딩 삭제 (트랜잭션 안전하게 처리)
            delete_existing_character_embeddings(db_conn, coll_name, char_name)
            
            # 3. 새로운 임베딩 추가
            add_new_embeddings(vectorstore, docs)
            
            # 4. 해당 캐릭터의 모든 임시 JSON 파일 백업 (오래된 과거 파일 누수 방지)
            for f_path in all_files_by_char[char_name]:
                archive_processed_file(f_path, ARCHIVE_DIR)
            
            success_count += 1
            logger.info(f"[{char_name}] 배치 처리 성공")
            
        except Exception as e:
            logger.error(f"[{char_name}] 처리 중 에러 발생: {e}. 다음 캐릭터로 넘어갑니다.")
            failure_count += 1
            
    logger.info(f"=== 캐릭터 데이터 배치 임베딩 종료 (성공: {success_count}, 실패: {failure_count}) ===")


if __name__ == "__main__":
    # 이 스크립트가 수동으로 단독 실행되었을 때 배치를 바로 작동시킵니다.
    run_character_embedding_batch()
