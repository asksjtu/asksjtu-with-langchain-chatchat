from webui_pages.utils import ApiRequest
from configs.asksjtu_config import ANALYTICS_PATH
import streamlit as st
import streamlit_analytics


def analytics_page(api: ApiRequest):
    st.experimental_set_query_params(analytics="on")
    with streamlit_analytics.track(load_from_json=ANALYTICS_PATH):
        pass
