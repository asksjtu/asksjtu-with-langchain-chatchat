import streamlit as st
import uuid
from webui_pages.utils import ApiRequest

from askadmin.db.models import User, KnowledgeBase, QACollection
from .components import Auth

KEY_USER_DETAIL_ID = "key_user_detail_id"
KEY_FORM_USER_CREATE = "key_form_user_create"

KEY_FORM_USER_CREATE_NAME = "key_form_user_create_name"
KEY_FORM_USER_CREATE_USERNAME = "key_form_user_create_username"
KEY_FORM_USER_CREATE_PASSWORD = "key_form_user_create_password"
KEY_FORM_USER_CREATE_ROLE = "key_form_user_create_role"


def create_user_form():
    # create an expander for user creation form
    with st.expander("**创建用户**", expanded=False):

        def create_user():
            name = st.session_state.get(KEY_FORM_USER_CREATE_NAME, None)
            username = st.session_state.get(KEY_FORM_USER_CREATE_USERNAME, None)
            password = st.session_state.get(KEY_FORM_USER_CREATE_PASSWORD, None)
            # check empty
            if len(name) == 0:
                st.error("用户名称不能为空")
                return
            if len(username) == 0:
                st.error("用户名不能为空")
                return
            if len(password) == 0:
                password = str(uuid.uuid4())

            if User.get_or_none(User.username == username) is not None:
                st.error(f"用户名 {username} 已存在")
                return
            user = User.create(
                username=username,
                name=name,
                password=User.hash_password(password),
            )
            st.success(f"用户 {user.name}({user.username}) 创建成功")
            # clean up form
            keys = [
                KEY_FORM_USER_CREATE_NAME,
                KEY_FORM_USER_CREATE_USERNAME,
                KEY_FORM_USER_CREATE_PASSWORD,
            ]
            for k in keys:
                st.session_state.pop(k)

        with st.form(KEY_FORM_USER_CREATE, border=False):
            st.text_input("用户名（用于登录）", key=KEY_FORM_USER_CREATE_USERNAME)
            st.text_input("部门名称（用于显示）", key=KEY_FORM_USER_CREATE_NAME)
            st.text_input(
                "密码",
                key=KEY_FORM_USER_CREATE_PASSWORD,
                type="password",
                help="留空自动生成",
            )
            st.selectbox(
                "角色",
                options=[User.ROLE_USER, User.ROLE_ADMIN],
                format_func=lambda role: (
                    "管理员" if role == User.ROLE_ADMIN else "普通用户"
                ),
                key=KEY_FORM_USER_CREATE_ROLE,
            )
            st.form_submit_button("创建用户", on_click=create_user)


def manage_index_page(api: ApiRequest):
    st.markdown("# 用户管理")
    create_user_form()

    st.divider()

    # display header
    fields = ["ID", "用户名", "部门名称", "操作"]
    cols = st.columns(len(fields))
    for i, field in enumerate(fields):
        cols[i].write(f"**{field}**")

    def set_detail_id(user_id):
        def inner():
            st.session_state[KEY_USER_DETAIL_ID] = user_id

        return inner

    for user in User.select():
        cols = st.columns(4)
        fields = [user.id, user.username, user.name]
        for i, field in enumerate(fields):
            cols[i].write(field)
        with cols[3]:
            st.button(
                "修改",
                key=f"user_modify_{user.id}",
                on_click=set_detail_id(user.id),
            )


def user_update_form(user: User):
    def save_user():
        user.name = st.session_state["user_update_name"]
        user.role = st.session_state["user_update_role"]
        user.save()
        st.toast("🎈 保存成功")

    with st.form("user_update_form"):
        st.text_input(
            "用户名", value=user.username, key="user_update_username", disabled=True
        )
        st.text_input("部门名称", value=user.name, key="user_update_name")
        st.selectbox(
            "角色",
            options=[User.ROLE_USER, User.ROLE_ADMIN],
            format_func=lambda role: (
                "管理员" if role == User.ROLE_ADMIN else "普通用户"
            ),
            key="user_update_role",
            index=0 if user.role == User.ROLE_USER else 1,
        )
        st.form_submit_button("保存", on_click=save_user)


def sync_server_kb():
    from server.knowledge_base.kb_api import list_kbs_from_db

    # get unsync kbs
    kb_names = set(list_kbs_from_db())
    existing_kb = [kb for kb in KnowledgeBase.select()]
    existing_kb_names = set([kb.name for kb in existing_kb])
    # filter all QACollection
    existing_qa_collection_names = set([c.name for c in QACollection.select()])
    delta = kb_names - existing_kb_names - existing_qa_collection_names
    # sync with new KBs
    new_kbs = []
    for name in delta:
        new_kbs.append(KnowledgeBase.create(name=name))
    # display result
    st.success(f"同步完成，共同步 {len(kb_names)} 个知识库，新同步 {len(new_kbs)} 个")


def manage_user_kb_section(user: User):
    st.button("↻ 同步知识库信息", on_click=sync_server_kb)

    kbs = [kb for kb in KnowledgeBase.select()]

    def grant_kb_to_user(kb):
        def inner():
            user.kbs.add(kb)
            st.toast(f"成功添加对 {kb.name} 的管理权限", icon="💡")

        return inner

    def revoke_kb_from_user(kb):
        def inner():
            user.kbs.remove(kb)
            st.toast(f"成功解除对 {kb.name} 的管理权限", icon="🚨")

        return inner

    if len(kbs) == 0:
        st.markodwn("_未找到知识库，请新建知识库后点击上方同步按钮_")
    else:
        fields = ["ID", "名称", "操作"]
        cols = st.columns(len(fields))
        for i, field in enumerate(fields):
            cols[i].write(f"**{field}**")

        managed_kbs = user.kbs
        for kb in kbs:
            cols = st.columns(3)
            fields = [kb.id, kb.name]
            for i, field in enumerate(fields):
                cols[i].write(field)
            with cols[2]:
                if kb in managed_kbs:
                    st.button(
                        "❌ 解除权限",
                        on_click=revoke_kb_from_user(kb),
                        key=f"kb_revoke_{kb.id}",
                    )
                else:
                    st.button(
                        "➕ 增加权限",
                        on_click=grant_kb_to_user(kb),
                        key=f"kb_grant_{kb.id}",
                    )


def manage_detail_page(api: ApiRequest):
    user_id = st.session_state[KEY_USER_DETAIL_ID]
    user = User.get_or_none(User.id == user_id)
    if user is None:
        st.session_state.pop(KEY_USER_DETAIL_ID)
        st.rerun()

    cols = st.columns([3, 1])
    cols[0].write(f"# 正在编辑 {user.username}")
    with cols[1]:
        st.button(
            "返回用户列表",
            key="back_to_index",
            on_click=lambda: st.session_state.pop(KEY_USER_DETAIL_ID),
        )
    # display user modification form
    user_update_form(user)

    st.markdown(f"## {user.name} 管理的知识库")
    manage_user_kb_section(user)

    st.divider()

    def delete_user():
        user.delete_instance()
        st.session_state.pop(KEY_USER_DETAIL_ID)
        return

    st.button(
        "删除该用户", type="primary", key=f"user_delete_{user.id}", on_click=delete_user
    )


def manage_page_router(*args, **kwargs):
    # superuser guard
    auth = Auth(key="manage_page_router")
    if not auth.is_authenticated:
        st.error("请先登录")
        st.stop()
    if not auth.user.role == User.ROLE_ADMIN:
        st.error("您没有权限访问该页面")
        st.stop()

    if st.session_state.get(KEY_USER_DETAIL_ID, None):
        manage_detail_page(*args, **kwargs)
    else:
        manage_index_page(*args, **kwargs)
