import re
import operator
from ESS.parsing import parser

class BindError(Exception):
    def __init__(self, in_error):
        Exception.__init__(self)
        self.in_error = in_error

    def __str__(self):
        return self.in_error

class ValueEvaluatingError(BindError):
    pass
class NotNumericOperandError(BindError):
    pass


ARITHMETIC_OP_REX = re.compile(r'[\\+*/]|-(?!>)')
OPERATOR = { '+': operator.add,
             '-': operator.sub,
             '/': operator.truediv,
             '*': operator.mul }


def bind_rules(rules, facts):
    rules = rules.copy()
    while rules.unbinded:
        rule = rules.unbinded.pop()
        flag = True
        if rule.antecedent.is_binded():
            for conclusion in rule.consequent.conclusions:
                if not flag:
                    break
                if not conclusion.is_binded():
                    flag = False
                    for fact in facts:
                        new_rule = rule.copy()
                        var_name = conclusion.fact_name
                        _replace_same_varname(var_name, fact.name, new_rule)
                        rules.add(new_rule)
        else:
            for disjunction in rule.antecedent.disjunctions:
                if not flag:
                    break
                for condition in disjunction.conditions:
                    if not flag:
                        break
                    if not condition.is_binded():
                        flag = False
                        for fact in facts:
                            new_rule = rule.copy()

                            if '?' in condition.fact_name:
                                var_name = condition.fact_name
                            else:
                                var_name = re.findall(r'\?[\w_]+', condition.value)[0]

                            _replace_same_varname(var_name, fact.name, new_rule)
                            rules.add(new_rule)
    return rules


def _replace_same_varname(var_name, fact_name, rule):
    if not var_name.startswith('?'):
        raise ValueError('var_name: %s' % var_name)
    for disjunction in rule.antecedent.disjunctions:
        for condition in disjunction.conditions:
            if not condition.is_binded():
                if condition.fact_name == var_name:
                    condition.fact_name = fact_name
                if isinstance(condition.value, str) and '?' in condition.value:
                    condition.value = re.sub('\\'+var_name, fact_name, condition.value)
    for conclusion in rule.consequent.conclusions:
        if not conclusion.is_binded():
            if conclusion.fact_name == var_name:
                conclusion.fact_name = fact_name
            if len(conclusion.arg_list)==2:
                conclusion.arg_list[1] = re.sub('\\'+var_name, fact_name, conclusion.arg_list[1])


def evaluate_values(rule, facts):
    new_rule = rule.copy()

    for disjunction in new_rule.antecedent.disjunctions:
        for condition in disjunction.conditions:
            if not condition.is_evaluated():
                unevaluated = condition.value
                op_result = ARITHMETIC_OP_REX.findall(unevaluated)
                if op_result:
                    if len(op_result) > 1:
                        raise ValueEvaluatingError(str(condition))
                    op = OPERATOR[op_result[0]]
                    operands = ARITHMETIC_OP_REX.split(unevaluated)
                    a = _get_attribute(operands[0], facts)
                    b = _get_attribute(operands[1], facts)
                    if a is None or b is None:
                        value = "NIL"
                    else:
                        if not _is_number(a) or not _is_number(b):
                            raise NotNumericOperandError("%s%s%s" % (str(a), op_result[0], str(b)))
                        value = op(a, b)
                else:
                    value = _get_attribute(unevaluated, facts)
                condition.value = value

    for conclusion in new_rule.consequent.conclusions:
        if not conclusion.is_evaluated():
            unevaluated = conclusion.arg_list[1]
            op_result = ARITHMETIC_OP_REX.findall(unevaluated)
            if op_result:
                if len(op_result) > 1:
                    raise ValueEvaluatingError(str(conclusion))
                op = OPERATOR[op_result[0]]
                operands = ARITHMETIC_OP_REX.split(unevaluated)
                a = _get_attribute(operands[0], facts)
                b = _get_attribute(operands[1], facts)
                if a is None or b is None:
                    value = "NIL"
                else:
                    if not _is_number(a) or not _is_number(b):
                        raise NotNumericOperandError("%s%s%s" % (str(a), op_result[0], str(b)))
                    value = op(a, b)
            else:
                value = _get_attribute(unevaluated, facts)
            conclusion.arg_list[1] = value

    return new_rule


def _is_number(v):
    if isinstance(v, int):
        return True
    if isinstance(v, float):
        return True
    return False


def _get_attribute(slice, facts):
    if '->' not in slice:
        v = parser.cast_trial(slice)
        return v
    try:
        fact_name, attr = slice.split('->')
    except:
        raise ValueEvaluatingError(str(slice))
    fact = facts[fact_name]
    v = fact[attr]
    if isinstance(v, str):
        v = parser.cast_trial(v)
    return v