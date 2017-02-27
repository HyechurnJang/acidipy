import os
from setuptools import setup

def read(fname): return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='acidipy',
    version='0.10.6',
    license='Apache 2.0',
    author='Hyechurn Jang',
    author_email='hyjang@cisco.com',
    url='https://github.com/HyechurnJang/acidipy',
    description='ACI Developing Interface for PYthon',
    long_description=read('README'),
    packages=['acidipy'],
    classifiers=[
      'Development Status :: 4 - Beta',
      'License :: OSI Approved :: Apache Software License',
      'Intended Audience :: Developers',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.7',
      'Topic :: Software Development :: Libraries :: Python Modules',
      'Operating System :: POSIX',
      'Operating System :: POSIX :: Linux',
      'Operating System :: MacOS',
      'Operating System :: MacOS :: MacOS X',
    ],
    install_requires=['pyaml', 'requests', 'websocket-client']
)
