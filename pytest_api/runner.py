import time
import types
from inspect import Parameter
from . import my_builtins, validate
from .create_function import create_function_from_parameters
from .render import rend_template_any
from . import extract


class ApiRunner:

    # @classmethod
    # def from_config_and_env(cls):
    #     return cls()

    @staticmethod
    def _run(request, session):
        '''
        发送请求
        '''
        # return self.send_request(**request)
        return session.send_request(**request)

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

    def run(self, step, session):
        res_param = {}
        # 发送请求
        assert "request" in step, "步骤中必须要有request字段，请检查当前yml文件"
        r = self._run(step["request"], session)
        # 请求对比
        if "response" in step:
            self.validate_response(r, step["response"])
        # 返回值处理
        if "return" in step:
            extract_result = self.extract_response(r, step["return"])
            print("extract_result=", extract_result)
        return res_param


class Runner(ApiRunner):
    def __init__(self, raw: dict, module: types.ModuleType):
        self.raw = raw  # 读取yml原始数据
        self.module = module  # 动态创建的module模型
        self.module_variable = {}  # 模块变量
        self.context = {}  # 全局变量
        self.handlers = {}  # ApiRunner

    def register_handler(self, key, handler):
        self.handlers[key] = handler

    def runner(self, pytestconfig):
        # config是pytest配置对象
        case_name = self.raw.get('name', '')  # 测试用例名字
        steps = self.raw.get("steps", [])  # 获取测试步骤
        config = self.raw.get('config', {})  # 公共参数
        config_variables = config.get('variables', {}) if config else {}

        # tags = self.raw["tags"] if "tags" in self.raw else []
        skip = self.raw.get("skip", "")
        tags = self.raw.get("tags", [])

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
            # 模块变量渲染
            self.context.update(__builtins__)  # noqa 内置函数加载
            self.context.update(my_builtins.__dict__)  # 自定义函数加载
            self.module_variable = rend_template_any(config_variables, **self.context)
            self.context.update(self.module_variable)

            def run_case(args):
                for step in steps:
                    # 支持跳过单个测试步骤
                    if "skip" in step and step["skip"]:
                        continue
                    for item, value in step.items():
                        if item == "name":
                            continue
                        elif item == "sleep":
                            time.sleep(value)
                        else:  # item = api
                            request_session = args.get('request_session')  # session 请求会话
                            # 通过调用from_config_and_env这个类方法将ip, port, urlprefix这三个参数传入，构造完整的url
                            # handler = self.handlers[item].from_config_and_env(config)
                            print("request_session=", request_session)
                            step = rend_template_any(value, **self.context)
                            print("step:", step)
                            # res_param为response返回值
                            # res_param = ApiRunner().run(step, request_session)
                            res_param = self.run(step, request_session)
                            self.context.update(res_param)

            f = create_function_from_parameters(
                func=run_case,
                # parameters 传内置fixture
                parameters=[
                    Parameter('request_session', Parameter.POSITIONAL_OR_KEYWORD),
                ],
                documentation=case_name,
                func_name=str(self.module.__name__),
                func_filename=f"{self.module.__name__}.py",
            )
            setattr(self.module, str(self.module.__name__), f)
