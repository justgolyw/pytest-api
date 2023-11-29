from pathlib import Path
from collections import ChainMap
from .common import read_yaml, getcwd

defaults_envs = {
    "proto": "https",
    "urlprefix": "",
    "headers": None,
    "auth": None
}


def get_envs_from_yml():
    """从yml文件读取配置信息"""
    env_path = Path(getcwd()) / Path("env.yml")
    print("env_path=", env_path)
    # envs = {}
    # if env_path.exists():
    #     envs = read_yaml(env_path)
    try:
        envs = read_yaml(env_path)
    except FileNotFoundError:
        raise FileNotFoundError
    return envs


def get_envs_from_cmd(config):
    """从命令行读取配置信息"""
    user = config.getoption("--user")
    password = config.getoption("--password")
    host = config.getoption("--host")
    port = config.getoption("--port")

    env = {}
    if user and password:
        env["auth"] = [user, password]
    if host:
        env["host"] = host
    if port:
        env["port"] = port
    return env


def get_envs_from_ini(config):
    """从pytest.ini读取配置信息"""
    host = config.getini('host')
    port = config.getini('port')
    env = {}
    if host:
        env["host"] = host
    if port:
        env["port"] = port
    return env


def get_envs(config):
    """
    优先从命令行获取，没有则从yml文件获取，再没有从默认值中获取
    """
    cmd_envs = get_envs_from_cmd(config)
    yml_envs = get_envs_from_yml()
    envs = ChainMap(cmd_envs, yml_envs, defaults_envs)
    # print("envs=", envs)
    return envs


# def get_envs(config):
#     """
#     优先从命令行获取，没有则从ini文件获取，再没有从默认值中获取
#     """
#     cmd_envs = get_envs_from_cmd(config)
#     ini_envs = get_envs_from_ini(config)
#     envs = ChainMap(cmd_envs, ini_envs, defaults_envs)
#     return envs
