from typing import List, Tuple, Optional
from streamlit.runtime.uploaded_file_manager import UploadedFile
import openpyxl
import pandas as pd

from askadmin.db.models import QA


PARSER_LIST = dict(
    csv=None,
    xlsx=None,
    xls=None,
)


def upload_file_to_df(file: UploadedFile):
    """
    Load stream.UploadedFile to pandas.DataFrame

    :param file: the uploaded file
    """
    ext: str = file.name.split(".")[-1]
    ext = ext.lower()
    if ext in ["csv"]:
        return pd.read_csv(file)
    elif ext in ["xlsx", "xls"]:
        return pd.read_excel(file)
    # unsupported
    raise ValueError(f"不支持的文件类型 {ext}，请使用 .csv,.xlsx,.xls 格式")


def parse_qa_from_source(
    file: UploadedFile,
    question_field: str,
    answer_field: str,
    alias_field: Optional[str] = None,
) -> List[QA]:
    """
    Parse question, answer and alias from file source

    :param file: the file source
    :return: a list of QA object
    """
    # load file to dataframe
    df = upload_file_to_df(file)
    df = df.fillna("")

    # verify the existance of fields
    if question_field not in df.columns:
        raise ValueError(f"未找到问题字段 {question_field}")
    if answer_field not in df.columns:
        raise ValueError(f"未找到回答字段 {answer_field}")
    if alias_field is not None and alias_field not in df.columns:
        raise ValueError(f"未找到关键字字段 {alias_field}")

    # remove `_x000D_` produced by carriage in xlsx source file
    for str_col in (question_field, answer_field):
        df[str_col] = df[str_col].astype(str).apply(openpyxl.utils.escape.unescape)

    # create QAs by iterating rows
    qa_list = [
        QA(
            question=row[question_field],
            answer=row[answer_field],
            alias=row[alias_field] if alias_field is not None else "",
        )
        for _, row in df.iterrows()
    ]
    return qa_list
