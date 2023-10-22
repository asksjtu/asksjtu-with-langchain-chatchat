from datetime import datetime, date
from configs.asksjtu_config import (
    PROMPT,
    SEMESTER_INFO,
)

PROMPT_VAR_DESC = r"""
目前支持的变量有：
- `<study_year_info>`: 学年信息，如 `2020-2021学年`
- `<semester_info>`: 学期信息，如 `秋季学期`
- `<date>`: 今天的日期，如 `2021年09月01日`
"""


def get_study_year_info() -> str:
    time_now = datetime.now()
    study_year = time_now.year if time_now.month >= 9 else time_now.year - 1
    study_year_info = f"{study_year}-{study_year+1}学年"
    return study_year_info


def get_semester_info() -> str:
    today = date.today()
    for name, start_date, end_date in SEMESTER_INFO:
        if start_date <= today <= end_date:
            return name
    return ""


def get_today_str() -> str:
    today = date.today()
    return today.strftime(r"%Y年%m月%d日")


def get_prompt_template() -> str:
    """
    生成 prompt 模板，目前支持的变量有：
    - study_year_info: 学年信息
    - semester_info: 学期信息
    - date: 今天的日期
    """
    template = PROMPT
    study_year_info = get_study_year_info()
    semester_info = get_semester_info()

    template = template.replace("<study_year_info>", study_year_info)
    template = template.replace("<semester_info>", semester_info)
    template = template.replace("<date>", get_today_str())
    return template


if __name__ == "__main__":
    print(get_prompt_template())
