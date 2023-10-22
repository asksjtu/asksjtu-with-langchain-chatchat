from configs.asksjtu_config import DEFAULT_DISCLAIMER_TEXT
from askadmin.db.models import KnowledgeBase
from webui_pages.asksjtu_admin.utils import get_knowledge_base_name
from webui_pages.utils import ApiRequest
import streamlit as st


def disclaimer_page(api: ApiRequest):

    kb_name = get_knowledge_base_name(api)
    kb = KnowledgeBase.get_or_none(name=kb_name)
    if kb and kb.policy:
        disclaimer_text = kb.policy
    else:
        disclaimer_text= DEFAULT_DISCLAIMER_TEXT

    st.title("免责声明")
    st.markdown(disclaimer_text)
