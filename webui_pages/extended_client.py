from .utils import ApiRequest
from typing import List, Dict
from configs import (
    LLM_MODELS,
    TEMPERATURE,
    SEARCH_ENGINE_TOP_K,
    VECTOR_SEARCH_TOP_K,
    SCORE_THRESHOLD,
)
from pprint import pprint

from langchain_core._api import deprecated


class ExtendedApiRequest(ApiRequest):

    def knowledge_base_chat_with_rag(
            self,
            query: str,
            knowledge_base_name: str,
            top_k: int = VECTOR_SEARCH_TOP_K,
            score_threshold: float = SCORE_THRESHOLD,
            history: List[Dict] = [],
            stream: bool = True,
            model: str = LLM_MODELS[0],
            temperature: float = TEMPERATURE,
            max_tokens: int = None,
            prompt_name: str = "default",
            with_query_expansion: bool = True,
            with_hyde: bool = False,
    ):
        '''
        对应api.py/chat/knowledge_base_chat_with_rag 接口
        '''
        data = {
            "query": query,
            "knowledge_base_name": knowledge_base_name,
            "top_k": top_k,
            "score_threshold": score_threshold,
            "history": history,
            "stream": stream,
            "model_name": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "prompt_name": prompt_name,
            "with_query_expansion": with_query_expansion,
            "with_hyde": with_hyde,
        }

        # print(f"received input message:")
        pprint(data)

        response = self.post(
            "/chat/knowledge_base_chat_with_rag",
            json=data,
            stream=True,
        )
        return self._httpx_stream2generator(response, as_json=True)

    @deprecated(
        since="0.3.0",
        message="搜索引擎问答将于 Langchain-Chatchat 0.3.x重写, 0.2.x中相关功能将废弃",
        removal="0.3.0"
    )
    def search_engine_chat_with_site(
            self,
            query: str,
            search_engine_name: str = 'bing',
            sites: List[str] = ['sjtu.edu.cn', 'wikipedia.com', 'baike.baidu.com'],
            top_k: int = SEARCH_ENGINE_TOP_K,
            history: List[Dict] = [],
            stream: bool = True,
            model: str = LLM_MODELS[0],
            temperature: float = TEMPERATURE,
            max_tokens: int = None,
            prompt_name: str = "default",
            split_result: bool = False,
    ):
        '''
        对应api.py/chat/search_engine_chat接口
        '''
        data = {
            "query": query,
            "search_engine_name": search_engine_name,
            "sites": sites,
            "top_k": top_k,
            "history": history,
            "stream": stream,
            "model_name": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "prompt_name": prompt_name,
            "split_result": split_result,
        }

        response = self.post(
            "/chat/search_engine_chat_with_site",
            json=data,
            stream=True,
        )
        return self._httpx_stream2generator(response, as_json=True)
