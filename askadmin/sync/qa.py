"""
Syncs the QA database with the NIC's database.
"""
from __future__ import annotations
from pydantic.dataclasses import dataclass
from dataclasses import asdict
from typing import List, Optional
import httpx

from askadmin.db.models import QACollection
from configs.asksjtu_config import ENDPOINTS


class QASyncWorker:
    @dataclass
    class RequestDataItem:
        question: str
        standardQuestion: str
        answer: str
        popularRank: int
        popular: bool

    @dataclass
    class Request:
        slug: str
        data: List[QASyncWorker.RequestDataItem]

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint if endpoint is not None else ENDPOINTS["qa_sync"]

    def sync(self, collection: QACollection):
        slug = collection.slug
        items = [
            self.RequestDataItem(
                question=qa.alias,
                standardQuestion=qa.question,
                answer=qa.answer,
                popularRank=qa.popular_rank,
                popular=qa.popular,
            )
            for qa in collection.questions
        ]
        data = self.Request(slug=slug, data=items)
        resp = httpx.post(self.endpoint, json=asdict(data))
        print(resp)
        print(resp.content)
        return resp

QASyncWorker.Request.__pydantic_model__.update_forward_refs()
