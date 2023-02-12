import pytest


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


# @pytest.fixture(scope="session", autouse=False)
# def login(request_session):
#     """全局仅一次登录， 更新session请求头部"""
#     import uuid
#     token = str(uuid.uuid4())
#     headers = {
#         "Authentication": f"Bearer {token}"
#     }
#     request_session.headers.update(headers)
#     print("headers=", request_session.headers)

@pytest.fixture(scope="function")
def demo_fixture1():
    print("用例前置操作->do something .....")
    yield
    print("用例后置操作，do something .....")


@pytest.fixture(scope="module")
def demo_fixture2():
    print("用例前置操作->do something .....")
    yield
    print("用例后置操作，do something .....")


@pytest.fixture(scope="session")
def demo_fixture3():
    print("用例前置操作->do something .....")
    yield
    print("用例后置操作，do something .....")


# def demo_fixture4():
#     print("用例前置操作->do something .....")


# def pytest_generate_tests(metafunc):
    """ generate (multiple) parametrized calls to a test function."""
    params_args = ["username", "password"]
    # if "param" in metafunc.fixturenames:
    #     print(metafunc.fixturenames)
    #     metafunc.parametrize(
    #         "param",                      # 参数名称
    #         metafunc.module.test_data,    # 测试数据
    #         ids=metafunc.module.names,  # 用例名称
    #         scope="function"              # 测试用例对象
    #     )

    # print(metafunc.fixturenames)
    # params_args = metafunc.fixturenames[1:3]
    # print(params_args)
    # metafunc.parametrize(
    #     params_args,  # 参数名称
    #     metafunc.module.test_data,  # 测试数据
    #     # ids=metafunc.module.names,  # 用例名称
    #     scope="function"  # 测试用例对象
    # )
