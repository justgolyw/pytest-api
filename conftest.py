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