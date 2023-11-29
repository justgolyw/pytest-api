#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
import random
from pytest_api import my_builtins


def get_cookie(response):
    headers = response.headers
    cookie = headers['Set-Cookie'].split(";")[0]
    return cookie


from pytest_api import my_builtins


# def username(num):
#     return f"test_{num}"
#
#
# # 注册到插件内置模块上
# my_builtins.username = username


@pytest.fixture()
def demo_fixture(request):
    text = request.param
    print(f"用例前置操作->{text} .....")
    yield
    print(f"用例后置操作->{text} .....")


# @pytest.fixture()
# def fixture1():
#     print("执行fixture1")
#
#
# @pytest.fixture()
# def fixture2():
#     print("执行fixture2")


# @pytest.fixture(scope="session", autouse=True)
# def login(request_session):
#     """全局仅一次登录， 更新session请求头部"""
#     login_url = "/v3-public/localproviders/local?action=login"
#     json = {"username": "admin", "password": "Admin@123", "responseType": "cookie"}
#     # response = requests.post(login_url, json=json, verify=False)
#     response = request_session.send_request(method="post", url=login_url, json=json)
#     cookie = get_cookie(response)
#     headers = {"Cookie": cookie}
#     request_session.headers.update(headers)

@pytest.fixture()
def demo_fixture0(request):
    text = request.param
    print(f"用例前置操作->{text} .....")
    yield
    print(f"用例后置操作->{text} .....")


@pytest.fixture()
def demo_fixture1(request):
    text = request.param
    print(f"用例前置操作->{text} .....")
    yield
    print(f"用例后置操作->{text} .....")


@pytest.fixture()
def demo_fixture2(request):
    text = request.param
    # print(f"用例前置操作->{text} .....")
    yield
    print(f"用例后置操作->{text} .....")


@pytest.fixture()
def demo_fixture_a(request):
    print("fixtures=", request.fixturenames)
    # print(f"用例前置操作->a.....")
    # return "hello"
    yield
    print(f"用例后置操作->a.....")


@pytest.fixture()
def demo_fixture_b():
    print(f"用例前置操作->b.....")
    # yield
    # print(f"用例后置操作->b.....")


@pytest.fixture()
def demo_fixture_a2(request):
    text = request.param
    # print(f"用例前置操作->{text} .....")
    yield
    print(f"用例后置操作->{text} .....")


@pytest.fixture()
def demo_fixture_b2(request):
    text = request.param
    # print(f"用例前置操作->{text} .....")
    yield
    print(f"用例后置操作->{text} .....")
