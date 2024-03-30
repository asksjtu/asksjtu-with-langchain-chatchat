import streamlit as st
from webui_pages.utils import *
from webui_pages.extended_client import ExtendedApiRequest
from webui_pages.asksjtu_tools.utils import get_messages_history
from webui_pages.asksjtu_admin.components import Auth
from streamlit_chatbox import *
from streamlit_modal import Modal
from datetime import datetime
import os
import re
import time
from configs import (
    TEMPERATURE,
    HISTORY_LEN,
    PROMPT_TEMPLATES,
    LLM_MODELS,
    DEFAULT_KNOWLEDGE_BASE,
    DEFAULT_SEARCH_ENGINE,
    SUPPORT_AGENT_MODEL,
)
from server.knowledge_base.utils import LOADER_DICT
import uuid
from typing import List, Dict

chat_box = ChatBox(
    assistant_avatar=os.path.join("img", "chatchat_icon_blue_square_v2.png")
)


def manager_dialogue_page(api: ExtendedApiRequest, is_lite: bool = False):
    auth = Auth(key="user-knowledge-base-page")
    if not auth.is_authenticated:
        st.stop()

    st.session_state.setdefault("conversation_ids", {})
    st.session_state["conversation_ids"].setdefault(
        chat_box.cur_chat_name, uuid.uuid4().hex
    )
    st.session_state.setdefault("file_chat_id", None)
    default_model = api.get_default_llm_model()[0]

    if not chat_box.chat_inited:
        chat_box.init_session()

    with st.sidebar:
        conv_names = list(st.session_state["conversation_ids"].keys())
        index = 0
        if st.session_state.get("cur_conv_name") in conv_names:
            index = conv_names.index(st.session_state.get("cur_conv_name"))
        llm_model = LLM_MODELS[0]

        prompt_template_name = ""
        temperature = st.slider("Temperature：", 0.0, 2.0, TEMPERATURE, 0.05)
        history_len = st.number_input("历史对话轮数：", 0, 20, HISTORY_LEN)


        with st.expander("知识库配置", True):
            kb_list = api.list_knowledge_bases()
            # make sure managed_kbs is not None
            managed_kb_names = set([kb.name for kb in auth.user.kbs])
            system_kb_names = set(kb_list)
            # only allowed kb can be managed
            kb_names = list(managed_kb_names & system_kb_names)

            if (
                "selected_kb_name" in st.session_state
                and st.session_state["selected_kb_name"] in kb_names
            ):
                selected_kb_index = kb_names.index(st.session_state["selected_kb_name"])
            else:
                selected_kb_index = 0

            selected_kb = st.selectbox(
                "请选择知识库：",
                kb_names,
                index=selected_kb_index,
                on_change=lambda : st.toast(f"已加载知识库： {st.session_state.selected_kb}"),
            )

            kb_top_k = st.number_input("匹配知识条数：", 1, 20, VECTOR_SEARCH_TOP_K)
            query_expansion = st.checkbox("是否启用增强检索-扩展查询", False)
            hyde = st.checkbox("是否启用增强检索-假设性回复", False)

            ## Bge 模型会超过1
            score_threshold = st.slider(
                "知识匹配分数阈值：", 0.0, 2.0, float(SCORE_THRESHOLD), 0.01
            )

    # Display chat messages from history on app rerun
    chat_box.output_messages()

    chat_input_placeholder = (
        "请输入对话内容，换行请使用Shift+Enter。输入/help查看自定义命令 "
    )

    if prompt := st.chat_input(chat_input_placeholder, key="prompt"):
        history = get_messages_history(chat_box, history_len)
        chat_box.user_say(prompt)
        chat_box.ai_say(
            [
                f"正在查询知识库 `{selected_kb}` ...",
                Markdown(
                    "...",
                    in_expander=True,
                    title="知识库匹配结果",
                    state="complete",
                ),
            ]
        )

        text = ""
        for d in api.knowledge_base_chat_with_rag(
            prompt,
            knowledge_base_name=selected_kb,
            top_k=kb_top_k,
            score_threshold=score_threshold,
            history=history,
            model=llm_model,
            prompt_name=prompt_template_name,
            temperature=temperature,
            with_query_expansion=query_expansion,
            with_hyde=hyde,
        ):
            if error_msg := check_error_msg(d):  # check whether error occured
                st.error(error_msg)
            elif chunk := d.get("answer"):
                text += chunk
                chat_box.update_msg(text, element_index=0)
        chat_box.update_msg(text, element_index=0, streaming=False)
        chat_box.update_msg(
            "\n\n".join(d.get("docs", [])), element_index=1, streaming=False
        )

    if st.session_state.get("need_rerun"):
        st.session_state["need_rerun"] = False
        st.rerun()

    with st.sidebar:
        cols = st.columns(2)
        export_btn = cols[0]
        if cols[1].button(
            "清空对话",
            use_container_width=True,
        ):
            chat_box.reset_history()
            st.rerun()

    now = datetime.now()
    export_btn.download_button(
        "导出记录",
        "".join(chat_box.export2md()),
        file_name=f"{now:%Y-%m-%d %H.%M}_对话记录.md",
        mime="text/markdown",
        use_container_width=True,
    )
