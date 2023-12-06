from typing import List
from langchain.docstore.document import Document
import peewee as pw
import text_splitter

# packages from langchain project
from configs import (
    ZH_TITLE_ENHANCE,
    logger,
)
from server.knowledge_base.kb_service.base import KBService
from askadmin.db.models import QA


def qa_to_document(
    qa: QA, with_answer: bool = True, with_alias: bool = True
) -> Document:
    """
    Convert a QA to a Document object with the following metadata:
        - source: collection_d
        - question: question
        - answer: answer
        - qa_id: id of QA if applied

    :params with_answer: specify if answer should be embeded
    :params with_alias: specify if alias should be embeded
    """
    content_list = [
        f"- 问题：{qa.question}",
        f"- 答案：{qa.answer}" if with_answer else "",
        f"- 关键词：{qa.alias}" if with_alias else "",
    ]
    content = "\n".join(content_list)
    metadata = {
        "source": qa.collection.id,
        "question": qa.question,
        "answer": qa.answer,
        "qa_id": qa.id,
    }
    return Document(
        page_content=content,
        metadata=metadata,
    )


def vectorize_multiple(
    kb: KBService,
    qa_list: List[QA],
    with_answer: bool = True,
    with_alias: bool = True,
):
    """
    Embed multiple QAs and insert to vector store

    1. Create corresponding `Document` object of every QA
    2. Set metadata to these `Document` objects, including:
        - source: collection_d
        - question: question
        - answer: answer
        - qa_id: id of QA if applied
    3. Embed these `Document` objects
    4. Insert these `Document` objects to vector store
    5. Update `vectorized` field of these QAs to True
    """
    # create `Document` objects for QAs and set metadata
    qa_docs = [
        qa_to_document(qa, with_answer=with_answer, with_alias=with_alias) for qa in qa_list
    ]
    # create embedding for these objects and save to vs
    if ZH_TITLE_ENHANCE:
        qa_docs = text_splitter.zh_title_enhance(qa_docs)
    id_and_docs = kb.do_add_doc(qa_docs)
    # save doc_id to qas
    # NOTE: id_and_doc will automatically convert qa_id to str
    qa_id_map = {str(qa.id): qa for qa in qa_list}
    for id_and_doc in id_and_docs:
        doc_id, metadata = id_and_doc["id"], id_and_doc["metadata"]
        qa_id = metadata["qa_id"]
        if qa_id not in qa_id_map:
            logger.warning(f"QA id {qa_id} not found in qa_id_map")
            continue
        # save doc_id and update vectorized status
        qa_id_map[qa_id].vectorized = True
        qa_id_map[qa_id].doc_id = doc_id
    # bulk update for better performance
    return QA.bulk_update(qa_list, fields=[QA.vectorized, QA.doc_id], batch_size=100)


def vectorize(kb: KBService, qa: QA):
    """
    Embed a QA and insert to vector store
    """
    return vectorize_multiple(kb, [qa])
