import streamlit as st

from webui_pages.utils import ApiRequest

from .qa_chat import qa_chat_page
from .dialogue import dialogue_page


def dialogue_route(api: ApiRequest):
    """
    Dispatch to correct page function with the following strategy:

    - Call `qa_chat_page` if `qa_slug` is shown in query params
    - Call `dialogue` otherwise
    """
    params = st.experimental_get_query_params()
    if "qa_slug" in params:
        return qa_chat_page(api)
    else:
        return dialogue_page(api)
