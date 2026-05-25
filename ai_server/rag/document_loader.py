# -*- coding: utf-8 -*-
"""
문서 로더 및 전처리

외부 파일이나 데이터베이스에서 문서를 로드하고 청크로 분할하여 저장합니다.
JSON 파일의 다양한 key-value 구조를 재귀적으로 Markdown으로 변환합니다.
"""

import logging
import json
import os
import glob
from pathlib import Path
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# 로그 설정
logger = logging.getLogger(__name__)


class DocumentLoader:
    """JSON 문서를 로드하고 Markdown으로 변환하여 청킹하는 클래스"""
    
    # 변환 시 건너뛸 필드들 (URL, 아이콘, 이미지 등 RAG에 불필요한 데이터)
    SKIP_KEYS: set = {
        "icon", "shape_icon", "character_image", "source",  # 이미지/아이콘 URL
        "date_expire", "freestyle_flag", "date",  # 메타데이터
    }
    
    # 값이 의미 없는 경우 건너뛸 값들
    SKIP_VALUES: set = {None, "", "null", "0", "none", "미적용", "미사용"}
    
    def __init__(
        self, 
        data_dir: str = "./rag_documents",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        DocumentLoader 초기화

        Args:
            data_dir: RAG 문서가 저장된 디렉토리 경로
            chunk_size: 청크 크기 (기본값 500자)
            chunk_overlap: 청크 간 중첩 크기 (기본값 50자)
        """
        self.data_dir = data_dir
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n##", "\n#", "\n", " ", ""]
        )
    
    def _should_skip_key(self, key: str) -> bool:
        key_lower = key.lower()
        # 정확히 일치하거나 URL/이미지 관련 키 패턴인 경우 건너뜀
        if key_lower in self.SKIP_KEYS:
            return True
        if any(pattern in key_lower for pattern in ["_icon", "_image", "_url", "http"]):
            return True
        return False
    
    def _should_skip_value(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            # URL인 경우 건너뜀
            if value.startswith(("http://", "https://")):
                return True
            # 빈 문자열 또는 의미 없는 값인 경우 건너뜀
            if value.strip().lower() in {"", "null", "none", "0"}:
                return True
        return False
    
    def _format_key(self, key: str) -> str:
        # 언더스코어를 공백으로 변환하고 타이틀 케이스 적용
        return key.replace("_", " ").title()

    def _process_list(self, data_list: List[Any], level: int) -> str:
        """리스트 타입의 데이터를 Markdown 불렛 포인트로 변환"""
        lines = []
        for item in data_list:
            if self._should_skip_value(item):
                continue
                
            if isinstance(item, (dict, list)):
                # 리스트 안에 객체가 있는 경우 재귀 호출
                # 들여쓰기 대신 구분을 위해 줄바꿈 추가
                sub_content = self._json_to_markdown(item, level)
                if sub_content.strip():
                    lines.append(f"- {sub_content}") # 객체 덩어리를 하나의 항목으로
            else:
                # 단순 값인 경우
                lines.append(f"- {str(item)}")
                
        return "\n".join(lines)
    
    def _json_to_markdown(
        self, 
        data: Any, 
        level: int = 1, 
        parent_key: str = ""
    ) -> str:
        """
        JSON 데이터를 Markdown 형식으로 재귀적으로 변환
        
        """
        lines = []
        
        # 헤딩 레벨은 최대 6까지
        heading_level = min(level, 6)
        heading_prefix = "#" * heading_level
        
        if isinstance(data, dict):
            for key, value in data.items():
                # 건너뛸 키인지 확인
                if self._should_skip_key(key):
                    continue
                
                # 값이 건너뛸 대상인지 확인
                if self._should_skip_value(value):
                    continue
                
                formatted_key = self._format_key(key)
                
                if isinstance(value, dict):
                    # 중첩된 딕셔너리: 하위 섹션으로 재귀 처리
                    lines.append(f"\n{heading_prefix} {formatted_key}")
                    nested_md = self._json_to_markdown(value, level + 1, key)
                    if nested_md.strip():
                        lines.append(nested_md)
                        
                elif isinstance(value, list):
                    # 리스트 처리
                    if value:  # 비어있지 않은 리스트만 처리
                        lines.append(f"\n{heading_prefix} {formatted_key}")
                        list_md = self._process_list(value, level + 1)
                        if list_md.strip():
                            lines.append(list_md)
                            
                else:
                    # 단순 값: 키-값 쌍으로 표시
                    str_value = str(value)
                    if str_value.strip():  # 빈 문자열이 아닌 경우만
                        lines.append(f"- **{formatted_key}**: {str_value}")
        
        elif isinstance(data, list):
            # 루트 레벨이 리스트인 경우
            lines.append(self._process_list(data, level))
        
        else:
            # 기본 타입 (문자열, 숫자 등)
            if not self._should_skip_value(data):
                lines.append(str(data))
        
        return "\n".join(lines)
    
    def load_json_file(self) -> List[Document]:
        search_pattern = os.path.join(self.data_dir, "**", "*.json")
        json_files = glob.glob(search_pattern, recursive=True)

        all_splits = []

        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                md_content = self._json_to_markdown(data)
                
                metadata = {
                    "source" : file_path,
                    "category" : os.path.basename(os.path.dirname(file_path)),
                    "modified_time" : os.path.getmtime(file_path),
                    "format" : "markdown"
                }

                doc = Document(page_content=md_content, metadata=metadata)
                splits = self.text_splitter.split_documents([doc])
                all_splits.extend(splits)

            except Exception as e:
                logger.error(f"JSON 파일 로드 중 오류: {file_path}")

        return all_splits


# --- 테스트 코드 ---
if __name__ == "__main__":
    # 테스트를 위해 임시 파일 생성 로직은 생략하고 로더만 실행
    loader = DocumentLoader(data_dir="./rag_documents") # 경로 확인 필요
    docs = loader.load_json_file()
    
    if docs:
        print("\n=== First Chunk Preview ===")
        print(f"Title: {docs[0].metadata.get('title')}")
        print(f"Content:\n{docs[0].page_content[:300]}...")
    else:
        print("로드된 문서가 없습니다. data 폴더 위치와 json 파일을 확인하세요.")