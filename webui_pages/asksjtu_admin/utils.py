import streamlit as st
from typing import List, Optional

from configs.asksjtu_config import DEFAULT_KNOWLEDGE_BASE_NAME
from askadmin.db.models import KnowledgeBase
from askadmin.utils import kb_name_to_hash
from webui_pages.utils import ApiRequest


def get_knowledge_base_name(api: ApiRequest):
    params = st.experimental_get_query_params()
    if not "kb" in params:
        return DEFAULT_KNOWLEDGE_BASE_NAME
    knowledge_base_hash = params["kb"][0]
    # try to get kb from manager
    kbs: List[KnowledgeBase] = [kb for kb in KnowledgeBase.select()]
    knowledge_base: Optional[KnowledgeBase] = next(
        filter(lambda kb: kb.slug == knowledge_base_hash, kbs),
        None,  # default value
    )
    if knowledge_base is not None:
        return knowledge_base.name
    # try to get kb from API
    knowledge_base_list = api.list_knowledge_bases()
    knowledge_base = next(
        filter(
            lambda kb: kb_name_to_hash(kb) == knowledge_base_hash,
            knowledge_base_list,
        ),
        None,  # default value
    )
    if knowledge_base is None:
        return DEFAULT_KNOWLEDGE_BASE_NAME
    return knowledge_base
