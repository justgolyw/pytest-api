import re
import json
import jmespath
import jsonpath
from requests import Response
from .common import get_cookies


def extract_by_jsonpath(extract_value: dict, extract_expression: str):
    """
    json path 取值
    :param extract_value: response.json()
    :param extract_expression: eg: '$.code'
    :return: None或提取的第一个值或全部
    """
    if not isinstance(extract_expression, str):
        return extract_expression
    extract_value = jsonpath.jsonpath(extract_value, extract_expression)
    # extract_value = jsonpath.JSONPath(extract_expression).parse(extract_value)
    if not extract_value:
        return
    elif len(extract_value) == 1:
        return extract_value[0]
    else:
        return extract_value


def extract_by_jmespath(extract_obj: dict, extract_expression: str):
    """
    jmespath 取值
    :param extract_obj: {
        "response": response.json(),
        "cookies": dict(response.cookies),
        "headers": response.headers,
    }
    :param extract_expression: eg: 'body.code'
    :return: 未提取到返回None, 提取到返回结果
    """
    if not isinstance(extract_expression, str):
        return extract_expression
    try:
        extract_value = jmespath.search(extract_expression, extract_obj)
        return extract_value
    except Exception as msg:
        raise msg


def extract_by_regex(extract_obj: str, extract_expression: str):
    """
    正则表达式提取返回结果
    :param extract_obj: response
    :param extract_expression:
    :return:
    """
    if not isinstance(extract_expression, str):
        return extract_expression
    extract_value = re.findall(extract_expression, extract_obj, flags=re.S)
    if not extract_value:
        return ''
    elif len(extract_value) == 1:
        return extract_value[0]
    else:
        return extract_value


def extract_by_object(response: Response, extract_expression: str):
    """
    从response 对象属性取值 [status_code, url, headers, cookies, text, json, encoding]
    :param response: Response Obj
    :param extract_expression: 取值表达式
    :return: 返回取值后的结果
    """
    if not isinstance(extract_expression, str):
        return extract_expression
    res = {
        "headers": response.headers,
        "cookies": get_cookies(response)
    }
    if extract_expression in ["status_code", "url"]:
        return getattr(response, extract_expression)
    elif extract_expression.startswith('headers') or extract_expression.startswith('cookies'):
        return extract_by_jmespath(res, extract_expression)
    elif extract_expression.startswith('response') or extract_expression.startswith('content'):
        try:
            response_parse_dict = response.json()
            return extract_by_jmespath({"response": response_parse_dict}, extract_expression)
        except Exception as msg:
            raise msg
    elif extract_expression.startswith('$.'):
        try:
            response_parse_dict = response.json()
            return extract_by_jsonpath(response_parse_dict, extract_expression)
        except Exception as msg:
            raise msg
    elif '.+?' in extract_expression or '.*?' in extract_expression:
        # 正则匹配
        return extract_by_regex(response.text, extract_expression)
    else:
        # 其它非取值表达式，直接返回
        return extract_expression


def extract_by_object2(response: list, extract_expression: str):
    """
    从执行命令后的返回值中取值
    :param response: list
    :param extract_expression: 取值表达式
    :return: 返回取值后的结果
    """
    if not isinstance(extract_expression, str):
        return extract_expression
    if extract_expression.startswith('$.'):
        try:
            response_parse_dict = json.loads(response[0])
            return extract_by_jsonpath(response_parse_dict, extract_expression)
        except Exception as msg:
            raise msg
    elif extract_expression.startswith('response') or extract_expression.startswith('content'):
        try:
            response_parse_dict = json.loads(response[0])
            return extract_by_jmespath({"response": response_parse_dict}, extract_expression)
        except Exception as msg:
            raise msg
    elif '.+?' in extract_expression or '.*?' in extract_expression:
        # 正则匹配
        return extract_by_regex(response[0], extract_expression)
    # 表达式为*，直接返回response
    elif "*" == extract_expression:
        return response[0]
    else:
        # 其它非取值表达式，直接返回
        return extract_expression
