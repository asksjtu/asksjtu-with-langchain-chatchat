import streamlit as st
from webui_pages.utils import *
from streamlit_chatbox import *
from datetime import datetime
import os
from configs import (
    TEMPERATURE,
    HISTORY_LEN,
    PROMPT_TEMPLATES,
    DEFAULT_KNOWLEDGE_BASE,
    DEFAULT_SEARCH_ENGINE,
    SUPPORT_AGENT_MODEL,
)
from typing import List, Dict

from webui_pages.asksjtu_admin.components import Auth
from webui_pages.asksjtu_qa.create import (
    section_qa_collection_create,
    section_qa_create,
)
from webui_pages.asksjtu_qa.display import display_qa_collection, display_collection_slug
from askadmin.db.models import QA, QACollection, KnowledgeBase, User


NEW_COLLECTION_HINT_TEXT = "新建问答库"


def qa_page(api: ApiRequest, is_lite: bool = False):
    """
    QA management page

    - selectbox of KnowledgeBase
    - selectbox of QA collections (with create section)
    - (divider)
    - QA creation form
    - QA list (with edit form via expandar)
    """
    # auth
    auth = Auth(key="qa-page")
    if not auth.is_authenticated:
        st.stop()

    # query all collections of the selected kb
    if auth.user.role == User.ROLE_ADMIN:
        collections = QACollection.select()
        collection_name = st.selectbox(
            "选择问答库",
            [c.name for c in collections] + [NEW_COLLECTION_HINT_TEXT],
        )
    else:
        collections = auth.user.qas
        collection_name = st.selectbox(
            "选择问答库",
            [c.name for c in collections],
        )

    # show create collection form if text match
    if auth.user.role == User.ROLE_ADMIN and collection_name == NEW_COLLECTION_HINT_TEXT:
        section_qa_collection_create(api)
        st.stop()

    # show collection detail
    selected_collection: Optional[QACollection] = next(
        filter(lambda c: c.name == collection_name, collections), None
    )

    # display slug
    display_collection_slug(selected_collection, allow_edit=auth.user.role == User.ROLE_ADMIN)

    st.divider()

    # show QA creation form
    section_qa_create(collection=selected_collection)
    # show QA list
    display_qa_collection(selected_collection)
