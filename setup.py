# from distutils.core import setup
from setuptools import setup

setup(
    name='acidipy',
    version='0.9.5',
#     package_dir={'' : 'acidipy'},
    packages=['acidipy'],
    install_requires=['pyaml', 'requests', 'websocket-client'],
    author='Hyechurn Jang',
    author_email='hyjang@cisco.com',
    url='https://github.com/HyechurnJang/acidipy',
    description='Acidipy'
)
