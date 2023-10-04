import re
import os
import requests
import json
import logging

from configs.server_config import API_SERVER

# !!! export CUDA_VISIBLE_DEVICES=1 !!!


class Base_XSTZFetcher:
    def __init__(self) -> None:
        self.base_url = "not specified"
        self.index_page = "not specified"
        self.name = "not specified"
        self.index_re = None
        self.title_re = None
        self.link_re = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.6"
        }
        self.text_re = re.compile(r'">.*?</span>', re.M)

    def request(self, url: str) -> str:
        url = self.base_url + url
        res = requests.get(url, headers=self.headers)
        if not res.ok:
            logging.error(f"request for {url} ended up with {res.status_code}")
            return ""
        return res.content.decode("utf-8")

    def get_newspiece(self, url_path: str) -> str:
        content = self.request(url_path)
        text_list = []
        for match in self.text_re.finditer(content):
            original = match.group()
            original = original[2:-7]
            if len(original) == 0 or original[-1] == ">":
                continue
            loc = original.find(">")
            if loc != -1:
                original = original.split(">")
                original = original[-1]
            text_list.append(original)
        return " ".join(text_list[:])

    def get_index_from_text(self, content: str):
        indexes = []
        for match in self.index_re.finditer(content):
            index_raw = match.group()
            title = self.title_re.findall(index_raw)
            if len(title) != 1:
                logging.info("missing title")
                continue
            link = self.link_re.findall(index_raw)
            if len(link) != 1:
                logging.info("missing link")
                continue
            indexes.append((title[0].strip(), link[0]))
        return indexes

    def get_indexes(self) -> list:
        content = self.request(self.index_page)
        return self.get_index_from_text(content)

    def download(self, filename: str) -> None:
        if self.name == "not specified":
            raise Exception("not specified fetcher for xstz")
        indexes = self.get_indexes()
        fh = open(filename, "w")
        fh.write(self.name + " 面向学生的通知\n\n")
        fh.write(
            "\n".join([item[0] + " 网址 " + self.base_url + item[1] for item in indexes])
        )
        fh.write("\n\n\n")
        for title, index_url in indexes:
            logging.info(f"fetching title: {title}, url: {self.base_url}{index_url}")
            news = self.get_newspiece(index_url)
            fh.write(title + "\n")
            fh.write(news + "\n\n")
        fh.close()
        logging.info("wrote {} news pieces into {}".format(len(indexes), filename))


class JWC_XSTZFetcher(Base_XSTZFetcher):
    def __init__(self) -> None:
        super().__init__()
        self.base_url = "http://www.jwc.sjtu.edu.cn/"
        self.index_page = "index/mxxsdtz.htm"
        self.name = "教务处"
        self.index_re = re.compile(r'<div class="wz">.*?</div>', re.DOTALL)
        self.title_re = re.compile(r"<h2>(.*?)</h2>")
        self.link_re = re.compile(r'<a href="../(.*?)">')


class SEIEE_XSTZFetcher(Base_XSTZFetcher):
    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://www.seiee.sjtu.edu.cn/"
        self.index_page = "active/ajax_article_list.html"
        self.name = "电院"
        self.index_re = re.compile(r"<li>\r\n.*?</li>", re.DOTALL)
        self.title_re = re.compile(r'<div class="name">\r\n(.*?)</div>')
        self.link_re = re.compile(
            r'<a href="https://www.seiee.sjtu.edu.cn/(.*?)" target="_blank">'
        )
        self.headers["Accept"] = "application/json"

    def get_indexes(self) -> list:
        params = {
            "page": "1",
            "cat_id": "241",
            "search_cat_code": "",
            "search_cat_title": "",
            "template": "v_ajax_normal_list1",
        }
        content = requests.post(
            self.base_url + self.index_page, data=params, headers=self.headers
        )
        text_json = json.loads(content.content.decode("utf-8"))
        return self.get_index_from_text(text_json["content"])


class ME_XSTZFetcher(Base_XSTZFetcher):
    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://me.sjtu.edu.cn/"
        self.index_page = "bkjx/tg_tzgg.html"
        self.name = "机动"
        self.index_re = re.compile(
            r'<li><a href="https://me.sjtu.edu.cn/bkjx/.*?</li>', re.DOTALL
        )
        self.title_re = re.compile(r'<p class="txt">\r\n(.*?)</p>')
        self.link_re = re.compile(r'<a href="https://me.sjtu.edu.cn/(.*?)">')


if __name__ == "__main__":
    comn_kb_name = "常用知识库"
    xstz_filepath = os.path.join(os.getcwd(), "knowledge_base/常用知识库/content/")
    fetchers = [
        ("05-教务处学生通知.txt", JWC_XSTZFetcher()),
        ("06-电院学生通知.txt", SEIEE_XSTZFetcher()),
        ("07-机动学生通知.txt", ME_XSTZFetcher()),
    ]
    url_update_doc = (
        f'http://{API_SERVER["host"]}:{API_SERVER["port"]}/knowledge_base/update_docs'
    )
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    request_body = {
        "knowledge_base_name": comn_kb_name,
        "file_name": "",
        "not_refresh_vs_cache": False,
    }
    request_body = {
        "knowledge_base_name": comn_kb_name,
        "file_names": [],
        "chunk_size": 320,
        "chunk_overlap": 50,
        "zh_title_enhance": False,
        "override_custom_docs": False,
        "docs": r"{}",
        "not_refresh_vs_cache": False,
    }
    for filename, fetcher in fetchers:
        xstz_filename = os.path.join(xstz_filepath, filename)
        logging.info(f"updating {xstz_filename}")
        if os.path.exists(xstz_filename):
            os.remove(xstz_filename)
        fetcher.download(xstz_filename)
        request_body["file_names"].append(filename)
    logging.info(f"download completed, begin posting to url: {url_update_doc}")
    response = requests.post(url_update_doc, json.dumps(request_body), headers=headers)
    if response.status_code == 200:
        logging.info("OK")
    elif response.status_code == 422:
        content = json.loads(response.content)
        logging.error(f"code 422, msg: {content}")
    else:
        logging.error(f"error code: {response.status_code}")
