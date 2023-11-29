import logging
from jinja2 import Template, Environment
from .log import logger


# logger = logging.getLogger(__name__)


def to_str(value):
    return str(value)


def add(value, num=0):
    """jinja2 过滤器 add函数"""
    return int(value) + num


# jinja2 过滤器
env_filter = Environment(
    variable_start_string='${', variable_end_string='}'
)

env_filter.filters["str"] = to_str
env_filter.filters["add"] = add


# print(env_filter.filters)


def rend_template_str(template_str, *args, **kwargs):
    """
    渲染模板字符串, 改写了默认的引用变量语法{{var}}, 换成${var}
    模板中引用变量语法 ${var},
    调用函数 ${fun()}
    :return: 渲染之后的值
    """
    # instance_template = Template(template_str, variable_start_string='${', variable_end_string='}')
    instance_template = env_filter.from_string(template_str)
    template_render_res = instance_template.render(*args, **kwargs)
    if template_str.startswith("${") and template_str.endswith("}"):
        template_raw_str = template_str.rstrip('}').lstrip('${')
        # print("template_raw_str=", template_raw_str)
        if kwargs.get(template_raw_str):
            logger.info(
                f"取值表达式: {template_str}, 取值结果：{kwargs.get(template_raw_str)} {type(kwargs.get(template_raw_str))}")
            return kwargs.get(template_raw_str)

        elif template_raw_str.startswith("int(") and template_raw_str.endswith(")"):
            logger.info(f"取值表达式: {template_str}, 取值结果：{template_render_res} {type(int(template_render_res))}")
            return int(template_render_res)

        elif template_raw_str.startswith("str(") and template_raw_str.endswith(")"):
            logger.info(f"取值表达式: {template_str}, 取值结果：{template_render_res} {type(template_render_res)}")
            return str(template_render_res)

        else:
            logger.info(f"取值表达式: {template_str}, 取值结果：{template_render_res}  {type(template_render_res)}")
            return template_render_res
    else:
        return template_render_res


def rend_template_obj(t_obj: dict, *args, **kwargs):
    """
    传 dict 对象，通过模板字符串递归查找模板字符串，转行成新的数据
    """
    if isinstance(t_obj, dict):
        for key, value in t_obj.items():
            if isinstance(value, str):
                t_obj[key] = rend_template_str(value, *args, **kwargs)
            elif isinstance(value, dict):
                rend_template_obj(value, *args, **kwargs)
            elif isinstance(value, list):
                t_obj[key] = rend_template_array(value, *args, **kwargs)
            else:
                pass
    return t_obj


def rend_template_array(t_array, *args, **kwargs):
    """
    传 list 对象，通过模板字符串递归查找模板字符串
    """
    if isinstance(t_array, list):
        new_array = []
        for item in t_array:
            if isinstance(item, str):
                new_array.append(rend_template_str(item, *args, **kwargs))
            elif isinstance(item, list):
                new_array.append(rend_template_array(item, *args, **kwargs))
            elif isinstance(item, dict):
                new_array.append(rend_template_obj(item, *args, **kwargs))
            else:
                new_array.append(item)
        return new_array
    else:
        return t_array


def rend_template_any(any_obj, *args, **kwargs):
    """渲染模板对象:str, dict, list"""
    if isinstance(any_obj, str):
        return rend_template_str(any_obj, *args, **kwargs)
    elif isinstance(any_obj, dict):
        return rend_template_obj(any_obj, *args, **kwargs)
    elif isinstance(any_obj, list):
        return rend_template_array(any_obj, *args, **kwargs)
    else:
        return any_obj
