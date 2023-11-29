#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import yaml
import json
import requests
import jsonpath
from pathlib import Path


def merge_dicts(dict1, dict2):
    """
    合并两个字典
    """
    merged_dict = dict1.copy()
    for key, value in dict2.items():
        if key in merged_dict and isinstance(merged_dict[key], dict) and isinstance(value, dict):
            merged_dict[key] = merge_dicts(merged_dict[key], value)
        else:
            merged_dict[key] = value
    return merged_dict


class SwaggerToYaml(object):
    """
    根据 swagger.json 文件自动解析出接口，转成 yaml 用例
    """

    def __init__(self, swagger='swagger.json'):
        """swagger 参数可以是本地./swagger.json 文件
        也可以从网络 http 获取
        """
        self.current_path = Path.cwd()  # 获取当前运行文件的父一级
        self.data = {}
        self.paths = {}
        self.body = {}
        if 'http' in swagger:
            res = requests.get(swagger)
            try:
                self.data = res.json()
            except Exception as msg:
                print(f"从网络地址 {swagger} 获取 json 数据解析错误: {msg}")
        elif self.current_path.joinpath(swagger).is_file():
            # 读取本地
            with open(self.current_path.joinpath(swagger), "r", encoding='utf-8') as fp:
                swagger_data = json.load(fp)
            self.data = swagger_data
        else:
            print("{swagger} :未找到合法的swagger.json文件")
        self.paths = self.data.get('paths', {})

    def parse_params(self, parameters):
        if parameters:
            param_type_value = {  # 收集参数信息
                "body": {},
                "query": {},
                "path": {}
            }
            # 遍历方法下一层级的parameters列表
            for param in parameters:
                # 根据参数类型body/query/header/path 等，收集参数的内容
                type_in = jsonpath.JSONPath('$..in').parse(param)
                if type_in == ["body"]:
                    # properties = jsonpath.JSONPath('$..properties').parse(param)
                    ref = jsonpath.JSONPath('$..$ref').parse(param)
                    # 解析 body 参数
                    # body = {}
                    if ref:
                        self.parse_model(ref[0], self.body)

                    param_type_value["body"] = self.body
                elif type_in == ["query"]:
                    args_name = param.get('name', '')
                    args_value = param.get('type', '')
                    param_type_value["query"].update({args_name: args_value})
                elif type_in == ["path"]:
                    args_name = param.get('name', '')
                    args_value = param.get('type', '')
                    param_type_value["path"].update({args_name: args_value})
                # elif type_in == ["header"]:
                #     arg_value = param.get('default', param.get('type', ''))
                #     param_type_value["headers"].update({param.get('name'): arg_value})
                else:
                    print(f"参数位 in 类型 未识别：{type_in}")
                    pass
            # print("param_type_value=", param_type_value)
            return param_type_value
        else:
            return {}

    def parse_model(self, ref, body):
        _properties_model = str(ref).lstrip("#/").split('/')
        try:
            expr = "$." + _properties_model[0] + "." + "'.'".join(
                _properties_model[1].split('.')) + ".properties"
            properties_model = jsonpath.JSONPath(expr).parse(self.data)[0]

        except IndexError:
            expr = "$." + _properties_model[0] + "." + "'.'".join(
                _properties_model[1].split('.'))
            properties_model = jsonpath.JSONPath(expr).parse(self.data)[0]

        # print("properties_model=", properties_model)

        for key, value in properties_model.items():
            if key != "description" and "type" in value:
                body.update({key: value['type']})

            elif "$ref" in value:
                body[key] = {}
                self.parse_model(value['$ref'], body[key])

        return body

    def parse_json(self):
        """解析json文件，生成对应的API 信息"""
        count = 1

        for url_path, views in self.paths.items():
            # print("url_path, views=", url_path, "    ", views)
            param_type_value = {  # 收集参数信息
                "path": {},
                "query": {}
            }
            # 与方法同一层级下的parameters
            if 'parameters' in views.keys():
                # 获取 path 路径参数
                for param in views['parameters']:
                    # print("param=", param)
                    args_type = param.get("in")
                    args_name = param.get("name")
                    args_value = param.get('type')
                    # args_value = 1 if args_value == 'integer' else args_value
                    if args_type == "path":
                        param_type_value["path"].update({args_name: args_value})
                    elif args_type == "query":
                        param_type_value["query"].update({args_name: args_value})
            # print("param_type_value=", param_type_value)

            for method, view in views.items():
                # print("method, view=", method, "    ", view)
                # 获取 get/post/put/delete 路径参数path--parameters 跳过：上面已经处理过了
                if method == "parameters":
                    continue

                # tags = jsonpath.jsonpath(view, '$.tags')
                tags = jsonpath.JSONPath('$.tags').parse(view)
                # 获取API 详细参数信息
                api_des = {
                    # "module": tags[0][0] if tags else '',
                    "tags": tags[0][0] if tags else '',
                    "url": url_path,
                    "method": method,
                    # "name": view.get('name', '') if isinstance(view, dict) else '',
                    "desc": view.get('description', '') if isinstance(view, dict) else '',
                }
                # 方法层级下的parameters
                parameters = view.get('parameters', {}) if isinstance(view, dict) else {}
                # print("parameters=", parameters)
                parameters_parser = self.parse_params(parameters)
                # print("******", parameters_parser)
                # print("parameters_parser=", parameters_parser)
                parm_dicts = merge_dicts(parameters_parser, param_type_value)
                # print("parm_dicts", parm_dicts)
                api_des.update(parm_dicts)
                print("api_des=", api_des)
                # 转yaml
                self.api_to_yaml(api_des)

            # count += 1
            # if count >= 2:
            #     break

    def api_to_yaml(self, api_des: dict):
        """api 自动转 yaml 用例
        {'module': 'api/case',
        'url': '/api/case',
        'method': 'get',
        'name': '查询全部Case',
        'desc': '查询全部Case',
        'path': {},
        'body': {},
        'query': {'page': 1, 'size': 50, 'case_name': '', 'module': '', 'project': ''},
        'headers': {'X-Fields': 'string'}
        }
        """
        # 在当前目录下创建模块文件夹
        module_name = api_des.get('tags', '')
        # yaml_name = f"test{api_des.get('url', '').replace('/', '_').rstrip('_')}_{api_des.get('method', '')}.yml"
        if api_des.get('method', '') == "get":
            get_bys = re.findall(r'{(.*?)}', api_des.get('url', ''))
            get_by = get_bys[-1] if get_bys else ""
            if get_by:
                yaml_name = f"test_{api_des.get('tags', '')}_{api_des.get('method', '')}_by_{get_by}.yml"
            else:
                yaml_name = f"test_{api_des.get('tags', '')}_{api_des.get('method', '')}.yml"
        else:
            yaml_name = f"test_{api_des.get('tags', '')}_{api_des.get('method', '')}.yml"
        if module_name:
            # module_dir = self.current_path.joinpath("apis", module_name)
            module_dir = self.current_path.joinpath("cases", module_name)
            if not module_dir.exists():
                # 如果模块文件夹不存在就创建
                # module_dir.mkdir()
                # 创建多层级目录
                os.makedirs(module_dir)
            yaml_file_name = str(module_dir.joinpath(yaml_name).resolve())
        else:
            # 没有模块名称，放项目根目录
            yaml_file_name = str(self.current_path.joinpath(yaml_name).resolve())

        # 写入yaml
        with open(yaml_file_name, 'w', encoding="utf-8") as fp:
            yaml_format = self.yaml_format(api_des)
            yaml.safe_dump(yaml_format, fp, indent=4,
                           default_flow_style=False,
                           encoding='utf-8',
                           allow_unicode=True,
                           sort_keys=False
                           )

    @staticmethod
    def yaml_format(api_des):
        """
        定义yaml文件输出的格式
        config:
          variables:
            x: 1
        get请求:
          name: GET请求示例
          request:
            method: GET
            url: http://httpbin.org/get
          validate:
            - eq: [status_code, 200]
        :return:
        """
        case_name = api_des.get('url', '').lstrip('/').replace('/', '_').rstrip('_') + '_' + api_des.get('method', '')
        case_request = {
            "method": api_des['method'],
            "url": str(api_des['url']).replace('/{', '/${')
        }
        # if api_des.get('headers'):
        #     case_request.update(headers=api_des['headers'])
        if api_des.get('query'):
            # case_request.update(params=api_des['query'])
            case_request.update(params={})
        if api_des.get('body'):
            # case_request.update(json=api_des['body'])
            case_request.update(json={'metadata': {}, 'spec': {}})
        # 用例格式
        case_format = {
            "name": case_name,
            "config": {
                "variables": api_des.get('path', {})
            },
            # 测试步骤
            "steps": {
                # "name": api_des.get('name', ''),
                "request": case_request,
                "response": [
                    {"eq": ["status_code", 200]}
                ]
            }
        }
        return case_format


if __name__ == '__main__':
    s = SwaggerToYaml("http://10.113.68.30/steve-swagger.json")
    s.parse_json()
