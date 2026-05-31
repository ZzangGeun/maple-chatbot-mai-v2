# -*- coding: utf-8 -*-
"""
캐릭터 데이터 배치 임베딩 모듈

매일 새벽 4시 character_data/ 디렉토리에 백업된 캐릭터 JSON 데이터 파일들을 가져와
캐릭터별 최신 스탯 정보를 추출한 후, pgvector 데이터베이스에 임베딩을 저장/갱신하고
성공한 파일들을 character_data/archived/ 디렉토리로 아카이빙합니다.
Langfuse Tracing을 연동하여 배치 프로세스의 모든 실행 흐름을 원격으로 추적 및 모니터링합니다.
"""

import os
import re
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

import psycopg
from langchain_core.documents import Document
from ai_server.config import settings
# Langfuse 관측 데코레이터 및 컨텍스트 연동 (버전 호환성 및 오프라인 방어막 구성)
try:
    from langfuse.decorators import observe, langfuse_context
except ImportError:
    try:
        from langfuse import observe, langfuse_context
    except ImportError:
        # Langfuse 패키지가 구버전이거나 존재하지 않는 경우를 대비한 Mock 구현
        def observe(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
        class MockLangfuseContext:
            def update_current_observation(self, *args, **kwargs): pass
            def update_current_trace(self, *args, **kwargs): pass
        langfuse_context = MockLangfuseContext()


from ai_server.rag.embeddings import QwenEmbeddings
from ai_server.rag.vectorstore import get_vectorstore
from ai_server.rag.document_loader import DocumentLoader
from common.db_utils import get_clean_db_connection_str

# 로그 설정 (독립 실행 및 스케줄러 실행 시 진행 상황 모니터링 목적)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("character_batch")

# 프로젝트 루트 디렉토리 계산
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHARACTER_DATA_DIR = BASE_DIR / "data" / "character_data"
ARCHIVE_DIR = CHARACTER_DATA_DIR / "archived"

# 파일명에서 캐릭터 이름과 타임스탬프를 분리하기 위한 패턴입니다.
FILENAME_PATTERN = re.compile(r"^(?P<char_name>.+)_(?P<timestamp>\d{8}_\d{6})\.json$")


def scan_character_files(
    data_dir: Path
) -> Tuple[Dict[str, Tuple[Path, datetime]], Dict[str, List[Path]]]:
    """
    data_dir 내의 캐릭터 JSON 파일들을 스캔하여 캐릭터별 최신 파일 하나와
    모든 파일 목록(아카이빙용)을 함께 반환합니다.
    """
    if not data_dir.exists():
        logger.warning(f"캐릭터 데이터 디렉토리가 존재하지 않습니다: {data_dir.resolve()}")
        return {}, {}
        
    char_files: Dict[str, List[Tuple[Path, datetime]]] = {}
    
    for file_path in data_dir.glob("*.json"):
        match = FILENAME_PATTERN.match(file_path.name)
        if not match:
            continue
            
        char_name = match.group("char_name")
        timestamp_str = match.group("timestamp")
        
        try:
            dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except ValueError:
            logger.warning(f"파일명의 타임스탬프 형식이 맞지 않습니다: {file_path.name}")
            continue
            
        if char_name not in char_files:
            char_files[char_name] = []
        char_files[char_name].append((file_path, dt))
        
    latest_files: Dict[str, Tuple[Path, datetime]] = {}
    all_files_by_char: Dict[str, List[Path]] = {}
    
    for char_name, files in char_files.items():
        files.sort(key=lambda x: x[1], reverse=True)
        latest_files[char_name] = files[0]
        all_files_by_char[char_name] = [f[0] for f in files]
        
    return latest_files, all_files_by_char


def convert_json_to_documents(
    char_name: str, 
    file_path: Path, 
    loader: DocumentLoader
) -> List[Document]:
    """개별 캐릭터 JSON 파일을 RAG에 사용할 수 있는 Document 청크 리스트로 변환합니다."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        md_content = loader._json_to_markdown(data)
        
        metadata = {
            "source": str(file_path),
            "character_name": char_name,
            "type": "character_info",
            "modified_time": os.path.getmtime(file_path),
            "format": "markdown"
        }
        
        doc = Document(page_content=md_content, metadata=metadata)
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
    """벡터 DB에서 특정 캐릭터명에 대한 기존 임베딩 문서들을 일괄 삭제합니다."""
    query = """
        DELETE FROM langchain_pg_embedding
        WHERE collection_id = (
            SELECT uuid FROM langchain_pg_collection WHERE name = %s
        )
        AND cmetadata->>'character_name' = %s
    """
    
    try:
        # psycopg를 사용하여 DB에 직접 쿼리를 날려 삭제 작업을 수행합니다.
        with psycopg.connect(db_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (collection_name, char_name))
                deleted_count = cur.rowcount
                conn.commit()
                logger.info(f"[{char_name}] 기존 임베딩 삭제 완료 (삭제된 레코드 수: {deleted_count})")
    except psycopg.Error as e:
        logger.error(f"[{char_name}] 기존 임베딩 삭제 중 DB 오류 발생: {e}")
        raise


def add_new_embeddings(vectorstore: Any, docs: List[Document]) -> None:
    """새로운 캐릭터 문서 조각(Document)들을 pgvector 저장소에 적재합니다."""
    try:
        vectorstore.add_documents(docs)
        logger.info(f"{len(docs)}개의 새로운 캐릭터 문서 청크 추가 완료")
    except Exception as e:
        logger.error(f"임베딩 추가 중 오류 발생: {e}")
        raise


def archive_processed_file(file_path: Path, archive_dir: Path) -> None:
    """성공적으로 처리된 캐릭터 JSON 파일을 아카이브 디렉토리로 이동시킵니다."""
    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
        dest_path = archive_dir / file_path.name
        shutil.move(str(file_path), str(dest_path))
        logger.info(f"원본 파일 아카이빙 완료: {file_path.name} -> archived/")
    except OSError as e:
        logger.error(f"파일 아카이빙 중 오류 발생 ({file_path.name}): {e}")
        raise


@observe(name="process_single_character")
def process_single_character(
    char_name: str,
    file_path: Path,
    all_files: List[Path],
    loader: DocumentLoader,
    vectorstore: Any,
    db_conn: str,
    coll_name: str
) -> None:
    """
    단일 캐릭터에 대한 배치 데이터 변환, 삭제 및 임베딩 적재 파이프라인을 실행합니다.
    Langfuse Trace 내의 개별 하위 스팬(Span)으로 로깅됩니다.
    """
    logger.info(f"[{char_name}] 처리 시작 - 파일명: {file_path.name}")
    
    # 랭퓨즈에 개별 캐릭터 단위의 모니터링 정보를 태깅합니다.
    langfuse_context.update_current_observation(
        input={"character_name": char_name, "target_file": str(file_path)},
        tags=["character_batch_item"]
    )
    
    # 1. JSON을 Document 리스트로 로드 및 청킹 (가장 최신 파일 1개만 임베딩)
    docs = convert_json_to_documents(char_name, file_path, loader)
    if not docs:
        logger.warning(f"[{char_name}] 유효한 데이터 청크가 생성되지 않아 건너뜁니다.")
        langfuse_context.update_current_observation(output="Skip: No document chunks created")
        return
        
    # 2. 기존 DB 임베딩 삭제
    delete_existing_character_embeddings(db_conn, coll_name, char_name)
    
    # 3. 새로운 임베딩 추가
    add_new_embeddings(vectorstore, docs)
    
    # 4. 해당 캐릭터의 모든 임시 JSON 파일 백업 (과거 파일 누수 방지)
    for f_path in all_files:
        archive_processed_file(f_path, ARCHIVE_DIR)
        
    logger.info(f"[{char_name}] 배치 처리 성공")
    langfuse_context.update_current_observation(
        output=f"Success: Processed {len(docs)} chunks and archived {len(all_files)} files."
    )


@observe(name="character_embedding_batch")
def run_character_embedding_batch() -> None:
    """
    캐릭터 JSON 데이터를 읽어 RAG 시스템에 주기적으로 인덱싱하는 메인 배치 작업입니다.
    FastAPI의 lifespan 스케줄러 또는 단독 쉘 스크립트 실행 시 구동됩니다.
    """
    logger.info("=== 캐릭터 데이터 배치 임베딩 시작 ===")
    
    coll_name = settings.db.collection_name
    
    try:
        # 공통 DB 유틸리티를 적용해 통일된 postgresql 연결 문자열을 확보합니다.
        db_conn = get_clean_db_connection_str()
    except ValueError as e:
        logger.error(str(e))
        langfuse_context.update_current_trace(output="Failure: DB connection configuration missing")
        return
        
    if not coll_name:
        logger.error("COLLECTION_NAME 환경 변수가 설정되지 않았습니다.")
        langfuse_context.update_current_trace(output="Failure: COLLECTION_NAME missing")
        return
        
    # 캐릭터별 최신 파일 및 전체 파일 목록 수집
    latest_files, all_files_by_char = scan_character_files(CHARACTER_DATA_DIR)
    
    # 랭퓨즈 트레이스 정보 업데이트
    langfuse_context.update_current_trace(
        input={"character_count": len(latest_files)},
        tags=["character_batch_main"]
    )
    
    if not latest_files:
        logger.info("처리할 캐릭터 데이터 JSON 파일이 없습니다.")
        logger.info("=== 캐릭터 데이터 배치 임베딩 종료 ===")
        langfuse_context.update_current_trace(output="Success: No files to process")
        return
        
    logger.info(f"총 {len(latest_files)}명의 캐릭터에 대해 신규 데이터 처리를 시작합니다.")
    
    # 의존 모듈 초기화
    loader = DocumentLoader()
    try:
        vectorstore = get_vectorstore()
    except Exception as e:
        logger.error(f"VectorStore 초기화 실패로 배치를 중단합니다: {e}")
        langfuse_context.update_current_trace(output=f"Failure: VectorStore initialization failed ({e})")
        return
        
    success_count = 0
    failure_count = 0
    
    for char_name, (file_path, dt) in latest_files.items():
        try:
            # 개별 캐릭터 작업을 랭퓨즈 하위 스팬 함수로 이관하여 격리된 추적이 되도록 합니다.
            process_single_character(
                char_name=char_name,
                file_path=file_path,
                all_files=all_files_by_char[char_name],
                loader=loader,
                vectorstore=vectorstore,
                db_conn=db_conn,
                coll_name=coll_name
            )
            success_count += 1
        except Exception as e:
            logger.error(f"[{char_name}] 처리 중 에러 발생: {e}. 다음 캐릭터로 넘어갑니다.")
            failure_count += 1
            
    logger.info(f"=== 캐릭터 데이터 배치 임베딩 종료 (성공: {success_count}, 실패: {failure_count}) ===")
    langfuse_context.update_current_trace(
        output=f"Completed batch. Success: {success_count}, Failure: {failure_count}"
    )


if __name__ == "__main__":
    # 이 스크립트가 수동으로 단독 실행되었을 때 배치를 바로 작동시킵니다.
    run_character_embedding_batch()
