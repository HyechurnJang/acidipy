import os
from setuptools import setup

def read(fname): return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='acidipy',
    version='0.9.5',
    license='Apache2.0',
    author='Hyechurn Jang',
    author_email='hyjang@cisco.com',
    url='https://github.com/HyechurnJang/acidipy',
    description='Acidipy',
    long_description=read('README'),
    packages=['acidipy'],
    install_requires=['pyaml', 'requests', 'websocket-client']
)
