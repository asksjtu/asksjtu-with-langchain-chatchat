from fastapi.routing import APIRouter
from fastapi import (
    Body,
    Query,
    Request,
)
from fastapi.responses import (
    StreamingResponse,
    FileResponse,
    JSONResponse,
    Response,
)
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chains import LLMChain
from langchain.prompts.chat import ChatPromptTemplate
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional, AsyncIterable
import json
import asyncio

from askadmin.db.models import KnowledgeBase
from configs import (
    LLM_MODELS,
    TEMPERATURE,
    VECTOR_SEARCH_TOP_K,
    SCORE_THRESHOLD,
    MAX_TOKENS,
)
from server.utils import (
    get_prompt_template,
    wrap_done,
    get_ChatOpenAI,
)
from server.chat.utils import History
from server.knowledge_base.utils import get_doc_path
from server.knowledge_base.kb_doc_api import search_docs

router = APIRouter()


class KnowledgeBaseChatDocs(BaseModel):
    """ChatDocs model"""
    filename: str
    content: str


class KnowledgeBaseChatResponse(BaseModel):
    """ChatStreamResponse model"""
    answer: str
    docs: str
    docs_json: List[KnowledgeBaseChatDocs]


@router.get(
    "/download_doc",
    response_class=FileResponse,
    responses={
        200: {"description": "需要下载的文件", "content": {}},
        404: {
            "model": str,
            "description": "错误信息",
            "content": {"text/plain": {"example": "未找到知识库 samples"}},
        },
    },
)
def download_knowledge_base_file(
    knowledge_base_slug: str = Query(..., description="知识库ID", examples=["samples"]),
    filename: str = Query(..., description="文件名", examples=["samples.json"]),
):
    kb: Optional[KnowledgeBase] = KnowledgeBase.get_or_none(slug=knowledge_base_slug)
    if kb is None:
        return Response(
            status_code=404, content=f"未找到知识库 {knowledge_base_slug}", charset="utf-8"
        )

    kb_doc_root = Path(get_doc_path(kb.name))
    file_path = kb_doc_root / filename
    if not file_path.exists():
        return Response(status_code=404, content=f"未找到文件 {filename}", charset="utf-8")
    return FileResponse(file_path, filename=file_path.name)


@router.post("/chat", responses={
    200: {
        "model": KnowledgeBaseChatResponse,
        "description": "对话结果。若不启用流式输出，则一次性返回上述内容；若启用流式输出，第一次会返回 answers, docs 和 docs_json，后续只会返回 answers。",
    },
    404: {
        "content": {
            "application/json": {
                "example": "{\"error\": \"未找到知识库 samples\"}"
            }
        },
        "description": "错误信息",
    }
})
async def knowledge_base_chat(
    query: str = Body(..., description="用户输入", examples=["你好"]),
    knowledge_base_slug: str = Body(..., description="知识库ID", examples=["samples"]),
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
    stream: bool = Body(False, description="是否启用流式输出"),
    request: Request = None,
):
    kb: Optional[KnowledgeBase] = KnowledgeBase.get_or_none(slug=knowledge_base_slug)
    if kb is None:
        return JSONResponse(
            status_code=404, content={"error": f"未找到知识库 {knowledge_base_slug}"}
        )

    top_k = VECTOR_SEARCH_TOP_K
    score_threshold = SCORE_THRESHOLD
    temperature = TEMPERATURE
    max_tokens = MAX_TOKENS
    model_name = LLM_MODELS[0]
    prompt_name = "default"
    knowledge_base_name = kb.name
    history = [History.from_data(h) for h in history]

    async def knowledge_base_chat_iterator(
        query: str, history: Optional[List[History]]
    ) -> AsyncIterable[str]:
        callback = AsyncIteratorCallbackHandler()
        model = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=[callback],
        )
        docs = search_docs(query, kb.name, top_k, score_threshold)
        # TODO: 优化一下结构
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
            filename = Path(doc.metadata["source"]).name
            text = f"""出处 [{inum + 1}] **{filename}** \n\n{doc.page_content}\n\n"""
            source_documents.append(text)

        doc_path = get_doc_path(knowledge_base_name)
        source_documents_json = [
            dict(
                filename=Path(doc.metadata["source"]).resolve().relative_to(doc_path),
                content=doc.page_content,
            )
            for doc in docs
        ]

        if stream:
            # dump docs_json first to avoid blocking, add empty "answer" for compatibility
            yield json.dumps(
                {
                    "answer": "",
                    "docs_json": source_documents_json,
                    "docs": source_documents,
                },
                ensure_ascii=False,
            )
            async for token in callback.aiter():
                # Use server-sent-events to stream the response
                yield json.dumps({"answer": token}, ensure_ascii=False)
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

    return StreamingResponse(
        knowledge_base_chat_iterator(
            query=query,
            history=history,
        ),
        media_type="text/event-stream",
    )
