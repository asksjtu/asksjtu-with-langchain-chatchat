from tinydb import TinyDB, Query
from typing import Optional

from configs.asksjtu_config import ADMIN_DB

from askadmin.utils import kb_name_to_hash

__all__ = ["kb", "user", "db"]

db = TinyDB(ADMIN_DB)

"""
Declare tables, set cache_size to 0 to allow multi-thread access
"""

# knowledge Base
kb = db.table("knowledge_base", cache_size=0)
# User Database
user = db.table("user", cache_size=0)


"""
Knowledge Base DAO

Fields:

- name: str
- slug: str (default: sha256(name + SALT))
- downloadable: bool
"""


def create_knowledge_base(name: str, slug: Optional[str], downloadable: bool = True):
    if slug is None:
        slug = kb_name_to_hash(name)
    return kb.insert(dict(name=name, slug=slug, downloadable=downloadable))


def get_knowledge_base_by_name(knowledge_base_name: str):
    """
    根据名称获取知识库
    """
    return kb.get(Query().name == knowledge_base_name)


def get_knowledge_base_by_slug(kb_slug: str):
    """
    根据 slug 获取知识库
    """
    return kb.get(Query().slug == kb_slug)
