==========
pytest-api
==========

REST API的通用测试框架，依赖pytest框架，整体是只是pytest框架的插件

----

Requirements
------------

* python3.8+
* pytest 7.2


支持功能列表
------------
* 基于 pytest 框架安装插件即可使用，环境非常简单
* 支持全局仅登录一次，在用例中自动在请求头部添加认证信息
* 支持全局header和局部单个api header
* 支持提取api返回值，返回值可在后续api中使用
* 支持打tag标签，执行可过滤和筛选，支持和TP案例ID联动
* 支持baisc授权，可支持全局授权和局部单个api授权
* 支持跳过测试用例个单个api测试步骤
* 支持通过命令行方式、pytest.ini或者env.yml指定测试环境
* 使用jinja2进行模板渲染，支持在yml中使用自定义函数

