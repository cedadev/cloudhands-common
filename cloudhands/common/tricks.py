#!/usr/bin/env python3
#   encoding: UTF-8

__doc__ = """
Helper functions and factories.
"""

#_FSMP = namedtuple("FSMParameters", ["table", "states"])
#
#def state_init(class_, params):
#    return class_(fsm=params.table, name=params.states[0])
#
#
#def fsm_factory(name, states):
#    className = name.capitalize() + "State"
#    attribs = dict(__mapper_args__={"polymorphic_identity": name})
#    class_ = type(className, (State,), attribs)
#    return (_FSMP(name, states), class_)
