from fastapi.routing import APIRouter
from fastapi import (
    Body,
    Query,
    Request,
)
from fastapi.responses import (
    JSONResponse,
)
from pydantic import BaseModel, Field
from typing import List, Optional, Annotated

from askadmin.db.models import QA, QACollection
from configs import (
    VECTOR_SEARCH_TOP_K,
    SCORE_THRESHOLD,
)
from server.knowledge_base.kb_doc_api import search_docs

router = APIRouter()


class QAQueryResponseItem(BaseModel):
    """ChatDocs model"""

    question: str = Field(..., description="问题")
    answer: str = Field(..., description="答案")
    score: float = Field(..., description="匹配度")


class QAQueryResponse(BaseModel):
    """ChatStreamResponse model"""

    query: str
    answer: str = Field(..., description="问答库中与用户输入最匹配的问题-答案对的答案")
    qas: List[QAQueryResponseItem] = Field(..., description="问题-答案对列表")


@router.post(
    "/query",
    responses={
        200: {
            "model": QAQueryResponse,
            "description": "查询结果",
        },
        404: {
            "content": {"application/json": {"example": '{"error": "未找到问答库 samples"}'}},
            "description": "错误信息",
        },
    },
)
async def qa_collection_query(
    query: str = Body(..., description="用户输入", examples=["你好"]),
    slug: str = Body(..., description="问答库标识符", examples=["samples"]),
    top_k: Annotated[Optional[int], Body(..., description="返回最匹配的前 k 个问题-答案对，最大为 50", ge=1, le=50)] = None,
    threshold: Annotated[Optional[float], Body(..., description="返回匹配度大于等于 threadshold 的问题-答案对", gt=0, lt=1)] = None,
    filter_by_answer: Annotated[Optional[bool], Body(..., description="是否过滤所有答案相同的项")] = False,
    request: Request = None,
):
    collection: Optional[QACollection] = QACollection.get_or_none(slug=slug)
    if collection is None:
        return JSONResponse(
            status_code=404, content={"error": f"未找到问答库 {slug}"}
        )

    if top_k is None:
        top_k = VECTOR_SEARCH_TOP_K
    if threshold is None:
        threshold = SCORE_THRESHOLD

    origin_top_k = top_k
    if filter_by_answer:
        top_k = min(2 * top_k, top_k + 20)

    # query vector store
    docs = search_docs(query, collection.name, top_k, threshold)

    # early return if no docs are found
    if len(docs) == 0:
        return QAQueryResponse(qas=[], query=query, answer="")
    
    # create response item
    id_score_map = {int(doc.metadata["qa_id"]): doc.score for doc in docs}
    if None in id_score_map.keys():
        del id_score_map[None]

    qa_ids = list(id_score_map.keys())
    qas = QA.select().where(QA.id.in_(qa_ids))
    items = [
        QAQueryResponseItem(
            question=qa.question,
            answer=qa.answer,
            score=id_score_map[qa.id],
        )
        for qa in qas
    ]
    sorted_items = sorted(items, key=lambda x: x.score)

    if filter_by_answer:
        # filter by answer
        answers = set()
        filtered_items = []
        for item in sorted_items:
            if item.answer not in answers:
                answers.add(item.answer)
                filtered_items.append(item)
        sorted_items = filtered_items[:origin_top_k]

    return QAQueryResponse(qas=sorted_items, query=query, answer=sorted_items[0].answer)
