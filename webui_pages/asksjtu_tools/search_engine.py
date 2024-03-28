import streamlit as st
from streamlit_chatbox import *
from webui_pages.utils import *
from webui_pages.extended_client import ExtendedApiRequest
from configs import HISTORY_LEN
from server.knowledge_base.utils import LOADER_DICT

from .utils import get_messages_history

chat_box = ChatBox(
    assistant_avatar=os.path.join("img", "chatchat_icon_blue_square_v2.png")
)


def search_engine_page(api: ExtendedApiRequest):
    search_engine = "bing"
    se_top_k = SEARCH_ENGINE_TOP_K

    history = get_messages_history(chat_box, HISTORY_LEN)
    llm_model = LLM_MODELS[0]
    temperature = TEMPERATURE
    prompt_template_name = 'search'

    chat_box.output_messages()

    if prompt := st.chat_input("问我关于交大的内容吧，换行请按 Shift+Enter", key="prompt"):
        chat_box.user_say(prompt)
        chat_box.ai_say([
            f"正在搜索...",
            Markdown("...", in_expander=True, title="网络搜索结果", state="complete"),
        ])
        text = ""
        for d in api.search_engine_chat_with_site(prompt,
                                        search_engine_name=search_engine,
                                        sites=["sjtu.edu.cn", "wikipedia.com", "baike.baidu.com"],
                                        top_k=se_top_k,
                                        history=history,
                                        model=llm_model,
                                        prompt_name=prompt_template_name,
                                        temperature=temperature,
                                        split_result=se_top_k > 1):
            if error_msg := check_error_msg(d):  # check whether error occured
                st.error(error_msg)
            elif chunk := d.get("answer"):
                text += chunk
                chat_box.update_msg(text, element_index=0)
        chat_box.update_msg(text, element_index=0, streaming=False)
        chat_box.update_msg("\n\n".join(d.get("docs", [])), element_index=1, streaming=False)