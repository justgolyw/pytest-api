import json
import os
import yaml
import types
import pytest
from _pytest.python import Module
from pathlib import Path
from .env import get_envs
from .common import read_yaml, get_cookie
from . import runner
from requests.adapters import HTTPAdapter
from .request import ApiRequest
from .runner import ApiRunner

# variables = {}

# 定义一个执行机
# runner = Runner()

# 是否debug输出
debug = False


# @pytest.fixture(scope="session", autouse=True)
# def get_host_and_port(pytestconfig):
#     """获取 pytest.ini 配置参数"""
#     host = pytestconfig.getini("host")
#     port = pytestconfig.getini("port")
#     print(f"读取配置文件：host={host}, port={port}")
#     return host, port


# @pytest.fixture(scope="session", autouse=True)
# def login(request_session):
#     """全局仅一次登录， 更新session请求头部"""
#     # login_url = "https://10.113.75.133/v3-public/localproviders/local?action=login"
#     login_url = "/v3-public/localproviders/local?action=login"
#     json = {"username": "admin", "password": "Admin@123", "responseType": "cookie"}
#     # response = requests.post(login_url, json=json, verify=False)
#     response = request_session.send_request(method="post", url=login_url, json=json)
#     cookie = get_cookie(response)
#     headers = {"Cookie": cookie}
#     request_session.headers.update(headers)


@pytest.fixture(scope="session", autouse=True)
def login(request_session):
    """全局仅一次登录， 更新session请求头部"""
    import uuid
    token = str(uuid.uuid4())
    headers = {
        "Authentication": f"Bearer {token}"
    }
    request_session.headers.update(headers)
    print("headers=", request_session.headers)


@pytest.fixture(scope="session")
def request_session(pytestconfig):
    """全局session"""
    # 通过request.config 获取配置参数
    # 或者 pytestconfig获取配置参数
    # envs = get_envs(request.config)
    envs = get_envs(pytestconfig)
    ip, port = envs["host"], envs["port"]
    session = ApiRequest(ip, port)
    # max_retries=2 重试2次
    session.mount("http://", HTTPAdapter(max_retries=2))
    session.mount("https://", HTTPAdapter(max_retries=2))
    yield session
    session.close()


def pytest_addhooks(pluginmanager):
    from . import hooks

    pluginmanager.add_hookspecs(hooks)


def pytest_addoption(parser):
    '''
    pytest命令增加两个参数，支持指定ip、端口、url前缀，方便命令行执行
    '''
    parser.addoption("--host", action="store", help="待测试的API的HOST，可填写IP或者域名", default="")
    parser.addoption("--port", action="store", help="待测试的API的PORT", default="")
    parser.addoption("--user", action="store", help="待测试的API的basic认证用户名，携带会覆盖env.yml里面的账号，默认为空", default="")
    parser.addoption("--password", action="store", help="待测试的API的basic的密码，携带会覆盖env.yml里面的密码，默认为空", default="")
    parser.addoption("--pdebug", action="store", help="是否打印错误信息堆栈", default=False)
    parser.addoption("--step-name", action="store", help="指定步骤执行，包括前后置中的步骤", default="")
    parser.addoption("--exclude", action="store", help="要排除的标签", default="")
    parser.addoption("--include", action="store", help="要包括的标签", default="")

    # pytest.ini 文件添加配置参数
    parser.addini("proto", type=None, default="http", help="待测试的API的协议，默认为http")
    parser.addini("host", type=None, default="", help="待测试的API的HOST，可填写IP或者域名")
    parser.addini("port", type=None, default="", help="待测试的API的PORT")


def pytest_collect_file(file_path: Path, parent):  # noqa
    # if file_path.suffix == ".yml" and not is_ignore_file(file_path):
    if file_path.suffix == ".yml" and file_path.name.startswith("test"):
        py_module = Module.from_parent(parent, path=file_path)
        # 动态创建 module
        module = types.ModuleType(file_path.stem)

        # 解析 yaml 内容
        # raw = yaml.safe_load(file_path.open(encoding='utf-8'))
        raw = read_yaml(file_path)
        # 执行用例
        runner1 = runner.Runner(raw, module)
        # 注册执行
        runner1.register_handler("api", ApiRunner)
        runner1.runner(parent.config)
        # 重写属性
        py_module._getobj = lambda: module  # noqa
        return py_module


# def pytest_ignore_collect(collection_path, config):
#     # 返回布尔值（会根据返回值为 True 还是 False 来决定是否收集改路径下的用例）
#     if collection_path.name == "xx.yml":
#         return True


def is_ignore_file(path):
    api_ignores = ["variables.yml", "env.yml"]
    return path.name in api_ignores


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item):
    # 解决乱码
    outcome = yield
    report = outcome.get_result()
    getattr(report, 'extra', [])
    report.nodeid = report.nodeid.encode("unicode_escape").decode("utf-8")