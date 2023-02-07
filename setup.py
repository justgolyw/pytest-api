import os
import codecs
from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='pytest_api',
    version='1.0.0',
    author='liyangwei',
    author_email='2531222095@qq.com',
    maintainer='liyangwei',
    maintainer_email='2531222095@qq.com',
    license='BSD-3',
    url='',
    description='rest api test',
    long_description=read('README.rst'),
    packages=['pytest_api'],
    python_requires='>=3.8',
    install_requires=[
        'Jinja2==3.1.2',
        'jmespath==0.9.5',
        'jsonpath==0.82',
        'pytest==7.2.0',
        'PyYAML==6.0',
        'requests==2.28.1',
        'allure-pytest==2.12.0'
    ],
    classifiers=[
        'Framework :: Pytest',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python :: 3.8',
    ],
    entry_points={
        'pytest11': [
            'api = pytest_api.plugin',
        ],
    },
)
