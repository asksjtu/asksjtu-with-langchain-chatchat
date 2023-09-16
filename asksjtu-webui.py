# 运行方式：
# 1. 安装必要的包：pip install streamlit-option-menu streamlit-chatbox>=1.1.6
# 2. 运行本机fastchat服务：python server\llm_api.py 或者 运行对应的sh文件
# 3. 运行API服务器：python server/api.py。如果使用api = ApiRequest(no_remote_api=True)，该步可以跳过。
# 4. 运行WEB UI：streamlit run webui.py --server.port 7860

import streamlit as st
from streamlit_option_menu import option_menu
from configs.asksjtu_config import ANALYTICS_PATH
from webui_pages.utils import *
from webui_pages.asksjtu_stylehack import style_hack
from webui_pages.asksjtu_dialogue import dialogue_page
from webui_pages.asksjtu_disclaimer import disclaimer_page
import os
import streamlit_analytics

api = ApiRequest(base_url=api_address())


if __name__ == "__main__":
    st.set_page_config(
        page_title="交大智讯",
        page_icon=os.path.join("img/asksjtu", "SJTU-logo-square.png"),
        initial_sidebar_state="collapsed",
        menu_items=None,
    )

    style_hack()

    streamlit_analytics.start_tracking(load_from_json=ANALYTICS_PATH)

    pages = {
        "对话": {
            "icon": "chat",
            "func": dialogue_page,
        },
        "免责声明": {
            "icon": "exclamation-octagon",
            "func": disclaimer_page,
        }
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

    streamlit_analytics.stop_tracking(save_to_json=ANALYTICS_PATH)
