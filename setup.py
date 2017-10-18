import os
from setuptools import setup

def read(fname): return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='acidipy',
    version='0.12.0',
    license='Apache 2.0',
    author='Hyechurn Jang',
    author_email='hyjang@cisco.com',
    url='https://github.com/HyechurnJang/acidipy',
    description='Cisco ACI Developing Interface for PYthon',
    long_description=read('README'),
    packages=['acidipy'],
    install_requires=['gevent', 'pygics', 'pyaml', 'requests', 'websocket-client'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ]
)
