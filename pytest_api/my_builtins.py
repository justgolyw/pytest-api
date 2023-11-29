#!/usr/bin/env python
# -*- coding: utf-8 -*-
import yaml
import random
import logging
from pathlib import Path
from .log import logger
# logger = logging.getLogger(__name__)


def random_num():
    """
    生成随机数据
    """
    return random.randint(0, 1000)


def random_str():
    """
    生成随机字符串
    """
    return 'test-{0}-{1}'.format(random_num(), random_num())


def split_str(string, sep):
    """
    :param string: 原始字符串
    :param sep: 分割符
    """
    ret = string.split(sep)
    return ret


def int2str(num):
    """
    将整形转换为字符串类型
    :param num:
    :return:
    """
    return str(num)


def username():
    """
    生成随机的用户名
    """
    return 'user_' + str(random.randint(0, 1000))


def read_file(file_path):
    """
    读取yaml文件数据参数化
    :param file_path: 文件路径
    :return:
    """
    path = Path(file_path)
    # print("path=", path)
    if not path.exists():
        logging.error(f"文件路径不存在：{path.absolute()}")
        return
    logger.info(f"读取文件路径：{path.absolute()}")
    if path.suffix in [".yml", ".yaml"]:
        res = yaml.safe_load(path.read_text(encoding="utf8"))
        return res
    else:
        logger.error("文件格式不支持")
