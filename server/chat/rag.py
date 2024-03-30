from fastapi import Body, Request
from sse_starlette.sse import EventSourceResponse
from fastapi.concurrency import run_in_threadpool
from configs import (
    LLM_MODELS,
    VECTOR_SEARCH_TOP_K,
    SCORE_THRESHOLD,
    TEMPERATURE,
    USE_RERANKER,
    RERANKER_MODEL,
    RERANKER_MAX_LENGTH,
    MODEL_PATH,
)
from server.utils import wrap_done, get_ChatOpenAI
from server.utils import BaseResponse, get_prompt_template
from langchain.chains import LLMChain
from langchain.callbacks import AsyncIteratorCallbackHandler
from typing import AsyncIterable, List, Optional
import asyncio
from langchain.prompts.chat import ChatPromptTemplate
from server.chat.utils import History
from server.knowledge_base.kb_service.base import KBServiceFactory
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from server.knowledge_base.kb_doc_api import search_docs
from server.reranker.reranker import LangchainReranker
from server.utils import embedding_device


async def knowledge_base_chat_with_rag(
    query: str = Body(..., description="用户输入", examples=["你好"]),
    knowledge_base_name: str = Body(
        ..., description="知识库名称", examples=["samples"]
    ),
    top_k: int = Body(VECTOR_SEARCH_TOP_K, description="匹配向量数"),
    score_threshold: float = Body(
        SCORE_THRESHOLD,
        description="知识库匹配相关度阈值，取值范围在0-1之间，SCORE越小，相关度越高，取到1相当于不筛选，建议设置在0.5左右",
        ge=0,
        le=2,
    ),
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
    request: Request = None,
    with_query_expansion: bool = Body(False, description="是否使用查询扩展增强检索"),
    with_hyde: bool = Body(False, description="是否使用假设回复增强检索")
):
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    print(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    history = [History.from_data(h) for h in history]
    max_tokens = max_tokens if isinstance(max_tokens, int) and max_tokens > 0 else None

    # Query expansion
    async def query_expansion(
        query: str,
        model_name: str = model_name,
    ) -> AsyncIterable[List[str]]:
        callback = AsyncIteratorCallbackHandler()
        model = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=[callback]
        )

        prompt_template = get_prompt_template('llm_chat', 'query_expansion')
        input_msg = History(role="user", content=prompt_template).to_msg_template(False)
        chat_prompt = ChatPromptTemplate.from_messages([input_msg])

        chain = LLMChain(prompt=chat_prompt, llm=model)
        task = asyncio.create_task(wrap_done(
            chain.acall({"input": query}),
            callback.done),
        )
        expanded = ""
        async for token in callback.aiter():
            expanded += token

        # remove empty line in expanded
        expanded = [line.strip() for line in expanded.split('\n') if line.strip()]
        expanded = [line[2:].strip() if line[1] == '.' else line.strip() for line in expanded]
        
        await task
        return expanded[:3]

    # HyDE
    async def hyde(
        query: str,
        model_name: str = model_name,
    ) -> AsyncIterable[str]:
        callback = AsyncIteratorCallbackHandler()
        model = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=[callback]
        )

        prompt_template = get_prompt_template('llm_chat', 'hyde')
        input_msg = History(role="user", content=prompt_template).to_msg_template(False)
        chat_prompt = ChatPromptTemplate.from_messages([input_msg])

        chain = LLMChain(prompt=chat_prompt, llm=model)
        task = asyncio.create_task(wrap_done(
            chain.acall({"input": query}),
            callback.done),
        )
        hypo_question = ""
        async for token in callback.aiter():
            hypo_question += token

        await task
        return hypo_question

    # knowledge base chat

    async def knowledge_base_chat_iterator(
        query: str,
        top_k: int,
        history: Optional[List[History]],
        model_name: str = model_name,
        prompt_name: str = prompt_name,
    ) -> AsyncIterable[str]:
        callback = AsyncIteratorCallbackHandler()

        model = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=[callback],
        )

        queries = [query]
        if with_query_expansion:
            queries.extend(await query_expansion(query, model_name))
        if with_hyde:
            queries.append(await hyde(query, model_name))

        docs = []

        for q in queries:
            docs += await run_in_threadpool(
                search_docs,
                query=q,
                knowledge_base_name=knowledge_base_name,
                top_k=top_k,
                score_threshold=score_threshold,
            )
        print("----------------- INFO START ------------------")
        print("knowledge base:", knowledge_base_name)
        print("query expansion:", with_query_expansion)
        print("HyDE:", with_hyde)
        print("queries:")
        for q in queries:
            print(" >", q)
        print("----------------- INFO END ------------------")

        # 加入reranker
        if USE_RERANKER:
            reranker_model_path = MODEL_PATH["reranker"].get(
                RERANKER_MODEL, "BAAI/bge-reranker-large"
            )
            print("-----------------model path------------------")
            print(reranker_model_path)
            reranker_model = LangchainReranker(
                top_n=top_k,
                device=embedding_device(),
                max_length=RERANKER_MAX_LENGTH,
                model_name_or_path=reranker_model_path,
            )
            print(docs)
            docs = reranker_model.compress_documents(documents=docs, query=query)
            print("---------after rerank------------------")
            print(docs)
        
        # get the highest `top_k`
        docs = docs[:top_k]

        context = "\n".join([doc.page_content for doc in docs])

        prompt_template = get_prompt_template(
            "knowledge_base_chat", prompt_name, knowledge_base_name
        )
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

        source_documents = []
        for inum, doc in enumerate(docs):
            filename = doc.metadata.get("source")
            parameters = urlencode(
                {"knowledge_base_name": knowledge_base_name, "file_name": filename}
            )
            base_url = request.base_url
            url = f"{base_url}knowledge_base/download_doc?" + parameters
            text = (
                f"""出处 [{inum + 1}] [{filename}]({url}) \n\n{doc.page_content}\n\n"""
            )
            source_documents.append(text)

        source_documents_json = [
            dict(
                filename=os.path.split(doc.metadata["source"])[-1],
                content=doc.page_content,
                kb_name=knowledge_base_name,
            )
            for doc in docs
        ]

        if stream:
            # dump docs_json first to avoid blocking, add empty "answer" for compatibility
            yield json.dumps(
                {"answer": "", "docs_json": source_documents_json}, ensure_ascii=False
            )
            async for token in callback.aiter():
                # Use server-sent-events to stream the response
                yield json.dumps({"answer": token}, ensure_ascii=False)
            yield json.dumps({"docs": source_documents}, ensure_ascii=False)
        else:
            answer = ""
            async for token in callback.aiter():
                answer += token
            yield json.dumps(
                {
                    "answer": answer,
                    "docs": source_documents,
                    "docs_json": source_documents_json,
                },
                ensure_ascii=False,
            )
        await task

    return EventSourceResponse(
        knowledge_base_chat_iterator(query, top_k, history, model_name, prompt_name)
    )
