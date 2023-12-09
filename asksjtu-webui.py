# 运行方式：
# 1. 安装必要的包：pip install streamlit-option-menu streamlit-chatbox>=1.1.6
# 2. 运行本机fastchat服务：python server\llm_api.py 或者 运行对应的sh文件
# 3. 运行API服务器：python server/api.py。如果使用api = ApiRequest(no_remote_api=True)，该步可以跳过。
# 4. 运行WEB UI：streamlit run webui.py --server.port 7860

import streamlit as st
from streamlit_option_menu import option_menu
from askadmin.db.models import KnowledgeBase
from configs.asksjtu_config import ANALYTICS_PATH
from webui_pages.utils import *
from webui_pages.asksjtu_admin.utils import get_knowledge_base_name
from webui_pages.asksjtu_stylehack import style_hack
from webui_pages.asksjtu_dialogue import dialogue_route
from webui_pages.asksjtu_disclaimer import disclaimer_page
import os
import random
import string
import streamlit_analytics

api = ApiRequest(base_url=api_address())


if __name__ == "__main__":
    if "page_title" in st.session_state:
        st.set_page_config(
            page_title=st.session_state.page_title,
            page_icon=os.path.join("img/asksjtu", "SJTU-logo-square.png"),
            initial_sidebar_state="collapsed",
            menu_items=None,
        )
    else:
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
            "func": dialogue_route,
        },
        "免责声明": {
            "icon": "exclamation-octagon",
            "func": disclaimer_page,
        },
    }

    kb_name = get_knowledge_base_name(api)
    kb = KnowledgeBase.get_or_none(name=kb_name)
    if kb and kb.display_name:
        display_name = kb.display_name
    else:
        display_name = "交大智讯"
    if "page_title" not in st.session_state:
        st.session_state["page_title"] = display_name
        st.rerun()

    with st.sidebar:
        st.image(os.path.join("img/asksjtu", "SJTU-logo.png"), use_column_width=True)

        st.markdown(
            f"<p style='text-align: center; font-size:x-large;'>{display_name}</p>",
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

    def generate_random_string():
        return "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(16)
        )

    streamlit_analytics.stop_tracking(
        save_to_json=ANALYTICS_PATH, unsafe_password=generate_random_string()
    )
