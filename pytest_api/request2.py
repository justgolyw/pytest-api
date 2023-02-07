import ssl
import json
import warnings
import urllib3
from pathlib import Path
from .common import getcwd
from requests import Session

warnings.filterwarnings("ignore")
urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context


class ApiRequest(Session):
    '''
    request操作的封装
    '''

    def __init__(self, host, port=80, urlprefix=""):
        super().__init__()
        self.host = host
        self.port = port
        self.proto = "http"
        # self.s = Session()
        # url前缀
        self.urlprefix = urlprefix
        self.url = ""

    def _url(self, url):
        self.url = f'{self.proto}://{self.host}:{self.port}{self.urlprefix}{url}'

    def _filter_auth(self, kw):
        """
        可在单个步骤删除全局授权信息
        只要带的形式是
        auth: none
        """
        # auth = self.auth
        auth = None
        if "auth" in kw:
            if kw["auth"] == 'none':
                auth = None
            else:
                auth = tuple(kw["auth"])
        return auth

    def _filter_headers(self, kw):
        """
        可在单个步骤删除全局授权信息
        只要带的形式是
        header: none
        """
        headers = None
        if "headers" in kw:
            if kw["headers"] == 'none':
                headers = None
            else:
                headers = kw["headers"]
        print("**headers**", headers)
        return headers

    def handle_files(self, kw):
        """
        发送文件的操作逻辑
        其中传输过来的files的结构是：
        {
            request:
                url: "",
                files: {
                    "file": "case_data/ssl/ssl.cert"
                    # 其中key值中的file需要填写的文件上传字段
                    # 其中的file不是固定写死的，是具体API定义的文件字段名称
                    # 多个文件也类似这样写
                }
        }
        """
        _files = None if "files" not in kw else kw["files"]
        if _files:
            files = {}
            cur_work_path = getcwd()
            for file_key, filepath in _files.items():
                filepath = Path(cur_work_path) / Path(filepath)
                files[file_key] = open(filepath, 'rb')
            return files
        return None

    def handle_urlprefix(self, kw):
        """
        处理url前缀问题，有的步骤不需要url前缀，需要卸载掉
        """
        if "urlprefix" in kw:
            if kw["urlprefix"] == 'none':
                self.urlprefix = ""
            else:
                self.urlprefix = kw["urlprefix"]

    def send_request(self, **kw):
        method = None if "method" not in kw else kw["method"]
        url = None if "url" not in kw else kw["url"]
        files = self.handle_files(kw)
        data = None if "data" not in kw else kw["data"]
        # json = None if "json" not in kw else kw["json"]
        params = None if "params" not in kw else kw["params"]
        timeout = 20 if "timeout" not in kw else kw["timeout"]
        auth = self._filter_auth(kw)
        headers = self._filter_headers(kw)
        self.handle_urlprefix(kw)

        if data and isinstance(data, dict):
            data = json.dumps(kw["data"], ensure_ascii=False).encode("utf-8")

        # 避免json中文问题，因为默认requests库的json是ascii编码
        # 改成自己组装，并变成data方式发送
        if "json" in kw:
            data = json.dumps(kw["json"], ensure_ascii=False).encode("utf-8")

        if headers and "Cookie" in headers:
            # 避免cookie和auth共存的行为
            auth = None

        self._url(url)
        # res = self.s.request(method, self.url, data=data, params=params, timeout=timeout,
        #                      auth=auth, headers=headers, files=files, verify=False)
        res = self.request(method, self.url, data=data, params=params, timeout=timeout,
                           auth=auth, headers=headers, files=files, verify=False)

        return res
