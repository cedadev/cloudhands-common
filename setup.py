#!/usr/bin/env python
# encoding: UTF-8

import ast
from setuptools import setup
import os.path


try:
    import cloudhands.common.__version__ as version
except ImportError:
    # Pip evals this file prior to running setup.
    # This causes ImportError in a fresh virtualenv.
    version = str(ast.literal_eval(
                open(os.path.join(os.path.dirname(__file__),
                "cloudhands", "common", "__init__.py"),
                'r').read().split("=")[-1].strip()))

__doc__ = open(os.path.join(os.path.dirname(__file__), "README.rst"),
               "r").read()

setup(
    name="cloudhands-common",
    version=version,
    description="Common definitions for cloudhands PaaS",
    author="D Haynes",
    author_email="david.e.haynes@stfc.ac.uk",
    url="http://pypi.python.org/pypi/cloudhands-common",
    long_description=__doc__,
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License"
    ],
    namespace_packages=["cloudhands"],
    packages=["cloudhands.common", "cloudhands.common.test"],
    package_data={
        "cloudhands.common": [],
        "cloudhands.common.test": [],
    },
    install_requires=[
        "SQLAlchemy>=0.8.3",
    ],
    entry_points={
        "console_scripts": [
        ],
        "jasmin.component.fsm": [
            "appliance = cloudhands.common.fsm:ApplianceState",
            "host = cloudhands.common.fsm:HostState",
            "membership = cloudhands.common.fsm:MembershipState",
            "registration = cloudhands.common.fsm:RegistrationState",
            "subscription = cloudhands.common.fsm:SubscriptionState",
        ],
    },
    zip_safe=False
)
