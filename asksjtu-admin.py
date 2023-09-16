import streamlit as st
import extra_streamlit_components as stx
from webui_pages.utils import *
from streamlit_option_menu import option_menu
from webui_pages import *
from webui_pages.asksjtu_stylehack import style_hack
from webui_pages.asksjtu_analytics import analytics_page
import os
import jwt
from datetime import datetime, timedelta
from configs import VERSION
from configs.asksjtu_config import JWT_SECRET, AUTH_PASSWORD
from server.utils import api_address


api = ApiRequest(base_url=api_address())


class Auth:
    COOKLE_NAME = "jwt"

    def __init__(self) -> None:
        self.manager = stx.CookieManager()
        self.jwt_secret = JWT_SECRET

    @property
    def is_authenticated(self):
        return self.verify_jwt()

    def sign_jwt(self) -> str:
        payload = {
            "exp": datetime.utcnow() + timedelta(days=7),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_jwt(self) -> bool:
        try:
            jwt.decode(
                self.manager.get(self.COOKLE_NAME),
                self.jwt_secret,
                algorithms=["HS256"],
            )
            return True
        except jwt.DecodeError:
            return False
        except jwt.ExpiredSignatureError:
            return False

    def login(self, password) -> bool:
        if password != AUTH_PASSWORD:
            print("login failed")
            return False
        print("login success")
        self.manager.set(self.COOKLE_NAME, self.sign_jwt())
        return True

    def logout(self):
        self.manager.delete(self.COOKLE_NAME)


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
    if not auth.is_authenticated:
        st.error("请登录", icon="🚨")
        password = st.text_input("密码", type="password", key="password")
        st.button("登录", on_click=lambda: auth.login(password))
        st.stop()

    style_hack()

    if not chat_box.chat_inited:
        st.toast(
            f"欢迎使用 [`AskSJTU`](https://jihulab.com/asksjtu/langchain-chat-chat) ! \n\n"
            f"当前使用模型`{LLM_MODEL}`, 您可以开始提问了."
        )

    pages = {
        "对话": {
            "icon": "chat",
            "func": dialogue_page,
        },
        "知识库管理": {
            "icon": "hdd-stack",
            "func": knowledge_base_page,
        },
        "访问统计": {
            "icon": "graph-up",
            "func": analytics_page,
        },
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
