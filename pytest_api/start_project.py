#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from configparser import ConfigParser

"""项目脚手架"""

ini_text = '''[pytest]
addopts = -v -s --show-capture=no -p no:warnings --strict

log_cli = false
log_cli_level = info
log_cli_format = %(asctime)s %(filename)s:%(lineno)s [%(levelname)s]: %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S

log_file = ./api_test.log
log_file_level = info
log_file_format = %(asctime)s %(filename)s:%(lineno)s [%(levelname)s]: %(message)s
log_file_date_format = %Y-%m-%d %H:%M:%S
'''

conftest_text = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
import random
from pytest_api import my_builtins


def get_cookie(response):
    headers = response.headers
    cookie = headers['Set-Cookie'].split(";")[0]
    return cookie


def username():
    """
    生成随机的用户名
    """
    return 'user_' + str(random.randint(0, 1000))


# 注册到插件内置模块上
my_builtins.username = username
'''

env_text = '''host: 10.113.78.100
port: 443

#token: token-6ff84:sx79s48xb7dsxpqxwf2z76nbq7b5qbrk8lwctl8v7dksf5q9gqgr45
headers:
  Authorization: Bearer token-k2xnx:cs7dvlswl6bwj566qmtwrmqtvlp2hfzwjqtjz4lncftsjf8ml5hvzc
'''

case1_text = '''test_get:
  name: 简单 get 请求
  request:
    method: GET
    url: /get
  validate:
    - eq: [status_code, 200]
'''


def start_project(config):
    root_path = Path(config.rootpath)
    ini_path = root_path.joinpath("pytest.ini")
    # 创建pytest.ini
    if not ini_path.exists():
        ini_path.touch()
        # ini = ConfigParser()
        # ini.add_section("pytest")
        # ini.set("pytest", "log_cli", "true")
        # ini.write(ini_path.open("w"))
        ini_path.write_text(ini_text, encoding='utf-8')
        sys.stdout.write(f"create ini file: {ini_path}\n")

    # 创建conftest文件
    conftest_path = root_path.joinpath("conftest.py")
    if not conftest_path.exists():
        conftest_path.touch()
        conftest_path.write_text(conftest_text, encoding='utf-8')
        sys.stdout.write(f"create config file: {conftest_path}\n")

    # 创建env.yml文件
    env_path = root_path.joinpath("env.yml")
    if not env_path.exists():
        env_path.touch()
        env_path.write_text(env_text, encoding='utf-8')
        sys.stdout.write(f"create env file: {env_path}\n")

    # 创建demo
    case_demo = root_path.joinpath('case_demo')
    if not case_demo.exists():
        case_demo.mkdir()
        sys.stdout.write(f"create file: {case_demo}\n")
        case1 = case_demo.joinpath('test_get.yml')
        if not case1.exists():
            case1.touch()
            case1.write_text(case1_text, encoding='utf-8')
            sys.stdout.write(f"create yaml file: {case1}\n")
