# -*- coding: utf-8 -*-
import os
import platform
import types
import pytest
import requests
from pathlib import Path
from .env import get_envs
from . import runner
from .request import ApiRequest
from .common import read_yaml
from _pytest.python import Module
from requests.adapters import HTTPAdapter
from .start_project import start_project
from .log import set_log_format


@pytest.fixture(scope="session")
def request_session(request):
    """全局session"""
    # 通过request.config 获取配置参数
    envs = get_envs(request.config)
    # 或者 pytestconfig获取配置参数
    # envs = get_envs(pytestconfig)
    host, port = envs["host"], envs["port"]
    session = ApiRequest(host, port)
    headers = envs.get("headers", "")
    if headers:
        session.headers = headers
    # print("初始化全局session=", session)
    # max_retries=2 重试2次
    session.mount("http://", HTTPAdapter(max_retries=2))
    session.mount("https://", HTTPAdapter(max_retries=2))
    yield session
    session.close()


@pytest.hookimpl
def pytest_addhooks(pluginmanager):
    from pytest_api import hooks

    pluginmanager.add_hookspecs(hooks)


@pytest.hookimpl
def pytest_addoption(parser):
    """
    pytest命令增加两个参数，支持指定ip、端口、url前缀，方便命令行执行
    """
    parser.addoption("--host", action="store", help="待测试的API的HOST，可填写IP或者域名", default="")
    parser.addoption("--port", action="store", help="待测试的API的PORT", default="")
    parser.addoption("--user", action="store", help="待测试的API的basic认证用户名，携带会覆盖env.yml里面的账号，默认为空", default="")
    parser.addoption("--password", action="store", help="待测试的API的basic的密码，携带会覆盖env.yml里面的密码，默认为空", default="")
    parser.addoption("--exclude", action="store", help="要排除的标签", default="")
    parser.addoption("--include", action="store", help="要包括的标签", default="")

    # pytest.ini 文件添加配置参数
    parser.addini("host", type=None, default="", help="待测试的API的HOST，可填写IP或者域名")
    parser.addini("port", type=None, default=443, help="待测试的API的PORT")

    # 创建项目脚手架
    parser.addoption("--start_project", action="store_true", help="start demo project")


@pytest.hookimpl
def pytest_collect_file(file_path: Path, parent):  # noqa
    """
     收集测试用例:
     yaml文件动态生成一个py模块，把yaml文件的数据，动态生成一个测试用例函数
    """
    # if file_path.suffix == ".yml" and not is_ignore_file(file_path):
    if (file_path.suffix == ".yml" or file_path.suffix == ".yaml") and file_path.name.startswith("test"):
        py_module = Module.from_parent(parent, path=file_path)
        # 动态创建 module
        module = types.ModuleType(file_path.stem)

        # 解析 yaml 内容
        raw = read_yaml(file_path)
        # 执行用例
        runner1 = runner.Runner(raw, module)
        # 注册执行
        runner1.runner(parent.config)
        # 重写属性
        py_module._getobj = lambda: module  # noqa
        return py_module


# def pytest_ignore_collect(collection_path, config):
#     # 返回布尔值（会根据返回值为 True 还是 False 来决定是否收集改路径下的用例）
#     if collection_path.name == "test2.yml":
#         return True


def is_ignore_file(path):
    api_ignores = ["variables.yml", "env.yml"]
    return path.name in api_ignores


# 将钩子函数转换为一个包装器函数，从而允许在钩子函数的执行前后执行其他操作
@pytest.mark.hookwrapper
def pytest_runtest_makereport(item):
    # 解决乱码
    outcome = yield
    report = outcome.get_result()
    getattr(report, 'extra', [])
    report.nodeid = report.nodeid.encode("unicode_escape").decode("utf-8")


@pytest.hookimpl
def pytest_generate_tests(metafunc):  # noqa
    """测试用例参数化功能实现"""
    if hasattr(metafunc.module, 'params_data'):  # 从module中获取params_data属性
        params_data = getattr(metafunc.module, 'params_data')
        params_len = 0  # 参数化的参数个数
        if isinstance(params_data, list):
            if isinstance(params_data[0], list):
                params_len = len(params_data[0])
            elif isinstance(params_data[0], dict):
                params_len = len(params_data[0].keys())
            else:
                params_len = 1
        params_args = metafunc.fixturenames[-params_len:]
        if len(params_args) == 1:
            if not isinstance(params_data[0], list):
                params_data = [[p] for p in params_data]
        metafunc.parametrize(
            params_args,
            params_data,
            scope="function"
        )


def pytest_cmdline_main(config):
    if config.option.start_project:
        start_project(config)
        return 0


@pytest.fixture(autouse=True)
def remove(request_session, request):
    def _cleanup(*resources):
        def clean_resource(resource):
            requests.delete(resource, headers=request_session.headers, verify=False)

        def clean():
            for resource in resources:
                clean_resource(resource)

        request.addfinalizer(clean)

    return _cleanup


@pytest.hookimpl
def pytest_configure(config):
    # 配置日志文件和格式
    # root_path = config.rootpath  # 项目根路径
    set_log_format(config)
    # 获取 allure 报告的路径
    allure_dir = config.getoption('--alluredir')  # noqa
    if allure_dir:
        # allure_report_path = Path(os.getcwd()).joinpath(allure_dir)
        allure_report_path = Path.cwd().joinpath(allure_dir)
        if not allure_report_path.exists():
            allure_report_path.mkdir()
        allure_report_env = allure_report_path.joinpath('environment.properties')
        if not allure_report_env.exists():
            allure_report_env.touch()  # 创建文件
            # 写入环境信息
            root_dir = str(config.rootdir).replace("\\", "\\\\")
            allure_report_env.write_text(f'system={platform.system()}\n'
                                         f'systemVersion={platform.version()}\n'
                                         f'pythonVersion={platform.python_version()}\n'
                                         f'pytestVersion={pytest.__version__}\n'
                                         f'rootDir={root_dir}\n')


@pytest.hookimpl
def pytest_terminal_summary(terminalreporter, exitstatus, config): # noqa
    """
    收集测试结果
    """
    total = terminalreporter._numcollected  # noqa
    if total > 0:
        passed = len([i for i in terminalreporter.stats.get("passed", []) if i.when != "teardown"])
        failed = len([i for i in terminalreporter.stats.get("failed", []) if i.when != "teardown"])
        error = len([i for i in terminalreporter.stats.get("error", []) if i.when != "teardown"])
        skipped = len([i for i in terminalreporter.stats.get("skipped", []) if i.when != "teardown"])
        if terminalreporter._numcollected - skipped == 0: # noqa
            successful = 0
        else:
            successful = len(terminalreporter.stats.get("passed", [])) / terminalreporter._numcollected * 100 # noqa
        # 执行时间
        duration = time.time() - terminalreporter._sessionstarttime # noqa
        report_path = Path(config.rootpath).joinpath('reports', 'result.txt')
        # 如果文件夹不存在，则创建文件夹
        if not report_path.parent.exists():
            report_path.parent.mkdir(parents=True)
        # 如果文件不存在，则创建文件，否则不创建，避免覆盖原有文件
        if not report_path.exists():
            report_path.touch()
        # 将执行结果写入文件中
        with open(report_path, "w", encoding="utf-8") as fp:
            fp.write("测试结果统计\n")
            fp.write("总用例数：%s\n" % total)
            fp.write("通过用例：%s\n" % passed)
            fp.write("跳过用例：%s\n" % skipped)
            fp.write("失败用例：%s\n" % failed)
            fp.write("异常用例：%s\n" % error)
            fp.write("测试通过率：%.2f%%\n" % successful)
            fp.write("测试耗时：%.2fs\n" % duration)

