from configs import BING_SUBSCRIPTION_KEY, LLM_MODELS, SEARCH_ENGINE_TOP_K, TEMPERATURE
from langchain.chains import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler

from langchain.prompts.chat import ChatPromptTemplate
from fastapi import Body
from sse_starlette import EventSourceResponse
from server.utils import wrap_done, get_ChatOpenAI
from server.utils import BaseResponse, get_prompt_template
from server.chat.utils import History
from server.chat.search_engine_chat import SEARCH_ENGINES, lookup_search_engine
from typing import AsyncIterable
import asyncio
import json
from typing import List, Optional


async def search_engine_chat_with_site(
    query: str = Body(..., description="用户输入", examples=["你好"]),
    search_engine_name: str = Body(
        ..., description="搜索引擎名称", examples=["bing"]
    ),
    sites: List[str] = Body(..., description="限定搜索范围", examples=[["sjtu.edu.cn"]]),
    top_k: int = Body(SEARCH_ENGINE_TOP_K, description="检索结果数量"),
    history: List[History] = Body(
        [],
        description="历史对话",
        examples=[
            [
                {"role": "user", "content": "我们来玩成语接龙，我先来，生龙活虎"},
                {"role": "assistant", "content": "虎头虎脑"},
            ]
        ],
    ),
    stream: bool = Body(False, description="流式输出"),
    model_name: str = Body(LLM_MODELS[0], description="LLM 模型名称。"),
    temperature: float = Body(TEMPERATURE, description="LLM 采样温度", ge=0.0, le=1.0),
    max_tokens: Optional[int] = Body(
        None, description="限制LLM生成Token数量，默认None代表模型最大值"
    ),
    prompt_name: str = Body(
        "default", description="使用的prompt模板名称(在configs/prompt_config.py中配置)"
    ),
    split_result: bool = Body(
        False, description="是否对搜索结果进行拆分（主要用于metaphor搜索引擎）"
    ),
):
    if search_engine_name not in SEARCH_ENGINES.keys():
        return BaseResponse(code=404, msg=f"未支持搜索引擎 {search_engine_name}")

    if search_engine_name == "bing" and not BING_SUBSCRIPTION_KEY:
        return BaseResponse(
            code=404, msg=f"要使用Bing搜索引擎，需要设置 `BING_SUBSCRIPTION_KEY`"
        )

    history = [History.from_data(h) for h in history]

    async def search_engine_chat_iterator(
        query: str,
        search_engine_name: str,
        top_k: int,
        history: Optional[List[History]],
        model_name: str = LLM_MODELS[0],
        prompt_name: str = prompt_name,
    ) -> AsyncIterable[str]:
        nonlocal max_tokens
        callback = AsyncIteratorCallbackHandler()
        if isinstance(max_tokens, int) and max_tokens <= 0:
            max_tokens = None

        model = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=[callback],
        )

        docs = []
        for site in sites:
            search_query = f"{query} (site:{site})"
            docs += await lookup_search_engine(
                search_query, search_engine_name, top_k, split_result=split_result
            )
            await asyncio.sleep(1)

        context = "\n".join([doc.page_content for doc in docs])

        prompt_template = get_prompt_template("search_engine_chat", prompt_name)
        input_msg = History(role="user", content=prompt_template).to_msg_template(False)
        chat_prompt = ChatPromptTemplate.from_messages(
            [i.to_msg_template() for i in history] + [input_msg]
        )

        chain = LLMChain(prompt=chat_prompt, llm=model)

        # Begin a task that runs in the background.
        task = asyncio.create_task(
            wrap_done(
                chain.acall({"context": context, "question": query}), callback.done
            ),
        )

        source_documents = [
            f"""出处 [{inum + 1}] [{doc.metadata["source"]}]({doc.metadata["source"]}) \n\n{doc.page_content}\n\n"""
            for inum, doc in enumerate(docs)
        ]

        if len(source_documents) == 0:  # 没有找到相关资料（不太可能）
            source_documents.append(
                f"""<span style='color:red'>未找到相关文档,该回答为大模型自身能力解答！</span>"""
            )

        if stream:
            async for token in callback.aiter():
                # Use server-sent-events to stream the response
                yield json.dumps({"answer": token}, ensure_ascii=False)
            yield json.dumps({"docs": source_documents}, ensure_ascii=False)
        else:
            answer = ""
            async for token in callback.aiter():
                answer += token
            yield json.dumps(
                {"answer": answer, "docs": source_documents}, ensure_ascii=False
            )
        await task

    return EventSourceResponse(
        search_engine_chat_iterator(
            query=query,
            search_engine_name=search_engine_name,
            top_k=top_k,
            history=history,
            model_name=model_name,
            prompt_name=prompt_name,
        ),
    )
