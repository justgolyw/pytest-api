import json
import yaml
import copy
import time
import types
import logging
from inspect import Parameter
from pathlib import Path
from . import extract
from . import my_builtins, validate
from .render import rend_template_any
from .create_function import create_function_from_parameters
from .ssh_client import user_ssh_client
from .ssh_client import DOCKER_CONTAINER_COMMAND
import mimetypes
from requests_toolbelt import MultipartEncoder
from .env import get_envs_from_yml
from .log import logger

# logger = logging.getLogger(__name__)


def protect_response(r):
    if r.status_code < 200 or r.status_code >= 300:
        message = f'Server responded with status_code {r.status_code}:\n{r.text}'
        logger.info(message)
        raise ValueError(message)


class ApiRunner:

    def run(self, request_value, session, root_dir):
        """
        发送request请求
        """
        # logger.info(f'----------  request info ----------\n'
        #             f'{json.dumps(request_value, indent=4)}')

        logger.info(f'--------  request info ----------')
        logger.info(f'yml raw  -->: {request_value}')
        # 处理文件上传
        request_value = self.multipart_request(request_value, root_dir)
        request_headers = session.headers
        if request_value.get("headers", {}):
            request_headers.update(request_value.get("headers", {}))
        request_value.update({"headers": request_headers})
        logger.info(f'headers  -->: {request_headers}')
        logger.info(f'method   -->: {request_value.get("method", "")}')
        logger.info(f'url      -->: {request_value.get("url", "")}')

        if request_value.get('json'):
            logger.info(f'json     -->: {json.dumps(request_value.get("json", {}), indent=4)}')
        else:
            logger.info(f'data     -->: {request_value.get("data", {})}')

        response = session.send_request(**request_value)

        logger.info(f'----------  response info  ----------\n'
                    f'Status Code: {getattr(response, "status_code")} {getattr(response, "reason", "")}\n'
                    f'Response Time: {getattr(response, "elapsed", "").total_seconds() if getattr(response, "elapsed", "") else ""}s\n'
                    # f'\n url: {getattr(response, "url", "")} \n'
                    # f'Response body: {getattr(response, "text", "")}'
                    # f'Response Body: {json.dumps(response.json(), indent=4)}'
                    )
        # protect_response(response)

        if getattr(response, "text"):
            logger.info(f'Response Body: {json.dumps(response.json(), indent=4)}')

        return response

    @staticmethod
    def extract_response(response, extract_obj):
        """提取返回结果"""
        extract_result = {}
        if isinstance(extract_obj, dict):
            for extract_var, extract_expression in extract_obj.items():
                extract_var_value = extract.extract_by_object(response, extract_expression)  # 实际结果
                extract_result[extract_var] = extract_var_value
            return extract_result
        else:
            return extract_result

    @staticmethod
    def validate_response(response, validate_check):
        """
        校验结果
        eq: [status_code, 200]
        """
        for check in validate_check:
            for check_type, check_value in check.items():
                actual_value = extract.extract_by_object(response, check_value[0])  # 实际结果
                expect_value = check_value[1]  # 期望结果
                if check_type in ["eq", "equals", "equal"]:
                    validate.equals(actual_value, expect_value)
                elif check_type in ["lt", "less_than"]:
                    validate.less_than(actual_value, expect_value)
                elif check_type in ["le", "less_or_equals"]:
                    validate.less_than_or_equals(actual_value, expect_value)
                elif check_type in ["gt", "greater_than"]:
                    validate.greater_than(actual_value, expect_value)
                elif check_type in ["ne", "not_equal"]:
                    validate.not_equals(actual_value, expect_value)
                elif check_type in ["str_eq", "string_equals"]:
                    validate.string_equals(actual_value, expect_value)
                elif check_type in ["len_eq", "length_equal"]:
                    validate.length_equals(actual_value, expect_value)
                elif check_type in ["len_gt", "length_greater_than"]:
                    validate.length_greater_than(actual_value, expect_value)
                elif check_type in ["len_ge", "length_greater_or_equals"]:
                    validate.length_greater_than_or_equals(actual_value, expect_value)
                elif check_type in ["len_lt", "length_less_than"]:
                    validate.length_less_than(actual_value, expect_value)
                elif check_type in ["len_le", "length_less_or_equals"]:
                    validate.length_less_than_or_equals(actual_value, expect_value)
                elif check_type in ["contains"]:
                    validate.contains(actual_value, expect_value)
                else:
                    if hasattr(validate, check_type):
                        getattr(validate, check_type)(actual_value, expect_value)
                    else:
                        # print(f'{check_type}  not valid check type')
                        raise Exception(f'{check_type}  not valid check type')

    @staticmethod
    def upload_file(file_path):
        """根据文件路径，自动获取文件名称和文件mime类型"""
        if not file_path.exists():
            logger.error(f'{file_path} not exists')
            return
        mime_type = mimetypes.guess_type(file_path)[0]
        print("mime_type=", mime_type)
        return (
            file_path.name, file_path.open("rb"), mime_type)

    def multipart_request(self, request_value, root_dir):
        """判断请求头部 Content-Type: multipart/form-data 格式支持"""
        if "files" in request_value.keys():
            fields = []
            for key, value in request_value.get("files", {}).items():
                # 文件路径
                if Path(root_dir).joinpath(value).is_file():
                    fields.append((key, self.upload_file(Path(root_dir).joinpath(value).resolve())))
                else:
                    fields.append((key, value))
            m = MultipartEncoder(fields=fields)
            request_value.pop('files')  # 去掉 files 参数
            request_value["data"] = m
            headers = {"Content-Type": m.content_type}   # 添加请求头
            request_value["headers"] = headers
            return request_value
        else:
            return request_value


class ExecRunner:

    @staticmethod
    def ssh_con(host, port, username, password):
        """
        发送请求
        """
        ssh_client = user_ssh_client(host, port, username, password)
        return ssh_client

    @staticmethod
    def extract_response2(response, extract_obj):
        """提取返回结果"""
        extract_result = {}
        if isinstance(extract_obj, dict):
            for extract_var, extract_expression in extract_obj.items():
                extract_var_value = extract.extract_by_object2(response[0], extract_expression)  # 实际结果
                extract_result[extract_var] = extract_var_value
            return extract_result
        else:
            return extract_result

    @staticmethod
    def validate_response2(response, validate_check):
        """
        校验结果
        """
        for check in validate_check:
            for check_type, check_value in check.items():
                actual_value = extract.extract_by_object2(response, check_value[0])  # 实际结果
                expect_value = check_value[1]  # 期望结果
                if check_type in ["eq", "equals", "equal"]:
                    validate.equals(actual_value, expect_value)
                elif check_type in ["lt", "less_than"]:
                    validate.less_than(actual_value, expect_value)
                elif check_type in ["le", "less_or_equals"]:
                    validate.less_than_or_equals(actual_value, expect_value)
                elif check_type in ["gt", "greater_than"]:
                    validate.greater_than(actual_value, expect_value)
                elif check_type in ["ne", "not_equal"]:
                    validate.not_equals(actual_value, expect_value)
                elif check_type in ["str_eq", "string_equals"]:
                    validate.string_equals(actual_value, expect_value)
                elif check_type in ["len_eq", "length_equal"]:
                    validate.length_equals(actual_value, expect_value)
                elif check_type in ["len_gt", "length_greater_than"]:
                    validate.length_greater_than(actual_value, expect_value)
                elif check_type in ["len_ge", "length_greater_or_equals"]:
                    validate.length_greater_than_or_equals(actual_value, expect_value)
                elif check_type in ["len_lt", "length_less_than"]:
                    validate.length_less_than(actual_value, expect_value)
                elif check_type in ["len_le", "length_less_or_equals"]:
                    validate.length_less_than_or_equals(actual_value, expect_value)
                elif check_type in ["contains"]:
                    validate.contains(actual_value, expect_value)
                else:
                    if hasattr(validate, check_type):
                        getattr(validate, check_type)(actual_value, expect_value)
                    else:
                        # print(f'{check_type}  not valid check type')
                        raise Exception(f'{check_type}  not valid check type')

    def exec_cmd(self, step):
        """
        执行shell命令
        """
        # 优先从step中读取ssh登录信息，没有则从env文件中读取
        if step.get("ssh_client", "") != "":
            ssh_info = eval(step["ssh_client"])
            ssh_client = self.ssh_con(*ssh_info)
        else:
            ssh_info = get_envs_from_yml()["ssh_client"]
            ssh_client = self.ssh_con(*ssh_info)
        if step.get("k8s_agent", "") is True:
            cmd = DOCKER_CONTAINER_COMMAND + f"'{step['shell']}'"
        else:
            cmd = step["shell"]
        logger.info(f"-------- command --------\n"
                    f"{step['shell']}")
        response = ssh_client.exec_command(cmd)
        logger.info(f"-------- response --------\n"
                    f"{response}")
        return response


class Runner(ApiRunner, ExecRunner):
    def __init__(self, raw: dict, module: types.ModuleType):
        self.raw = raw  # 读取yml原始数据
        self.module = module  # 动态创建的module模型
        self.module_variable = {}  # 模块变量
        self.context = {}  # 全局变量
        # self.handlers = {}  # ApiRunner

    def runner(self, pytestconfig):
        # pytestconfig是pytest配置对象
        case_name = self.raw.get('name', '')  # 测试用例名字
        steps = self.raw.get("steps", [])  # 获取测试步骤
        skip = self.raw.get("skip", "")
        tags = self.raw.get("tags", [])

        if isinstance(steps, dict):
            steps = [steps]

        config = self.raw.get('config', {})  # 公共参数
        if config:
            config_variables = config.get('variables', {})
            config_fixtures = config.get('fixtures', [])  # fixture
            config_params = config.get('parameters', [])  # 参数化变量
            config_indirect = config.get('indirect', False)
        else:
            config_variables = {}
            config_fixtures = []
            config_params = []
            config_indirect = False

        # 模块变量渲染
        self.context.update(__builtins__)  # noqa 内置函数加载
        self.context.update(my_builtins.__dict__)  # 自定义函数加载
        if config_variables:
            self.module_variable = rend_template_any(config_variables, **self.context)
            # print("module_variable=", self.module_variable)
        # 模块变量: 添加到模块全局变量
        if isinstance(self.module_variable, dict):
            self.context.update(self.module_variable)

        # 参数化数据
        config_params = rend_template_any(config_params, **self.context)
        config_fixtures = rend_template_any(config_fixtures, **self.context)
        if config_params:
            config_params = config_params if isinstance(config_params[0], list) else [config_params]
        config_fixtures, config_params = self.parameters_data(config_fixtures, config_params)

        def is_include():
            """
            包含标签
            """
            include = pytestconfig.getoption("--include")
            if include == "":
                return True
            flag = False
            include_tags = include.split(",")
            for include_tag in include_tags:
                if include_tag in tags:
                    flag = True
                    break
            return flag

        def is_exclude():
            """
            排除标签
            """
            exclude = pytestconfig.getoption("--exclude")
            if exclude == "":
                return False
            exclude_tags = exclude.split(",")
            for exclude_tag in exclude_tags:
                return exclude_tag in tags
            return False

        # 有skip标签则跳过
        if skip:
            print(f"跳过测试用例：{case_name}")
            return

        #  过滤exclude标签的案例，包含则跳过
        if is_exclude():
            return

        # 收集只包含include的标签
        if is_include():
            step_fixtures, step_params = [], []
            step_indirect = False
            for raw in steps:
                if "fixtures" in raw:
                    step_raw_fixture = raw.get("fixtures", "")
                    step_fixtures = rend_template_any(step_raw_fixture, **self.context)
                if "parameters" in raw:
                    step_raw_parameter = raw.get("parameters", [])
                    step_params = rend_template_any(step_raw_parameter, **self.context)
                if "indirect" in raw:
                    step_raw_indirect = raw.get("indirect", True)
                    step_indirect = rend_template_any(step_raw_indirect, **self.context)

            # step中的参数化
            if step_params:
                step_params = step_params if isinstance(step_params[0], list) else [step_params]

            step_fixtures, step_params = self.parameters_data(step_fixtures, step_params)

            def run_case(args):
                """
                args字典中的键值对是根据测试用例中的参数化值和fixture的值动态生成的
                """
                # 获取fixtures
                request_session = args.get('request_session')
                remove = args.get('remove')

                root_dir = args.get("request").config.rootdir  # 内置request 获取root_dir

                # print("root_dir=", root_dir)

                # 加载参数化的值和fixture的值
                self.context.update(args)

                # 获取被调用的函数名称
                logger.info(f"执行文件-> {self.module.__name__}.yml")
                logger.info(f"用例名称-> {case_name}")
                logger.info(f"variables-> {config_variables}")
                logger.info(f"fixtures-> {config_fixtures}")
                logger.info(f"parameters-> {config_params}")

                for step in steps:
                    response = None
                    step_context = self.context.copy()
                    # 支持跳过测试步骤
                    if "skip" in step and step["skip"]:
                        continue
                    for item, value in step.items():
                        if item == "name":
                            logger.info(f"----  request name: {value} ----")
                        elif item == "sleep":
                            time.sleep(value)
                        elif item == "fixtures":
                            pass
                        elif item == "parameters":
                            pass
                        elif item == "indirect":
                            pass
                        elif item == "variables":  # 获取步骤中的变量
                            copy_value = copy.deepcopy(value)
                            step_variables_value = rend_template_any(copy_value, **self.context)
                            step_context.update(step_variables_value)
                        elif item == "request":  # 发送请求
                            copy_value = copy.deepcopy(value)  # 深拷贝一份新的value:否则参数化时会修改yml文件中的初始值
                            # request_value = rend_template_any(copy_value, **self.context)
                            request_value = rend_template_any(copy_value, **step_context)
                            response = self.run(request_value, request_session, root_dir)
                        elif item == "validate":  # request验证返回值
                            copy_value = copy.deepcopy(value)  # 深拷贝一份新的value
                            # validate_value = rend_template_any(copy_value, **self.context)
                            validate_value = rend_template_any(copy_value, **step_context)
                            self.validate_response(response, validate_value)
                            # print("**validate_value**", validate_value)
                            logger.info(f'validate 校验内容-> {validate_value}')
                        elif item == "extract":  # request提取变量
                            copy_value = copy.deepcopy(value)  # 深拷贝一份新的value
                            # extract_value = rend_template_any(copy_value, **self.context)
                            extract_value = rend_template_any(copy_value, **step_context)
                            extract_result = self.extract_response(response, extract_value)
                            # print("extract_result=", extract_result)
                            logger.info(f'extract 提取变量-> {extract_result}')
                            # 添加到模块变量
                            self.module_variable.update(extract_result)
                            if isinstance(self.module_variable, dict):
                                self.context.update(self.module_variable)
                        elif item == "api":
                            # root_dir = args.get("request").config.rootdir  # 内置request 获取root_dir
                            api_path = Path(root_dir).joinpath(value)  # api文件存放路径
                            # print("api_path=", api_path)
                            raw_api = yaml.safe_load(api_path.open(encoding='utf-8'))  # 加载yaml文件
                            copy_value = copy.deepcopy(raw_api)  # 深拷贝一份新的value
                            # request_value = rend_template_any(copy_value.get('request'), **self.context)
                            request_value = rend_template_any(copy_value.get('request'), **step_context)
                            response = self.run(request_value, request_session, root_dir)
                            # print("response=", response)
                        elif item == "exec":
                            copy_value = copy.deepcopy(value)
                            # exec_value = rend_template_any(copy_value, **self.context)
                            exec_value = rend_template_any(copy_value, **step_context)
                            response = self.exec_cmd(exec_value)
                            # print("response=", response)
                        elif item == "validate2":  # exec验证返回值
                            copy_value = copy.deepcopy(value)  # 深拷贝一份新的value
                            # validate_value = rend_template_any(copy_value, **self.context)
                            validate_value = rend_template_any(copy_value, **step_context)
                            # print("**validate2_value**", validate_value)
                            self.validate_response2(response, validate_value)
                            logger.info(f'validate 校验内容-> {validate_value}')
                        elif item == "extract2":  # exec提取变量
                            copy_value = copy.deepcopy(value)  # 深拷贝一份新的value
                            # extract_value = rend_template_any(copy_value, **self.context)
                            extract_value = rend_template_any(copy_value, **step_context)
                            extract_result = self.extract_response2(response, extract_value)
                            logger.info(f'extract 提取变量-> {extract_result}')
                            # print("extract_result=", extract_result)
                            # 添加到模块变量
                            self.module_variable.update(extract_result)
                            if isinstance(self.module_variable, dict):
                                self.context.update(self.module_variable)
                        elif item == "remove":
                            copy_value = copy.deepcopy(value)  # 深拷贝一份新的value
                            remove_value = rend_template_any(copy_value, **self.context)
                            values = remove_value.split(",")
                            for val in values:
                                remove(val)
                                logger.info(f'后置处理，清理资源-> {val}')
                        else:
                            try:
                                # 支持python原生函数，例如print
                                copy_value = copy.deepcopy(value)
                                # value = rend_template_any(copy_value, **self.context)
                                value = rend_template_any(copy_value, **step_context)
                                eval(item)(value)
                            except Exception as msg:
                                print(msg)

            fun_fixtures = []
            # fun_params = []
            # 合并config 和 case 用例 fixtures
            fun_fixtures.extend(config_fixtures)
            # [fun_fixtures.append(fixture) for fixture in step_fixtures]
            [fun_fixtures.append(fixture) for fixture in step_fixtures if fixture not in fun_fixtures]

            # 参数化以step优先
            # fun_params = step_params or config_params

            # 合并config 和 case 用例 params
            fun_params = config_params
            # 将step_params的元素添加到fun_params中
            if step_params:
                for param in step_params:
                    fun_params.append(param)

            fun_indirect = step_indirect or config_indirect

            f = create_function_from_parameters(
                func=run_case,
                # parameters 传内置fixture和用例fixture
                parameters=self.function_parameters(fun_fixtures),
                documentation=case_name,
                func_name=str(self.module.__name__),
                func_filename=f"{self.module.__name__}.py",
            )
            setattr(self.module, str(self.module.__name__), f)

            if fun_params:
                # 向 module 中加参数化数据的属性，参数化时使用
                setattr(self.module, 'params_data', fun_params)

            # 向 module 中加参数化数据的indirect属性，参数化时使用
            setattr(self.module, 'params_indirect', fun_indirect)

    @staticmethod
    def function_parameters(config_fixtures) -> list:
        """测试用例传内置fixture和自定义fixture"""
        # 内置request fixture
        function_parameters = [
            Parameter("request", Parameter.POSITIONAL_OR_KEYWORD),
        ]

        """
        获取传递给用例的fixtures
        格式1，字符串形式，逗号隔开
        config:
            fixtures: fixture_name1,  fixture_name2
        格式2：列表形式
        config:
            fixtures: [fixture_name1,  fixture_name2]
        """

        # 获取传给用例的fixtures
        if isinstance(config_fixtures, str):
            config_fixtures = [item.strip(" ") for item in config_fixtures.split(',')]
        if not config_fixtures:
            function_parameters.append(
                Parameter('request_session', Parameter.POSITIONAL_OR_KEYWORD),
            )
            function_parameters.append(
                Parameter('remove', Parameter.POSITIONAL_OR_KEYWORD),
            )
        else:
            if 'request_function' in config_fixtures:
                function_parameters.append(
                    Parameter('request_function', Parameter.POSITIONAL_OR_KEYWORD),
                )
            elif 'request_module' in config_fixtures:
                function_parameters.append(
                    Parameter('request_module', Parameter.POSITIONAL_OR_KEYWORD),
                )
            else:
                function_parameters.append(
                    Parameter('request_session', Parameter.POSITIONAL_OR_KEYWORD),
                )
            for fixture in config_fixtures:
                if fixture not in ['request_function', 'request_module', "request_session"]:
                    function_parameters.append(
                        Parameter(fixture, Parameter.POSITIONAL_OR_KEYWORD),
                    )
        # print("function_parameters=", function_parameters)
        return function_parameters

    @staticmethod
    def parameters_data(fixtures, parameters):
        """
        参数化实现2种方式：
        方式1：
            config:
               fixtures: username, password
               parameters:
                 - [test1, '123456']
                 - [test2, '123456']
        方式2：
            config:
               parameters:
                 - {"username": "test1", "password": "123456"}
                 - {"username": "test2", "password": "1234562"}
        :returns
        fixtures: 用例需要用到的fixtures:  ['username', 'password']
        parameters: 参数化的数据list of list : [['test1', '123456'], ['test2', '123456']]
        """
        if isinstance(fixtures, str):
            # 字符串切成list
            fixtures = [item.strip(" ") for item in fixtures.split(',')]
        if isinstance(parameters, list) and len(parameters) >= 1:
            if isinstance(parameters[0], dict):
                # list of dict
                params = list(parameters[0].keys())
                new_parameters = []
                for item in parameters:
                    new_parameters.append(list(item.values()))
                # fixtures 追加参数化的参数
                for param in params:
                    if param not in fixtures:
                        fixtures.append(param)
                return fixtures, new_parameters
            else:
                # list of list
                return fixtures, parameters
        else:
            return fixtures, []

