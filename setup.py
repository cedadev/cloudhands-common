#!/usr/bin/env python
# encoding: UTF-8

from setuptools import setup
import os.path

import cloudhands.ops

__doc__ = open(os.path.join(os.path.dirname(__file__), "README.rst"),
               "r").read()

setup(
    name="cloudhands-ops",
    version=cloudhands.ops.__version__,
    description="Operations for cloudhands PaaS",
    author="D Haynes",
    author_email="david.e.haynes@stfc.ac.uk",
    url="http://pypi.python.org/pypi/cloudhands-ops",
    long_description=__doc__,
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License"
    ],
    namespace_packages=["cloudhands"],
    packages=["cloudhands.ops"],
    package_data={"cloudhands.ops": [
                    "doc/*.rst",
                    "doc/_templates/*.css",
                    "doc/html/*.html",
                    "doc/html/*.js",
                    "doc/html/_sources/*",
                    "doc/html/_static/*",
                    ]},
    install_requires=[],
    entry_points={
        "console_scripts": [
        ],
    },
    zip_safe=False
)
