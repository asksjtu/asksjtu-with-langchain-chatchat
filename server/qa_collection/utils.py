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


def qa_to_document(qa: QA) -> Document:
    """
    Convert a QA to a Document object with the following metadata:
        - source: collection_d
        - question: question
        - answer: answer
        - qa_id: id of QA if applied

    The default strategy for chosing content for embedding is: the `alias`
    field will be used for embedding. If `alias` field is empty, the `question`
    field will be used instead.

    :params qa: a QA object with question, answer and alias
    """
    # get content for embedding
    content = qa.alias if len(qa.alias) != 0 else qa.question
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
    qa_docs = [qa_to_document(qa) for qa in qa_list]
    # create embedding for these objects and save to vs
    if ZH_TITLE_ENHANCE:
        qa_docs = text_splitter.zh_title_enhance(qa_docs)
    id_and_docs = kb.do_add_doc(qa_docs)
    # save doc_id to qas
    # NOTE: id_and_doc will automatically convert qa_id to str
    qa_id_map = {str(qa.id): qa for qa in qa_list}
    for id_and_doc in id_and_docs:
        doc_id, metadata = id_and_doc["id"], id_and_doc["metadata"]
        qa_id = str(metadata["qa_id"])
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


def delete_docs_by_id(kb: KBService, doc_ids: List[str]):
    """
    Delete multiple docs from vector store by doc_id
    """
    if len(doc_ids) == 0:
        return

    from server.knowledge_base.kb_service.milvus_kb_service import MilvusKBService
    from server.knowledge_base.kb_service.faiss_kb_service import FaissKBService
    from server.knowledge_base.kb_service.pg_kb_service import PGKBService

    if isinstance(kb, MilvusKBService):
        if kb.milvus.col:
            doc_ids = [int(pk) for pk in doc_ids]
            kb.milvus.col.delete(expr=f"pk in {doc_ids}")
    elif isinstance(kb, FaissKBService):
        with kb.load_vector_store().acquire() as vs:
            vs.delete(doc_ids)
    elif isinstance(kb, PGKBService):
        kb.pg_vector.delete(doc_ids)
    else:
        raise NotImplementedError()
