import streamlit as st
from typing import List

from askadmin.db.models import QA, QACollection


def display_qa_item(qa: QA) -> None:
    with st.expander(qa.question):
        st.markdown(f"**回答：** {qa.answer}")
        if qa.alias:
            st.markdown(f"**关键字：** {qa.alias}")


def display_qa_list(qa: List[QA]) -> None:
    for qa in qa:
        display_qa_item(qa)


def display_qa_collection(collection: QACollection):
    """
    Display all QA in a collection
    """
    qas = collection.questions
    if len(qas) != 0:
        st.markdown("### 问答列表")
    display_qa_list(qas)

