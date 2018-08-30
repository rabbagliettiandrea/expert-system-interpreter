import inspect
import re
from ESS import operation


def _get_actions_names():
    return [fun_name[5:] for fun_name in _get_fun_name_list() if fun_name.startswith('actn_')]

def _get_predicates_names():
    return [fun_name[5:] for fun_name in _get_fun_name_list() if fun_name.startswith('pred_')]

def _get_fun_name_list():
    return [function[0] for function in inspect.getmembers(operation, inspect.isfunction)
                 if function[0].startswith('actn') or function[0].startswith('pred')]


CONDITION_CHECK = re.compile(r'(%s)\([?\w_]+,[\w_]+,(NIL|"[^"]*"|[\d.]+|(\?[\w_.]+->[\*+-/\w_.]+))+\)' %
                                 '|'.join(_get_predicates_names()))
ACTION_CHECK = re.compile(r'(%s)\([?\w_]+(,[\w_]+(,(NIL|"[^"]*"|[\d.]+|(\?[\w_.]+->[\*+-/\w_.]+)))?)?\)' %
                              '|'.join(_get_actions_names()))
STRING_CHECK = re.compile(r'"[^"]*"')