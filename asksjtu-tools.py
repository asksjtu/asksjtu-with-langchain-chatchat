import streamlit as st
from streamlit_option_menu import option_menu
from webui_pages.utils import *
from webui_pages.asksjtu_stylehack import style_hack
from webui_pages.asksjtu_pdf import pdf_page
from webui_pages.asksjtu_disclaimer import disclaimer_page
import os

api = ApiRequest(base_url=api_address())


if __name__ == "__main__":
    st.set_page_config(
        page_title="交大智讯-PDF对话",
        page_icon=os.path.join("img/asksjtu", "SJTU-logo-square.png"),
        initial_sidebar_state="collapsed",
        menu_items=None,
    )

    style_hack()

    pages = {
        "PDF 对话": {
            "icon": "chat",
            "func": pdf_page,
        },
        "免责声明": {
            "icon": "exclamation-octagon",
            "func": disclaimer_page,
        },
    }

    with st.sidebar:
        st.image(os.path.join("img/asksjtu", "SJTU-logo.png"), use_column_width=True)

        st.markdown(
            "<p style='text-align: center; font-size:x-large;'>交大智讯</p>",
            unsafe_allow_html=True,
        )

        options = list(pages)
        icons = [x["icon"] for x in pages.values()]
        default_index = 0
        selected_page = option_menu(
            "",
            options=options,
            icons=icons,
            menu_icon="chat-quote",
            default_index=default_index,
        )

    if selected_page in pages:
        pages[selected_page]["func"](api)
