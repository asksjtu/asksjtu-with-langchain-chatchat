import streamlit as st
from streamlit_chatbox import *
from webui_pages.utils import *
from configs import HISTORY_LEN
from server.knowledge_base.utils import LOADER_DICT

from .utils import get_messages_history

chat_box = ChatBox(
    assistant_avatar=os.path.join("img", "chatchat_icon_blue_square_v2.png")
)


@st.cache_data
def upload_temp_docs(files, _api: ApiRequest) -> str:
    """
    将文件上传到临时目录，用于文件对话
    返回临时向量库ID
    """
    return _api.upload_temp_docs(files).get("data", {}).get("id")


def pdf_page(api: ApiRequest):

    with st.sidebar:
        kb_top_k = st.number_input("匹配知识条数：", 1, 20, VECTOR_SEARCH_TOP_K)
        ## Bge 模型会超过1
        score_threshold = st.slider(
            "知识匹配分数阈值：", 0.0, 2.0, float(SCORE_THRESHOLD), 0.01
        )

    has_file_uploaded = st.session_state.get("file_chat_id", None) is not None
    with st.expander("上传文件", expanded=not has_file_uploaded):
        files = st.file_uploader(
            "上传知识文件：",
            [i for ls in LOADER_DICT.values() for i in ls],
            accept_multiple_files=True,
        )
        if st.button("开始上传", disabled=len(files) == 0):
            st.session_state["file_chat_id"] = upload_temp_docs(files, api)

    chat_box.init_session()

    temperature = TEMPERATURE
    llm_model = LLM_MODELS[0]
    prompt_template_name = 'default'
    history_len = HISTORY_LEN
    chat_input_placeholder = "请输入关于文件的问题，换行请使用Shift+Enter。"
    DEFAULT_REPLY_WHEN_NO_DOCS = "未在上传的文件中找到相似信息"

    if prompt := st.chat_input(
        chat_input_placeholder,
        key="prompt",
    ):
        history = get_messages_history(chat_box, history_len)
        chat_box.user_say(prompt)
        chat_box.ai_say(
            [
                f"正在查询文件 `{st.session_state['file_chat_id']}` ...",
                Markdown(
                    "...", in_expander=True, title="文件匹配结果", state="complete"
                ),
            ]
        )
        text = ""
        for d in api.file_chat(
            prompt,
            knowledge_id=st.session_state["file_chat_id"],
            top_k=kb_top_k,
            score_threshold=score_threshold,
            history=history,
            model=llm_model,
            prompt_name=prompt_template_name,
            temperature=temperature,
        ):
            if error_msg := check_error_msg(d):  # check whether error occured
                st.error(error_msg)
            elif chunk := d.get("answer"):
                text += chunk
                chat_box.update_msg(text, element_index=0)
            if "docs_json" in d:
                # concat docs string
                docs_json = d.get("docs_json", [])
                docs = []
                source_names = set()

                if len(docs_json) == 0 and DEFAULT_REPLY_WHEN_NO_DOCS:
                    # no related documentation found and default reply set
                    text = DEFAULT_REPLY_WHEN_NO_DOCS
                    # the text will be updated outside the for-loop
                    # update matched docs block
                    chat_box.update_msg(
                        "（未找到相关文档）", streaming=False, element_index=1, state="complete"
                    )
                    break

                for inum, doc in enumerate(docs_json):
                    # deal with docs content
                    filename, _, content = (
                        doc["filename"],
                        doc["kb_name"],
                        doc["content"],
                    )
                    source_text = (
                        f"""出处 [{inum + 1}] **{filename}** \n\n{content}\n\n"""
                    )
                    docs.append(source_text)
                    # deal with download buttons
                    # skip duplicate files
                    if filename not in source_names:
                        source_names.add(filename)
                # update reference box
                chat_box.update_msg(
                    "\n\n".join(docs),
                    element_index=1,
                    streaming=False,
                    state="complete",
                )
        chat_box.update_msg(text, element_index=0, streaming=False)
        chat_box.update_msg(
            "\n\n".join(d.get("docs", [])), element_index=1, streaming=False
        )
