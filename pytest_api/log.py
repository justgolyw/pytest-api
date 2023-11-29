#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def remove_log_by_create_time(log_dir, count=4, suffix=".log"):
    """
    判断log目录文件大于4个，按文件创建时间删除
    :param log_dir: log日志目录
    :param count: 保留log文件数量
    :param suffix: 查找log文件后缀
    :return: None
    """
    if not log_dir.exists():
        return
    # 查找log文件
    logs = [item for item in log_dir.iterdir() if item.is_file() and item.suffix == suffix]
    # 按创建时间倒序排列
    logs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    # 删除多余的log
    for item in logs[count:]:
        item.unlink()


def set_log_format(config):
    """设置 log 日志格式"""
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    if not config.getini('log_file') and not config.getoption('log_file'):
        config.option.log_file = Path(config.rootdir).joinpath('logs', f'{current_time}.log')
    if not config.getini('log_file_level') and not config.getoption('log_file_level'):
        config.option.log_file_level = "info"
    # log_file_format和log_file_date_format的默认值为
    # '%(levelname)-8s %(name)s:%(filename)s:%(lineno)d %(message)s'、%H:%M:%S
    if config.getini('log_file_format') == '%(levelname)-8s %(name)s:%(filename)s:%(lineno)d %(message)s' \
            and not config.getoption('log_file_format'):
        config.option.log_file_format = "%(asctime)s [%(levelname)s]: %(message)s"
    if config.getini('log_file_date_format') == '%H:%M:%S' and not config.getoption('log_file_date_format'):
        config.option.log_file_date_format = "%Y-%m-%d %H:%M:%S"

    # 设置日志文件在控制台的输出格式
    if not config.getini('log_cli_format') and not config.getoption('log_cli_format'):
        config.option.log_cli_format = '%(asctime)s [%(levelname)s]: %(message)s'
    if not config.getini('log_cli_date_format') and not config.getoption('log_cli_date_format'):
        config.option.log_cli_date_format = '%Y-%m-%d %H:%M:%S'

    # 只保留最近 5 个 log 文件
    log_dir = Path(config.rootdir).joinpath('logs')
    remove_log_by_create_time(log_dir=log_dir)
