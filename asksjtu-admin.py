import os
import streamlit as st
from streamlit_option_menu import option_menu

from askadmin.db.models import User, KnowledgeBase
from webui_pages.utils import *
from webui_pages import *
from webui_pages.asksjtu_admin.components import Auth
from webui_pages.asksjtu_stylehack import style_hack
from webui_pages.asksjtu_analytics import analytics_page
from webui_pages.asksjtu_knowledge_base import user_knowledge_base_page
from webui_pages.asksjtu_knowledge_base import admin_knowledge_base_page
from configs import VERSION
from server.utils import api_address


api = ApiRequest(base_url=api_address())


if __name__ == "__main__":
    st.set_page_config(
        "交大智讯",
        os.path.join("img/asksjtu", "SJTU-logo-square.png"),
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/chatchat-space/Langchain-Chatchat",
            "Report a bug": "https://github.com/chatchat-space/Langchain-Chatchat/issues",
            "About": f"""欢迎使用 Langchain-Chatchat WebUI {VERSION}！""",
        },
    )

    auth = Auth()

    auth.display_login_form(always_show=False, stop_if_not_login=True)

    style_hack()

    if not chat_box.chat_inited:
        st.toast(
            f"欢迎使用 [`AskSJTU`](https://jihulab.com/asksjtu/langchain-chat-chat) ! \n\n"
            f"当前使用模型`{LLM_MODEL}`, 您可以开始提问了."
        )

    if auth.user and auth.user.role == User.ROLE_ADMIN:
        # unlock all features
        pages = {
            "对话": {"icon": "chat", "func": dialogue_page},
            "知识库管理": {"icon": "hdd-stack", "func": admin_knowledge_base_page},
            "访问统计": {"icon": "graph-up", "func": analytics_page},
        }
    else:
        # normal user
        pages = {
            "知识库管理": {"icon": "hdd-stack", "func": user_knowledge_base_page},
        }

    with st.sidebar:
        st.image(os.path.join("img/asksjtu", "SJTU-logo.png"), use_column_width=True)
        st.caption(
            f"""<p align="right">当前版本：{VERSION}</p>""",
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

        # add logout button
        st.button(
            "退出登录",
            on_click=lambda: auth.logout(),
            use_container_width=True,
            type="secondary",
            key="logout",
        )

    if selected_page in pages:
        pages[selected_page]["func"](api)
