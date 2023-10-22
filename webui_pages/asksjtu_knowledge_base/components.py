import streamlit as st
from configs.asksjtu_config import (
    DEFAULT_WELCOME_MESSAGE,
    DEFAULT_COMMAND,
)
from asksjtu_prompt import PROMPT_VAR_DESC
from askadmin.db.models import KnowledgeBase
from askadmin.utils import kb_name_to_hash


def edit_welcome_message(db_kb: KnowledgeBase):
    def update_welcome_message():
        welcome_message = st.session_state.get("new_kb_slug", "")
        if welcome_message == "" or welcome_message is None:
            welcome_message = DEFAULT_WELCOME_MESSAGE
        db_kb.welcome_message = welcome_message
        db_kb.save()
        st.info("欢迎消息已保存")

    def reset_to_default():
        db_kb.welcome_message = DEFAULT_WELCOME_MESSAGE
        db_kb.save()
        st.info("欢迎消息已恢复默认值")

    with st.form("kb_slug_form"):
        st.text_input(
            "欢迎消息：",
            value=db_kb.welcome_message,
            placeholder=DEFAULT_WELCOME_MESSAGE,
            key="new_kb_slug",
        )
        cols = st.columns(4)
        cols[0].form_submit_button("保存欢迎消息", on_click=update_welcome_message, use_container_width=True)
        cols[1].form_submit_button("恢复默认值", on_click=reset_to_default, use_container_width=True)


def display_slug(db_kb: KnowledgeBase):
    slug = db_kb.slug
    st.info(f"通过链接访问知识库：\n[https://ask.sjtu.cn/?kb={slug}](/?kb={slug})")


def edit_slug(db_kb: KnowledgeBase):
    def update_slug():
        new_slug = st.session_state.get("new_kb_slug", "")
        if new_slug == "" or new_slug is None:
            default_slug = kb_name_to_hash(db_kb.name)
            if KnowledgeBase.where(KnowledgeBase.slug == default_slug).count() == 0:
                st.warning("slug 为空，将使用默认值")
                db_kb.slug = default_slug
                db_kb.save()
                return
            # 如果默认值已被占用，则报错
            st.error("slug 不能为空且默认值已被占用，请输入其他值")
            return
        if KnowledgeBase.where(KnowledgeBase.slug == new_slug).count() > 0:
            st.error("该 slug 已被占用，请尝试其他值")
            return
        db_kb.slug = new_slug
        db_kb.save()
        st.info("slug 已保存")

    def reset_to_default():
        default_slug = kb_name_to_hash(db_kb.name)
        if KnowledgeBase.where(KnowledgeBase.slug == default_slug).count() == 0:
            st.warning("默认值已被占用，请手动输入其他值")
            return
        db_kb.slug = default_slug
        db_kb.save()
        st.info("slug 已恢复默认值")

    with st.form("kb_slug_form"):
        st.text_input(
            "Slug：",
            value=db_kb.slug,
            placeholder="请输入新的 slug",
            key="new_kb_slug",
        )
        cols = st.columns(4)
        cols[0].form_submit_button("保存 slug", on_click=update_slug, use_container_width=True)
        cols[1].form_submit_button("恢复默认值", on_click=reset_to_default, use_container_width=True)


def edit_kb_prompt(db_kb: KnowledgeBase):
    def update_kb_prompt():
        prompt = st.session_state.get("new_kb_prompt", "")
        if prompt == "" or prompt is None:
            prompt = DEFAULT_COMMAND
        db_kb.prompt = prompt
        db_kb.save()
        st.info("提示语已保存")

    def reset_to_default():
        db_kb.prompt = DEFAULT_COMMAND
        db_kb.save()
        st.info("提示语已恢复默认值")

    with st.form("kb_prompt_form"):
        st.text_area(
            "提示语：",
            value=db_kb.prompt or DEFAULT_COMMAND,
            placeholder="请输入提示语",
            key="new_kb_prompt",
        )
        st.markdown(PROMPT_VAR_DESC)
        cols = st.columns(4)
        cols[0].form_submit_button("保存提示语", on_click=update_kb_prompt, use_container_width=True)
        cols[1].form_submit_button("恢复默认值", on_click=reset_to_default, use_container_width=True)
