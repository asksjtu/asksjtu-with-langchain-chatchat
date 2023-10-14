import streamlit as st
from streamlit_chatbox import *
from typing import List, Dict
from datetime import datetime
import os
from askadmin.utils import kb_name_to_hash
from askadmin.manager import KBManager
from configs.model_config import LLM_MODEL, TEMPERATURE, HISTORY_LEN
from configs.asksjtu_config import DEFAULT_KNOWLEDGE_BASE_NAME
from webui_pages.utils import *
from server.knowledge_base.utils import get_file_path as get_kb_file_path

from .widgets import DownloadButtons, DownloadButtonProps

manager = KBManager()
chat_box = ChatBox(
    assistant_avatar=os.path.join("img", "chatchat_icon_blue_square_v2.png")
)


def get_messages_history(history_len: int) -> List[Dict]:
    def filter(msg):
        """
        针对当前简单文本对话，只返回每条消息的第一个element的内容
        """
        content = [
            x._content
            for x in msg["elements"]
            if x._output_method in ["markdown", "text"]
        ]
        return {
            "role": msg["role"],
            "content": content[0] if content else "",
        }

    history = chat_box.filter_history(
        100000, filter
    )  # workaround before upgrading streamlit-chatbox.
    user_count = 0
    i = 1
    for i in range(1, len(history) + 1):
        if history[-i]["role"] == "user":
            user_count += 1
            if user_count >= history_len:
                break
    return history[-i:]


def get_slug_of_kb(kb_name: str) -> str:
    return kb_name_to_hash(kb_name)


def dialogue_page(api: ApiRequest):
    chat_box.init_session()

    with st.sidebar:
        # dialogue_mode 强制设定为 知识库问答
        dialogue_mode = "知识库问答"
        # llm_model 强制选择为 默认模型
        llm_model = LLM_MODEL
        st.session_state["cur_llm_model"] = LLM_MODEL
        # temperature 和 history_len 强制设置为默认值
        temperature = TEMPERATURE
        history_len = HISTORY_LEN
        # 知识库相关设置，全部设置为默认值
        kb_top_k = VECTOR_SEARCH_TOP_K
        score_threshold = SCORE_THRESHOLD
        # 两个暂时不适用的参数
        # chunk_content: bool = False
        # chunk_size 取值为 (0, 500)
        # chunk_size = 250

    def get_knowledge_base():
        params = st.experimental_get_query_params()
        if not "kb" in params:
            return DEFAULT_KNOWLEDGE_BASE_NAME
        knowledge_base_hash = params["kb"][0]
        # try to get kb from manager
        kbs = manager.list() or []
        knowledge_base = next(
            filter(lambda kb: kb.get("slug", None) == knowledge_base_hash, kbs),
            None,  # default value
        )
        if knowledge_base is not None:
            return knowledge_base.get("name")
        # try to get kb from API
        knowledge_base_list = api.list_knowledge_bases()
        knowledge_base = next(
            filter(
                lambda kb: kb_name_to_hash(kb) == knowledge_base_hash,
                knowledge_base_list,
            ),
            None,  # default value
        )
        if knowledge_base is None:
            return DEFAULT_KNOWLEDGE_BASE_NAME
        return knowledge_base

    selected_kb = get_knowledge_base()
    print(selected_kb)

    # Display chat messages from history on app rerun

    chat_box.output_messages()
    if "isWelcomeSaid" not in st.session_state:
        st.session_state.isWelcomeSaid = False
    if not st.session_state.isWelcomeSaid:
        st.session_state.isWelcomeSaid = True
        chat_box.ai_say([Markdown("欢迎使用交大智讯，一个用于回答校园相关问题的大语言模型。")])

    chat_input_placeholder = "请输入对话内容，换行请使用Shift+Enter "

    if prompt := st.chat_input(chat_input_placeholder, key="prompt"):
        history = get_messages_history(history_len)
        chat_box.user_say(prompt)
        history = get_messages_history(history_len)
        chat_box.ai_say(
            [
                f"正在查询知识库 `{selected_kb}` ...",
                Markdown("...", in_expander=True, title="知识库匹配结果", state="running"),
                DownloadButtons([]),
            ]
        )
        text = ""
        for d in api.knowledge_base_chat(
            prompt,
            knowledge_base_name=selected_kb,
            top_k=kb_top_k,
            score_threshold=score_threshold,
            history=history,
            model=llm_model,
            temperature=temperature,
        ):
            if error_msg := check_error_msg(d):  # check whether error occured
                st.error(error_msg)
            elif chunk := d.get("answer"):
                text += chunk
                chat_box.update_msg(text, element_index=0)
        chat_box.update_msg(text, element_index=0, streaming=False)
        # concat docs string
        docs = []
        for inum, doc in enumerate(d.get("docs_json", [])):
            filename, kb_name, content = doc["filename"], doc["kb_name"], doc["content"]
            text = f"""出处 [{inum + 1}] **{filename}** \n\n{content}\n\n"""
            docs.append(text)
        chat_box.update_msg(
            "\n\n".join(docs), element_index=1, streaming=False, state="complete"
        )

        source_names = set()
        sources = []
        for inum, doc in enumerate(d.get("docs_json", [])):
            filename, kb_name, content = doc["filename"], doc["kb_name"], doc["content"]
            # remove duplicate
            if filename in source_names:
                continue
            else:
                source_names.add(filename)
            # append to sources
            filepath = get_kb_file_path(kb_name, filename)
            if os.path.exists(filepath):
                sources.append(
                    DownloadButtonProps(
                        name=filename, path=get_kb_file_path(kb_name, filename)
                    )
                )
        chat_box.update_msg(DownloadButtons(sources), element_index=2, streaming=False)

    now = datetime.now()
    with st.sidebar:
        cols = st.columns(2)
        export_btn = cols[0]
        if cols[1].button(
            "清空对话",
            use_container_width=True,
        ):
            chat_box.reset_history()
            st.experimental_rerun()

    export_btn.download_button(
        "导出记录",
        "".join(chat_box.export2md()),
        file_name=f"{now:%Y-%m-%d %H.%M}_对话记录.md",
        mime="text/markdown",
        use_container_width=True,
    )
