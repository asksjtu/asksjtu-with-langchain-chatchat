"""
Section of QA page for creating/importing QAs
"""

import streamlit as st
import pandas as pd
from webui_pages.utils import *
from webui_pages.asksjtu_qa.utils import parse_qa_from_source
from askadmin.db.models import QA, QACollection
from server.knowledge_base.kb_service.base import KBServiceFactory
from server.qa_collection import utils as qa_utils


KEY_QA_CREATE_FORM = "QA-CREATE-FORM"
KEY_QA_NEW_QUESTION = "new_qa_question"
KEY_QA_NEW_ANSWER = "new_qa_answer"
KEY_QA_NEW_ALIAS = "new_qa_alias"
KEY_QA_IMPORT_FROM_FILE = "new_import_from_file"
KEY_QA_IMPORT_FROM_FILE_INPUT_FILE = "new_import_from_file_input_file"

KEY_QA_COLLECTION_CREATE_FORM = "QA-COLLECTION-CREATE-FORM"
KEY_QA_COLLECTION_NEW_NAME = "new_qa_collection_name"
KEY_QA_COLLECTION_NEW_SOURCE = "new_qa_collection_source"

QA_QUESTION_COL_NAME = "问题"
QA_ANSWER_COL_NAME = "答案"
QA_ALIAS_COL_NAME = "关键词"


def section_qa_create(collection: QACollection, api: Optional[ApiRequest] = None) -> None:
    def create_qa():
        question = st.session_state.get(KEY_QA_NEW_QUESTION, "")
        answer = st.session_state.get(KEY_QA_NEW_ANSWER, "")
        alias = st.session_state.get(KEY_QA_NEW_ALIAS, "")
        if question == "" or answer == "":
            st.error("问题和回答不能为空")
            return
        if alias == "":
            alias = None
        # save in db
        qa = QA.create(
            collection=collection,
            question=question,
            answer=answer,
            alias=alias,
        )
        # save to vector store
        kb = KBServiceFactory.get_service_by_name(collection.name)
        if kb is None:
            raise ValueError("未找到 QACollection 对应的知识库")
        qa_utils.vectorize(kb, qa)
        # send notification
        st.success("问答已创建")
        st.rerun()

    def import_qa():
        """
        Parse QAs from imported file and create them
        """
        source = st.session_state.get(KEY_QA_IMPORT_FROM_FILE_INPUT_FILE, None)
        if source is None:
            st.error("请上传文件")
            return

        try:
            qa_list = parse_qa_from_source(
                source,
                question_field=QA_QUESTION_COL_NAME,
                answer_field=QA_ANSWER_COL_NAME,
                alias_field=None,
            )
        except ValueError as e:
            st.error(e)
            return

        # upload source file to KnowledgeBase of langchain-chatchat
        if api is not None:
            rsp = api.upload_kb_docs(
                files=[source],
                knowledge_base_name=collection.name,
                # manually disable
                to_vector_store=False,
            )
            if rsp["code"] != 200:
                logger.error(rsp)
                raise ValueError(rsp.get("msg", "导入问答库失败，请联系管理员排查"))

        # add metadata to QAs
        for qa in qa_list:
            qa.source = Path(source.name).name
            qa.collection = collection

        # TODO: optimize this
        # QA.bulk_create(qa_list)
        for qa in qa_list:
            qa.save()

        kb = KBServiceFactory.get_service_by_name(collection.name)
        if kb is None:
            st.error("未找到 QACollection 对应的知识库")
            return
        qa_utils.vectorize_multiple(kb, qa_list)
        
        st.success(f"共导入 {len(qa_list)} 条记录")


    with st.expander("创建/导入新问答"):
        # form for creating single and form for importing multiple
        tab_form, tab_import = st.tabs(["创建新问答", "导入新问答"])

        with tab_form:
            with st.form(KEY_QA_CREATE_FORM, border=False):
                # widgets for question, answer and alias (or keywords)
                st.text_input("问题：", placeholder="请输入问题", key=KEY_QA_NEW_QUESTION)
                st.text_area("回答：", placeholder="请输入回答", key=KEY_QA_NEW_ANSWER)
                st.text_input("关键字：", placeholder="请输入关键字", key=KEY_QA_NEW_ALIAS)
                # submit button
                st.form_submit_button("创建新问答", on_click=create_qa)

        with tab_import:
            with st.form(KEY_QA_IMPORT_FROM_FILE, border=False):
                # allow upload file
                st.file_uploader(
                    "从文件中导入：",
                    type=["csv", "xlsx", "xls"],
                    key=KEY_QA_IMPORT_FROM_FILE_INPUT_FILE,
                )
                # submit button
                st.form_submit_button("导入新问答", on_click=import_qa)


def section_qa_collection_create(api: ApiRequest) -> None:
    def create_qa_collection():
        # validate name of new qa collection
        name = st.session_state.get("new_qa_collection_name", "")
        if name == "":
            st.error("问答库名称不能为空")
            return
        if KBServiceFactory.get_service_by_name(name) is not None:
            st.error("该问答库名称已被使用，请重新填写")
            return

        # validate source file
        source = st.session_state.get(KEY_QA_COLLECTION_NEW_SOURCE, None)

        # try parse QA source if provided
        if source:
            try:
                qa_list = parse_qa_from_source(
                    source,
                    question_field=QA_QUESTION_COL_NAME,
                    answer_field=QA_ANSWER_COL_NAME,
                    alias_field=None,
                )
            except ValueError as e:
                st.error(e)
                return

        # create knowledge base in langchain-chatchat
        rsp = api.create_knowledge_base(
            knowledge_base_name=name,
            vector_store_type=DEFAULT_VS_TYPE,
            embed_model=EMBEDDING_MODEL,
        )
        if rsp["code"] != 200:
            logger.error(rsp)
            raise ValueError(rsp.get("msg", "创建问答库失败，请联系管理员排查"))
        # create corresponding QACollection
        collection = QACollection.create(name=name)
        if not source:
            st.success(f"问答库 {name} 已创建")
            return

        # if source is provided, add it to the knowledge base source file list
        rsp = api.upload_kb_docs(
            files=[source],
            knowledge_base_name=name,
            # manually disable
            to_vector_store=False,
        )
        if rsp["code"] != 200:
            logger.error(rsp)
            raise ValueError(rsp.get("msg", "导入问答库失败，请联系管理员排查"))

        # add metadata to QAs
        for qa in qa_list:
            qa.source = Path(source.name).name
            qa.collection = collection

        # TODO: optimize this
        # QA.bulk_create(qa_list)
        for qa in qa_list:
            qa.save()

        kb = KBServiceFactory.get_service_by_name(name)
        if kb is None:
            st.error("未找到 QACollection 对应的知识库")
            return
        qa_utils.vectorize_multiple(kb, qa_list)
        
        st.success(f"问答库 {name} 已创建，共导入 {len(qa_list)} 条记录")
        return

    with st.form(KEY_QA_COLLECTION_CREATE_FORM):
        # widgets for name
        st.text_input("问答库名称：", placeholder="请输入问答库名称", key=KEY_QA_COLLECTION_NEW_NAME)
        st.file_uploader(
            "从文件中导入：", type=["csv", "xlsx", "xls"], key=KEY_QA_COLLECTION_NEW_SOURCE
        )
        # submit button
        st.form_submit_button("创建新问答库", on_click=create_qa_collection)
