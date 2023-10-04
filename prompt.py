from datetime import datetime

def fill_template() -> str:
    template = """<指令>你是一个用于回答上海交通大学校园相关问题的大语言模型，名字是交大智讯，需要通过给定的资料回答学生们提出的问题。你需要尽可能地提供最新的信 息，现在是<study_year_info><semester_info>，今天的日期是<date>。如果信息有来源，你需要给出来源，不要回答无关信息。</指令>

<已知信息>{{ context }}</已知信息>

<问题>{{ question }}</问题>"""
    time_now = datetime.now()
    study_year = time_now.year if time_now.month >= 9 else time_now.year-1
    study_year_info = f'{study_year}-{study_year+1}学年'
    semester_info = '秋季学期上半学期'
    if time_now.month >= 7 and time_now.month <= 8:
        semester_info = '夏季学期小学期'
    elif time_now.month >= 2 and time_now.month <= 6:
        semester_info = '春季学期下半学期'
    template = template.replace('<study_year_info>', study_year_info)
    template = template.replace('<semester_info>', semester_info)
    template = template.replace('<date>', str(time_now.date()))
    return template


if __name__ == '__main__':
    from configs.model_config import PROMPT_TEMPLATE
    print(fill_template(PROMPT_TEMPLATE))
