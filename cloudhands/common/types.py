#!/usr/bin/env python3
# encoding: UTF-8


def name(self, name):
    """
    This generative one-shot method allows you to define and name an
    object in a single statement.
    """
    self.name = name
    return self

NamedDict = type("NamedDict", (dict,), {"name": name})
NamedList = type("NamedList", (list,), {"name": name})
