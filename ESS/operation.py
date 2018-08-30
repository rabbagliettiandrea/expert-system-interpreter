from ESS import entity

class OperationError(Exception):
    def __init__(self, cause):
        Exception.__init__(self)
        self.cause = cause

    def __str__(self):
        return self.cause

class AttrError(OperationError):
    pass


def pred_equal(facts, fact_name, test_attr, value):
    fact = facts[fact_name]
    try:
        return fact[test_attr] == value
    except KeyError:
        return False

def pred_not_equal(facts, fact_name, test_attr, value):
    return not pred_equal(facts, fact_name, test_attr, value)

def pred_greater_than(facts, fact_name, test_attr, value):
    fact = facts[fact_name]
    try:
        return fact[test_attr] > value
    except KeyError:
        return False

def pred_less_than(facts, fact_name, test_attr, value):
    fact = facts[fact_name]
    try:
        return fact[test_attr] < value
    except KeyError:
        return False

def pred_greater_equal_than(facts, fact_name, test_attr, value):
    fact = facts[fact_name]
    try:
        return fact[test_attr] >= value
    except KeyError:
        return False

def pred_less_equal_than(facts, fact_name, test_attr, value):
    fact = facts[fact_name]
    try:
        return fact[test_attr] <= value
    except KeyError:
        return False

def actn_assert(facts, fact_name):
    fact = entity.Fact(fact_name)
    facts.add(fact)

def actn_retract(facts, fact_name):
    facts.remove(fact_name)

def actn_add(facts, fact_name, attr, value):
    fact = facts[fact_name]
    if attr in fact:
        raise AttrError(str(attr))
    fact[attr] = value

def actn_update(facts, fact_name, attr, value):
    fact = facts[fact_name]
    if attr not in fact:
        raise AttrError(str(attr))
    fact[attr] = value

def actn_remove(facts, fact_name, attr):
    fact = facts[fact_name]
    if attr not in fact:
        raise AttrError(str(attr))
    del fact[attr]