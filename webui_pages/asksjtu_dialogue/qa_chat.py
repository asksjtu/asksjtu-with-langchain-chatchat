import os
import streamlit as st
from streamlit_chatbox import *

from askadmin.db.models import QACollection, QA
from webui_pages.utils import ApiRequest
from server.knowledge_base.kb_doc_api import search_docs
from configs import (
    VECTOR_SEARCH_TOP_K,
    SCORE_THRESHOLD,
)


chat_box = ChatBox(
    assistant_avatar=os.path.join("img", "chatchat_icon_blue_square_v2.png")
)


def get_qa_collection_from_query() -> QACollection:
    params = st.experimental_get_query_params()
    if "qa_slug" not in params:
        st.error("未找到问答库标识（`qa_slug`）")
        st.stop()
    qa_slug = params.get("qa_slug")[0]

    collection = QACollection.get_or_none(slug=qa_slug)
    if not collection:
        st.error("未找到问答库")
        st.stop()

    return collection


def user_ask(collection: QACollection, question: str):
    chat_box.user_say(question)
    chat_box.ai_say(
        [
            f"正在查询问答库 `{collection.display_name or collection.name}`...",
            # *[Markdown(in_expander=True) for _ in range(VECTOR_SEARCH_TOP_K)],
        ]
    )

    # TODO: get answer and hints
    qa_docs = search_docs(
        query=question,
        knowledge_base_name=collection.name,
        top_k=VECTOR_SEARCH_TOP_K,
        score_threshold=SCORE_THRESHOLD,
    )

    qa_ids = [doc.metadata.get("qa_id", None) for doc in qa_docs]
    # remove None from qa_ids if any
    qa_ids = [qa_id for qa_id in qa_ids if qa_id]

    if len(qa_ids) == 0:
        chat_box.update_msg("未找到相关问答", element_index=0, streaming=False)
        return

    # peewee, filter by id
    qas = collection.questions.select().where(QA.id.in_(qa_ids))
    qa_id_map = {qa.id: qa for qa in qas}

    # show the most matched question and answer
    answer_text = ""
    most_matched = min(qa_docs, key=lambda doc: doc.score)
    most_matched_qa_id = most_matched.metadata.get("qa_id", None)
    if most_matched_qa_id:
        most_matched_qa = qa_id_map[most_matched_qa_id]
        answer_text += "\n\n".join(
            [
                f"**Q:** {most_matched_qa.question}",
                f"**A:** {most_matched_qa.answer}",
                f"---\n",
            ]
        )
        chat_box.update_msg(answer_text, element_index=0, streaming=False)

    # show other QA as related question
    idx = 1  # the related questions are located in 1,2, 3, ...
    for doc in qa_docs:
        if doc == most_matched:
            continue
        qa_id = doc.metadata.get("qa_id", None)
        if not qa_id:
            continue
        qa = qa_id_map.get(qa_id, None)
        if not qa:
            continue
        chat_box.insert_msg(Markdown(
            title=f"[{doc.score:.4f}] {qa.question}",
            content=qa.answer,
            in_expander=True,
            state="complete",
        ))
        # chat_box.update_msg(
        #     qa.answer,
        #     element_index=idx,
        #     streaming=False,
        #     expanded=True,
        #     title=f"[{doc.score:.4f}] {qa.question}",
        #     state="complete",
        # )
        idx += 1


def qa_chat_page(api: ApiRequest):
    """
    Page for chatting with QA Collection
    """
    collection = get_qa_collection_from_query()

    chat_box.output_messages()

    chat_input_placeholder = "请输入您的问题，换行请使用 Shift + Enter"

    if question := st.chat_input(chat_input_placeholder):
        user_ask(collection=collection, question=question)
