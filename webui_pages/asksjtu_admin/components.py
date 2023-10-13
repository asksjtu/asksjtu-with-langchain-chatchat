import jwt
import streamlit as st
import extra_streamlit_components as stx
from datetime import datetime, timedelta
from typing import Optional, Dict
from tinydb.table import Document

from askadmin.manager import UserManager, KBManager
from configs.asksjtu_config import JWT_SECRET


class Auth:
    COOKLE_NAME = "jwt"
    STATE_WRONG_PASSWORD = "WRONG_PASSWORD"

    def __init__(self, key: Optional[str] = 'init', jwt_secret: Optional[str] = None) -> None:
        self.user_manager = UserManager()
        self.manager = stx.CookieManager(key=key)
        self.jwt_secret = jwt_secret if jwt_secret is not None else JWT_SECRET

    @property
    def user(self) -> Optional[Document]:
        jwt = self.verify_jwt()
        if jwt is None:
            return None
        user_id = jwt.get("user_id")
        if user_id is None:
            # invalid jwt
            return None
        return self.user_manager.get(pk=user_id)

    @property
    def is_authenticated(self) -> bool:
        return bool(self.verify_jwt())

    def sign_jwt(self, user_id: int) -> str:
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=7),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_jwt(self) -> Optional[Dict]:
        try:
            return jwt.decode(
                self.manager.get(self.COOKLE_NAME),
                self.jwt_secret,
                algorithms=["HS256"],
            )
        except jwt.DecodeError:
            return None
        except jwt.ExpiredSignatureError:
            return None

    def login(self, username: str, password: str) -> Optional[Dict]:
        """
        return user if the credentials are correct
        """
        if not self.user_manager.check_password(username, password):
            self.mark_wrong_password()
            return None
        user = self.user_manager.get(username=username)
        # login success
        self.manager.set(self.COOKLE_NAME, self.sign_jwt(user_id=user.doc_id))
        self.clear_wrong_password()
        return user

    def logout(self):
        self.manager.delete(self.COOKLE_NAME)

    def display_login_form(
        self, always_show: bool = False, stop_if_not_login: bool = True
    ) -> None:
        if always_show or not self.is_authenticated:
            with st.form('login_form'):
                if self.is_wrong_password:
                    st.error("账号或密码错误", icon="🚨")
                else:
                    st.warning("请登录", icon="🚨")
                username = st.text_input("用户名", type="default", key="username")
                password = st.text_input("密码", type="password", key="password")
                st.form_submit_button("登录", on_click=lambda: self.login(username, password))
        if stop_if_not_login and not self.is_authenticated:
            st.stop()

    @property
    def is_wrong_password(self):
        return (
            self.STATE_WRONG_PASSWORD in st.session_state
            and st.session_state[self.STATE_WRONG_PASSWORD]
        )

    @classmethod
    def mark_wrong_password(cls):
        st.session_state[cls.STATE_WRONG_PASSWORD] = True

    @classmethod
    def clear_wrong_password(cls):
        if Auth.STATE_WRONG_PASSWORD in st.session_state:
            del st.session_state[cls.STATE_WRONG_PASSWORD]
