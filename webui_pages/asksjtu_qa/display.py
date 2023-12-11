import streamlit as st
import pandas as pd
from typing import List, Dict

from server.knowledge_base.kb_service.base import KBServiceFactory
from server.qa_collection import utils as qa_utils
from askadmin.db.base import db
from askadmin.db.models import QA, QACollection


ZH_QUESTION = "问题"
ZH_ANSWER = "答案"
ZH_VECTORIZED = "是否入库"
ZH_IF_DELETE = "删除？"


def diff_qa_dict_list(
    origin: pd.DataFrame,
    updated: pd.DataFrame,
    key: str = "ID",
    columns: List[str] = [ZH_VECTORIZED, ZH_IF_DELETE, ZH_QUESTION, ZH_ANSWER],
) -> List[Dict]:
    """
    Compare updated and origin dataframe of QAs and return the difference in updated df
    """
    origin_id_map = {qa[key]: qa for qa in origin.to_dict(orient="records")}
    updated_id_map = {qa[key]: qa for qa in updated.to_dict(orient="records")}
    diff = []
    for qa_id, qa in updated_id_map.items():
        if qa_id not in origin_id_map:
            diff.append(qa)
        origin_qa = origin_id_map[qa_id]
        for col in columns:
            if qa[col] != origin_qa[col]:
                diff.append(qa)
                break
    return diff


def update_qas(
    collection: QACollection,
    df: pd.DataFrame,
    updated: pd.DataFrame,
    qas_dict: List[Dict],
) -> None:
    """
    Update on QAs

    :param collection: the QACollection currently editing
    :param df: the original dataframe of QAs
    :param updated: the updated dataframe of QAs
    :param qas_dict: the original QAs in dict format

    Update QAs with the following policy:
    1. Collect all QAs should be removed from vector stores, including:
        - QAs with `vectorized` set to True and content of Question/Answer changed
        - QAs with `if_delete` set to True and originally `vectorized` is True
        - QAs with `vectorized` set to False and originally `vectorized` is True
    2. Collect all QAs should be added to vector stores, including:
        - QAs with content of Question/Answer changed
        - QAs with content of Question/Answer unchanged but originally `vectorized` is set to False
    3. Remove QAs in 1. from vector stores (with `vectorized` and `doc_id` field updated)
    4. Update content of Question/Answer
    5. Remove QAs with `if_delete` set to True
    6. Add QAs in 2. to vector stores (with `vectorized` and `doc_id` field updated)
    """
    diff = diff_qa_dict_list(df, updated)
    origin_qa_id_map = {qa_dict["qa_id"]: qa_dict for qa_dict in qas_dict}
    diff_id_map = {d["ID"]: d for d in diff}
    # 1. Collect all QAs should be removed from vector stores
    to_remove = []
    for updated_qa in diff:
        origin_qa_dict = origin_qa_id_map[updated_qa["ID"]]
        if origin_qa_dict["vectorized"] and (
            origin_qa_dict["question"] != updated_qa[ZH_QUESTION]
            or origin_qa_dict["answer"] != updated_qa[ZH_ANSWER]
        ):
            to_remove.append(updated_qa["ID"])
            continue
        if not origin_qa_dict["vectorized"]:
            continue
        if updated_qa[ZH_IF_DELETE]:
            to_remove.append(updated_qa["ID"])
            continue
        if not updated_qa[ZH_VECTORIZED]:
            to_remove.append(updated_qa["ID"])
    # 2. Collect all QAs should be added to vector stores
    to_add = []
    for updated_qa in diff:
        origin_qa_dict = origin_qa_id_map[updated_qa["ID"]]
        if not updated_qa[ZH_VECTORIZED]:
            continue
        if not origin_qa_dict["vectorized"]:
            to_add.append(updated_qa["ID"])
            continue
        if (
            origin_qa_dict["question"] != updated_qa[ZH_QUESTION]
            or origin_qa_dict["answer"] != updated_qa[ZH_ANSWER]
        ):
            to_add.append(updated_qa["ID"])
            continue

    # Run 3, 4, 5 to atomic actions to maintain consistancy
    kb = KBServiceFactory.get_service_by_name(collection.name)
    if not kb:
        st.error("问答库不存在，请联系管理员")
        st.stop()

    # 3. Remove QAs in 1. from vector stores (with `vectorized` field updated)
    to_removed_qas = QA.select(QA.doc_id).where(QA.id.in_(to_remove))
    to_removed_doc_ids = [qa.doc_id for qa in to_removed_qas]
    with db.atomic() as transaction:
        qa_utils.delete_docs_by_id(kb, to_removed_doc_ids)
        QA.update(vectorized=False, doc_id=None).where(QA.id.in_(to_remove)).execute()

    # 4. Update content of Question/Answer
    to_update = []
    for updated_qa in diff:
        origin_qa_dict = origin_qa_id_map[updated_qa["ID"]]
        if (
            updated_qa[ZH_QUESTION] != origin_qa_dict["question"]
            or updated_qa[ZH_ANSWER] != origin_qa_dict["answer"]
        ):
            to_update.append(updated_qa["ID"])
    if len(to_update) != 0:
        to_update_qas = QA.select().where(QA.id.in_(to_update))
        for qa in to_update_qas:
            qa.question = diff_id_map[qa.id][ZH_QUESTION]
            qa.answer = diff_id_map[qa.id][ZH_ANSWER]
        QA.bulk_update(to_update_qas, fields=[QA.question, QA.answer])

    # 5. Remove QAs with `if_delete` set to True
    to_delete = []
    for updated_qa in diff:
        if updated_qa[ZH_IF_DELETE]:
            to_delete.append(updated_qa["ID"])
    if len(to_delete) != 0:
        QA.delete().where(QA.id.in_(to_delete)).execute()

    # 6. Add QAs in 2. to vector stores (with `vectorized` field updated)
    if len(to_add) != 0:
        to_add_qas = QA.select().where(QA.id.in_(to_add))
        with db.atomic() as transaction:
            qa_utils.vectorize_multiple(kb, to_add_qas)
            transaction.commit()


def display_qa_collection(collection: QACollection) -> None:
    qas = collection.questions
    if len(qas) != 0:
        st.markdown("### 问答列表")

    qas_dict = [
        dict(
            qa_id=qa.id,  # for updating
            question=qa.question,
            answer=qa.answer,
            vectorized=qa.vectorized,
            if_delete=False,  # set init value to false
        )
        for qa in qas
    ]
    df = pd.DataFrame.from_dict(qas_dict)
    df.rename(
        columns={
            "qa_id": "ID",
            "question": ZH_QUESTION,
            "answer": ZH_ANSWER,
            "vectorized": ZH_VECTORIZED,
            "if_delete": ZH_IF_DELETE,
        },
        inplace=True,
    )

    updated = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        disabled=["ID"],
    )

    col_update, col_preview, _, _ = st.columns(4)

    with col_update:
        update_button = st.button("更新问答库", type="primary", use_container_width=True)

    with col_preview:
        preview_button = st.button("预览", type="secondary", use_container_width=True)

    if preview_button:
        diff = diff_qa_dict_list(df, updated)
        if len(diff) == 0:
            st.info("未检测到变更")
            return
        st.markdown("#### 变更预览")
        st.dataframe(diff)

    if update_button:
        update_qas(
            collection=collection,
            df=df,
            updated=updated,
            qas_dict=qas_dict,
        )
        st.rerun()


def display_remove_collection_button(collection: QACollection) -> None:
    delete_collection = st.button("删除问答库")
    if delete_collection:
        kb = KBServiceFactory.get_service_by_name(collection.name)
        if not kb:
            st.error("问答库不存在，请联系管理员")
            st.stop()

        with db.atomic() as transaction:
            if not (kb.clear_vs() and kb.drop_kb()):
                st.error("问答库删除异常，请联系管理员")
            # for database without on_delete constraint
            # TODO: optimize this
            QA.delete().where(QA.collection == collection).execute()
            collection.delete_instance()
            transaction.commit()

        st.toast("问答库已删除", icon="🗑️")
        st.rerun()


def display_collection_slug(collection: QACollection, allow_edit: bool = False) -> None:
    if allow_edit:

        def update_slug():
            collection.slug = new_slug
            collection.save()
            st.toast("问答库标识已更新", icon="🎈")
            st.rerun()

        with st.form("edit-collection-slug"):
            new_slug = st.text_input("问答库标识", value=collection.slug)
            submit = st.form_submit_button("更新", on_click=update_slug)
    else:
        st.info(f"问答库标识：{collection.slug}")
