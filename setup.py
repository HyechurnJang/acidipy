import os
from setuptools import setup

def read(fname): return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='acidipy',
    version='0.10.0',
    license='Apache 2.0',
    author='Hyechurn Jang',
    author_email='hyjang@cisco.com',
    url='https://github.com/HyechurnJang/acidipy',
    description='ACI Developing Interface for PYthon',
    long_description=read('README'),
    packages=['acidipy'],
    install_requires=['pyaml', 'requests', 'websocket-client']
)
