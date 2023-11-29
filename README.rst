==========
pytest-api
==========

REST API的通用测试框架，依赖pytest框架，整体是只是pytest框架的插件

支持功能列表
------------
* 支持pip install进行插件安装
* 支持全局仅登录一次，自动在request请求头中添加认证信息
* yml文件中支持定义变量与引用变量
* yml支持提取与引用返回值，实现多个接口的参数关联
* yml中支持python原生函数和自定义函数的引用
* yml中支持自定义fixture功能
* yml中支持用例参数化parameters功能
* yml中支持tags标签，执行可过滤和筛选
* yml中支持skip标记跳过测试用例执行
* yml中支持sleep在测试步骤中添加延时
* 支持用例分层：api层和case层，case层中可以引用api层中的api
* 支持执行动作扩展，可在yml中写shell命令
* 支持通过命令行方式、pytest.ini指定测试环境
* 支持根据swagger.json自动生成yml文件接口用例
* 支持项目脚手架，快速创建项目demo
* 支持文件上传功能
* 支持后置处理清理资源
* 支持从外部文件读取参数化数据

项目路径
------------
http://mq.code.sangfor.org/paas/kubespace/automatic-test/tree/pytest-api-develop

插件安装
------------
进入项目目录下执行：pip install -U .

用例结构
------------

建议目录结构
::
    apis:           # 存放接口描述信息的目录，可以带上基本的校验，可选文件
    cases           # 存放测试案例的目录，用例层通过api关键字导入需要的API, 必选文件
    env.yml         # 公共的环境配置文件，可选文件
    pytest.ini      # pytest以及公共的环境配置的配置信息，可选文件
    conftest.py     # 在这个文件中可以自定义fixture和自定义函数，可选文件

API参数说明
::

    name: 用例名称                          # 用例名称，可选
    tags: ['BVT']                         # 用例标签，可选
    skip: false                           # 是否跳过该用例，skip: true跳过当前用例，可选
    config:                               # 用例配置项，可选
      variables:                          # 变量声明，可选
        var1: test1
      fixtures: fixture1                  # fixture引用， 可选

    steps:                                # 用例步骤参数，必选
      -
        name: 步骤1，发送request请求         # 步骤名称，可选
        sleep: 1                          # 延时1秒，可选
        skip: false                       # 是否跳过该步骤，skip: true跳过当前步骤，可选
        request:                          # 执行request请求，必选
          url: /v3/xxx                    # url, 必选
          method: POST                    # 请求方法，不区分大小写，必选
          json:                           # post请求参数，可选
            name: test1
          params:                         # get请求参数,也可以把请求参数写在url上， 可选
            limit: 1
        validate:                         # 返回值校验参数， 可选
          - eq: [status_code, 201]        # 状态码校验， 可选
          - eq: [$.name, test1]           # 返回值校验， 可选
        extract:                          # 返回值提取参数, 可选
          name1: $.name                   # 从response返回值中获取name赋值给name1

      -
        name: 步骤2，执行shell命令           # 步骤名称，可选
        exec:                             # 执行shell命令，必选
          ssh_client: [10.74.60.2, 22, root, Sangfor-paas.237] # ssh登录信息，必选
          k8s_agent: false                                     # 是否进入k8s_agent容器，k8s_agent: true进入容器，可选
          shell: kubectl get ns -A                             # shell命令，必选
        validate2:                                             # 执行shell命令后结果校验，可选
          - eq: ["*", default]                                 # 校验返回值是否存在指定值


用例编写
------------

1. 变量的声明与引用
>>>>>>>>>>>>>>>>>>>

目前只支持在config声明整个yml文件的全局变量（不支持单个step的变量），通过${var}进行变量的引用
::
    name: 变量的声明与引用
    config:
      variables:
        username: test1
        password: Admin@123
    steps:
      -
        name: 添加user1
        request:
          url: /v3/user
          method: POST
          json:
            username: ${username}
            password: ${password}
        validate:
          - eq: [status_code, 201]

2. 自定义函数的使用
>>>>>>>>>>>>>>>>>>>

声明变量时我们希望变量的值是可变的，一些复杂的逻辑处理，也需自己写代码去实现，我们可以通过实现自定义的函数来实现这一功能，
在这个框架中我已经实现了如下几个自定义函数，可以直接在yml中进行调用
::
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

其他自定义函数的实现，需在conftest.py文件中实现，例如
::

    import pytest
    import random
    from pytest_api import my_builtins


    def username():
        """
        生成随机的用户名
        """
        return 'user_' + str(random.randint(0, 1000))

    # 注册到插件内置模块上
    my_builtins.username = username

实现基本原理是自己定义一个函数，然后注册到插件内置模块my_builtins上，这样我们在测试用例中就可以使用该函数方法了。

如下用例引用自定义函数username
::
    name: 自定义函数的使用
    config:
      variables:
        username: ${username()}
        password: Admin@123
    steps:
      -
        name: 添加user
        request:
          url: /v3/users
          method: POST
          json:
            username: ${username}
            password: ${password}
            name: ${username}
        validate:
          - eq: [status_code, 201]

3. 自定义fixture的使用
>>>>>>>>>>>>>>>>>>>>>

在conftest.py文件中实现你需要的fixture功能, scope的范围为function、module或session
::
    @pytest.fixture()
    def demo_fixture():
        print("用例前置操作->do something .....")
        yield
        print("用例后置操作，do something .....")

然后在yml文件中引用
::
    name: 自定义fixture的使用
    config:
      fixtures: demo_fixture
    steps:
      -
        name: 获取user
        request:
          url: /v3/users
          method: GET
        validate:
          - eq: [status_code, 200]

当yml中的用例需要用到多个fixtures时, 支持2种格式进行引用
::
    name: 多个自定义fixture的使用
    config:
      fixtures: fixture1, fixture2     # 使用逗号隔开
    # fixtures: [fixture1, fixture2]   # 使用列表形式
    steps:
      -
        name: 获取user
        request:
          url: /v3/users
          method: get
        validate:
          - eq: [status_code, 200]

4. 参数化parameters的使用
>>>>>>>>>>>>>>>>>>>>>>>>

当一个测试用例需要用到多组测试数据的时候，我们必然会用到参数化，pytest中默认的参数化使用@pytest.mark.parametrize，
我们在yaml文件中实现参数化的方式如下
::
    name: 测试用例参数化实现
    config:
      parameters:
        - {"username": "test1", "password": "Test1@123"}
        - {"username": "test2", "password": "Test2@123"}
    steps:
      -
        name: 添加user
        request:
          url: /v3/user
          method: POST
          json:
             username: ${username}
             password: ${password}
        validate:
          - eq: [status_code, 201]

5. validate参数返回值校验
>>>>>>>>>>>>>>>>>>>>>>>>

对于接口的返回值我们除了需要校验响应码外，一般还需要校验参数的返回值，在yml中使用validate关键字进行返回值校验。
校验值可以支持response取值对象：status_code, headers, cookies, json等。返回值返回的是json格式，那么可以支持以下取值语法：

- jmespath 语法: response.key1.key2
- jsonpath 语法: $..key1
- re 正则语法: xx(.+?)xxx
- 如果返回的不是 json 格式，那么可以用正则re取值，例如exec的返回值校验

举个例子
::
    name: 参数值提取与校验
    config:
      variables:
        clusterId: c-mj6ft
        pro_name: ${random_str()}
    steps:
      -
        name: 创建项目
        request:
          url: /v3/project
          method: POST
          json:
            clusterId: ${clusterId}
            name: ${pro_name}
        validate:
          - eq: [status_code, 201]
          - eq: [headers."Content-Type", application/json]
          - eq: [response.name, '${pro_name}']
          - eq: [$..name, '${pro_name}']
          - eq: ['"name":*"(.+?)"', '${pro_name}']

validate 支持以下几种通用的校验类型：

- eq: == 等于
- ne: != 不等于
- lt: < 小于
- gt: > 大于

6. extract参数返回值提取
>>>>>>>>>>>>>>>>>>>>>>>>

在自动化用例中有多个接口，下一个接口需要获取上一个接口的返回值， 我们通过extract提取接口返回值进行参数的关联，下面举一个例子
::
    name: 参数提取与关联
    config:
      variables:
        clusterId: c-mj6ft
        name: ${random_str()}
    steps:
      -
        name: 创建project
        request:
          url: /v3/project
          method: POST
          json:
            clusterId: ${clusterId}
            name: ${name}
        response:
          - eq: [ status_code, 201 ]
        extract:
           proj_id: $.id
      -
        name: 创建namespace
        request:
          url: /v3/clusters/${clusterId}/namespace
          method: POST
          json:
            clusterId: ${clusterId}
            projectId: ${proj_id}
            name: ${name}
        validate:
          - eq: [status_code, 201]
          - eq: [$.name, '${name}']

在这个例子中通过extract关键字提取了创建project返回值中的项目id的值（proj_id），接下来在创建namespace时引用了proj_id的值。

- extract 支持以下几种取值语法对json格式进行取值：
- jmespath 语法: response.key1.key2
- jsonpath 语法: $..key1
- re 正则语法: xx(.+?)xxx
- 如果返回的不是 json 格式，那么可以用正则re取值

7. 测试用例分层
>>>>>>>>>>>>>>>>>>>>>>>>

当我们在测试用例中需反复去调用同一个接口时我们最好将这些接口进行封装，以便进行API的复用，
那么在yml 文件中，我们可以把单个API写到一个yml文件，测试用例去调用导入API。于是测试用例可以分成2层

- API层: 描述接口request请求，可以带上validate 基本的校验
- case层: 用例层多个步骤按顺序引用API

如上面的创建命名空间的测试，我们可以将创建项目这个API抽离出来放到项目根目录apis目录下，
API层不能使用test_*.yml命名，不支持单独运行，因为它只是用例的一个步骤，不能当成用例去执行。

API层：proj.yml
::
    name: 创建项目API描述
    request:
      url: /v3/project
      method: POST
      json:
        clusterId: "c-mj6ft"
        name: ${random_str()}
    response:
      - eq: [status_code, 201]

测试用例层：test_xx.yml
::
    name: 用例分层：api引用
    config:
      variables:
        clusterId: c-mj6ft
    steps:
      -
        name: 创建namespace
        # 引用创建project的API
        api: apis/proj.yml
        extract:
          proj_id: response.id
        request:
          url: /v3/clusters/${clusterId}/namespace
          method: POST
          json:
            clusterId: ${clusterId}
            projectId: ${proj_id}
            name: ${random_str()}
        validate:
          - eq: [status_code, 201]

8. 变量、函数和返回值的二次取值
>>>>>>>>>>>>>>>>>>>>>>>>>>>

例子1： 定义了一个变量name的值是"test123"，但是引用变量的时候只想取出前面四个字符串，于是可以用到引用变量语法
::
    $(name[:4])

例子2： extract获取到项目id的返回值为"c-mj6ft:p-6blkd"，但是引用id的时候只想取出':'后面的字符串，
于是可以使用split_str这个函数方法对字符串进行二次分割，返回值是一个列表，可以再次切片取出"p-6blkd"
::
    ${split_str(id, ':')[1]}

给一个具体的例子说明：
::
    name: 变量、返回值、函数的二次取值
    config:
      variables:
        name: ${random_str()}
    steps:
      -
        name: 创建项目
        request:
          url: /v3/project
          method: POST
          json:
            clusterId: "c-mj6ft"
            name: ${name[:4]}
        validate:
          - eq: [status_code, 201]
        extract:
          proj_id: $.id
      -
         name: 执行shell:检查后台是否存在项目的id
         exec:
           ssh_client: [10.74.60.2, 22, root, Sangfor-paas.237]
           shell: kubectl get project -A
         validate2:
           - eq: ['${split_str(proj_id, ":")[1]}', True]

9.扩展动作支持
>>>>>>>>>>>>>>>>>>>>>>>>

支持执行外部shell命令，进行后台检查，使用上跟API类似，具体使用如上面的例子所示，
注意，在exec扩展动作中返回值校验使用validate2关键字，返回值提取使用extract2关键字。
目前扩展动作还比较简单，许多校验项还不支持，待完善......

shell 校验项说明:
::
    name: shell检查请求示例
    config:
      variables:
        name: ${random_str()}
        ns_id: default
    steps:
      -
        name: 创建configmap
        request:
          url: /api/v1/namespaces/${ns_id}/configmaps
          method: post
          json:
            metadata:
              name: ${name}
            data:
              lyw: test-lyw
        validate:
          - eq: [ status_code, 201]
        extract:
          cm_name: $.metadata.name
      -
         name: 执行shell检查
         exec:
           ssh_client: [10.113.65.49, 22, root, Sangfor-paas.237]
           k8s_agent: True
           # shell: kubectl get cm -n default ${cm_name} -o jsonpath='{.data}'
           shell: kubectl get cm -n default | awk "NR>1{print \$1}"
           #shell: kubectl get cm -n default
         validate2:
           - eq: [$.lyw, test-lyw]
           # - contains: ["*", '${cm_name}']

extract和validate 支持以下几种取值语法对shell 返回值格式进行取值：
- jmespath 语法: response.key1.key2
- jsonpath 语法: $..key1
- re 正则语法: xx(.+?)xxx
- "*" 表示获取当前shell命令执行完成后的完整返回值

扩展功能支持
------------

当项目中有很多个接口的时候，一个个去转成 yaml 文件的用例会很浪费时间，提供接口的swagger.json 接口文档。
那么我们可以从swagger.json 中解析出接口，自动生成 yaml 格式的用例，节省工作量。
提供swagger_parser.py将API接口信息解析出来，并自动生成yaml格式的用例，swagger 参数可以是本地./swagger.json 文件
也可以直接从网络 http 获取。
::
    s = SwaggerToYaml("http://10.113.68.30/k8s-swagger.json")
    s.parse_json()


用例执行
------------
将代码下载到本地，通过 pip install 安装插件后，测试用例可以放在任意目录执行。
::
   pytest cases/  # 执行cases目录下的所有用例，不填写host和port信息，默认从pytest.ini中读取，推荐这种方式
   pytest cases/test_1.yml # 执行cases目录下的指定用例
   pytest --exclude BUG cases/ # 案例中可以打标签，可以排除打了BUG标签的用例不执行,多个标签可以逗号隔开
   pytest --incluce BVT cases/ # 只执行BVT案例，其中exclude和include可以同时使用，多个标签可以逗号隔开
   pytest --html=report.html cases/ # 生成html报告，需要安装Pytest-html 插件
   pytest --host=127.0.0.1 --port 443  cases/ # 执行用例时, 指定host和port，port默认为443


