import json
import logging
import asyncio
from typing import List, Dict

try:
    from ...llm.llm_loader import LocalLLMLoader
    from ..retriever import Retriever  # Relative import from ai_server.rag.evaluation
except ImportError:
    # For running as script directly
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    from ai_server.llm.llm_loader import LocalLLMLoader
    from ai_server.rag.retriever import Retriever

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_Eval")

class RAGEvaluator:
    def __init__(self):
        self.retriever = Retriever()
        self.llm_loader = LocalLLMLoader()
        self.llm = self.llm_loader.get_llm()

    def evaluate_retrieval(self, question: str, ground_truth: str) -> Dict:
        """
        검색 성능 평가 (Context Relevance)
        """
        docs = self.retriever.retrieve(question)
        context_text = "\n".join([doc.page_content for doc in docs])
        
        # LLM에게 채점을 맡김
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 검색 품질 평가자입니다.
사용자의 질문과 정답(Ground Truth)이 주어졌을 때, 
검색된 문서(Context)가 정답을 도출하기에 충분한 정보를 포함하고 있는지 판단하세요.
점수는 0점부터 10점까지 부여하세요.
출력 형식: 점수: <점수> / 이유: <이유>"""),
            ("human", """
질문: {question}
정답: {ground_truth}

[검색된 문서]
{context}
""")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({
            "question": question, 
            "ground_truth": ground_truth, 
            "context": context_text
        })
        
        return {
            "retrieved_docs": len(docs),
            "context_preview": context_text[:100] + "...",
            "evaluation": result.strip()
        }

    def run_batch(self, testset_path: str):
        with open(testset_path, 'r', encoding='utf-8') as f:
            testset = json.load(f)
            
        results = []
        print(f"총 {len(testset)}개의 테스트 케이스 실행 중...")
        
        for item in testset:
            q = item['question']
            gt = item['ground_truth']
            print(f"Testing: {q}")
            
            eval_result = self.evaluate_retrieval(q, gt)
            results.append({
                "question": q,
                "result": eval_result
            })
            
        return results

if __name__ == "__main__":
    evaluator = RAGEvaluator()
    # 현재 디렉토리의 testset.json 사용
    current_dir = os.path.dirname(os.path.abspath(__file__))
    testset_file = os.path.join(current_dir, "testset.json")
    
    final_results = evaluator.run_batch(testset_file)
    
    print("\n" + "="*50)
    print(" [평가 결과 리포트] ")
    print("="*50)
    for res in final_results:
        print(f"Q: {res['question']}")
        print(f"Eval: {res['result']['evaluation']}")
        print("-" * 30)
