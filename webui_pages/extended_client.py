from .utils import ApiRequest
from typing import List, Dict
from configs import (
    LLM_MODELS,
    TEMPERATURE,
    SEARCH_ENGINE_TOP_K,
)

from langchain_core._api import deprecated


class ExtendedApiRequest(ApiRequest):

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
