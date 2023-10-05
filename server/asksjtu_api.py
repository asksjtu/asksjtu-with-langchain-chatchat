from fastapi import Query
from server.knowledge_base.kb_doc_api import download_doc as kb_download_doc
from server.db.repository.knowledge_base_repository import list_kbs_from_db as kb_list_kbs_from_db
from configs.asksjtu_config import SALT
import hashlib


def download_doc(
    knowledge_base_hash: str = Query(...,description="知识库哈希"),
    file_name: str = Query(...,description="文件名称", examples=["test.txt"]),
    preview: bool = Query(False, description="是：浏览器内预览；否：下载"),
):
    """
    download_doc 的封装，将 knowledge_base_hash 转成 knowledge_base_name

    由于 fastapi 通过函数的参数类型传入对应参数，download_doc 的参数列表需和原函数保持一致（除了 knowledge_base_hash）
    """
    knowledge_base_list = kb_list_kbs_from_db()
    knowledge_base_name = next(
        filter(
            lambda kb: hashlib.sha256((kb + SALT).encode()).hexdigest() == knowledge_base_hash,
            knowledge_base_list,
        ),
        None # default value
    )
    return kb_download_doc(
        knowledge_base_name=knowledge_base_name,
        file_name=file_name,
        preview=preview
    )
