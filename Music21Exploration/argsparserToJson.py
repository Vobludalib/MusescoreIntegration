import argparse
import json

def argsparser_to_json(parser):
    flags = {}

    for action in parser._actions:
        flag_name = action.dest
        flag_type = type(action.default).__name__ if action.default is not None else 'None'
        flags[flag_name] = flag_type

    return json.dumps(flags, indent=4)

def get_argument_types(parser):
    types = {}

    for action in parser._actions:
        if action.type is not None:
            types[action.dest] = action.type.__name__

    return types