import copy
import re

ARITHMETIC_OP_REX = re.compile(r'[\\+*-/]')


class Rule(object):

    def __init__(self, name, antecedent, consequent):
        self.name = name
        self.antecedent = antecedent
        self.consequent = consequent

    def __str__(self):
        return "[Rule: %s]\nAntecedent:\n%s\nConsequent:\n%s" % (self.name, self.antecedent, self.consequent)

    def __hash__(self):
        return hash((self.antecedent, self.consequent, self.name))

    def __eq__(self, other):
        b = self.name == other.name and \
                self.antecedent == other.antecedent and \
                    self.consequent == other.antecedent
        return b

    def __deepcopy__(self, memo):
        new_antecedent = copy.deepcopy(self.antecedent, memo)
        new_consequent = copy.deepcopy(self.consequent, memo)
        new_rule = Rule(self.name, new_antecedent, new_consequent)
        memo[id(self)] = new_rule
        return new_rule

    def copy(self):
        return copy.deepcopy(self)

    def is_binded(self):
        return self.antecedent.is_binded() and self.consequent.is_binded()

    def is_evaluated(self):
        return self.antecedent.is_evaluated() and self.consequent.is_evaluated()


class Antecedent(object):

    def __init__(self, disjunctions=None):
        self.disjunctions = disjunctions or []

    def __str__(self):
        l = []
        for disj in self.disjunctions:
            line = str(disj)
            if self.disjunctions[-1] != disj:
                line += ' &&'
            l.append(line)
        return '\n'.join(l)

    def __call__(self, facts):
        b = True
        for disj in self.disjunctions:
            b = disj(facts)
            if not b:
                break
        return b

    def __hash__(self):
        return hash(frozenset(self.disjunctions))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __deepcopy__(self, memo):
        new_disjunctions = []
        for disjunction in self.disjunctions:
            new_disjunctions.append(copy.deepcopy(disjunction, memo))
        new_antecedent = Antecedent(new_disjunctions)
        memo[id(self)] = new_antecedent
        return new_antecedent

    def copy(self):
        return copy.deepcopy(self)

    def is_binded(self):
        for disjunction in self.disjunctions:
            if not disjunction.is_binded():
                return False
        return True

    def is_evaluated(self):
        for disjunction in self.disjunctions:
            if not disjunction.is_evaluated():
                return False
        return True


class Disjunction(object):

    def __init__(self, conditions=None):
        self.conditions = conditions or []

    def __str__(self):
        l = [str(condition) for condition in self.conditions]
        return ' || '.join(l)

    def __call__(self, facts):
        b = False
        for cond in self.conditions:
            b = bool(cond(facts))
            if b:
                break
        return b

    def __hash__(self):
        return hash(frozenset(self.conditions))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __deepcopy__(self, memo):
        new_conditions = []
        for condition in self.conditions:
            new_conditions.append(copy.deepcopy(condition))
        new_disjunction = Disjunction(new_conditions)
        memo[id(self)] = new_disjunction
        return new_disjunction

    def copy(self):
        return copy.deepcopy(self)

    def is_binded(self):
        for condition in self.conditions:
            if not condition.is_binded():
                return False
        return True

    def is_evaluated(self):
        for condition in self.conditions:
            if not condition.is_evaluated():
                return False
        return True


class Consequent(object):

    def __init__(self, conclusions=None):
        self.conclusions = conclusions or []

    def __str__(self):
        return '\n'.join([str(conclusion) for conclusion in self.conclusions])

    def __call__(self, facts):
        new_facts = facts.copy()
        for conclusion in self.conclusions:
            conclusion(new_facts)
        return new_facts

    def __hash__(self):
        return hash(frozenset(self.conclusions))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __deepcopy__(self, memo):
        new_conclusions = []
        for conclusion in self.conclusions:
            new_conclusions.append(copy.deepcopy(conclusion))
        new_consequent = Consequent(new_conclusions)
        memo[id(self)] = new_consequent
        return new_consequent

    def copy(self):
        return copy.deepcopy(self)

    def is_binded(self):
        for conclusion in self.conclusions:
            if not conclusion.is_binded():
                return False
        return True

    def is_evaluated(self):
        for conclusion in self.conclusions:
            if not conclusion.is_evaluated():
                return False
        return True


class Conclusion(object):

    def __init__(self, action, fact_name, *arg_list):
        self.action = action
        self.fact_name = fact_name
        self.arg_list = list(arg_list)

    def __str__(self):
        action_name = re.sub('actn_', '', self.action.func_name)
        if not self.arg_list:
            return "%s(%s)" % (action_name, self.fact_name)
        l = ['%s(%s, ' % (action_name, self.fact_name)]
        for arg in self.arg_list[:-1]:
            l.append('%s, ' % arg)
        l.append('%s)' % self.arg_list[-1])
        return ''.join(l)

    def __call__(self, facts):
        self.action(facts, self.fact_name, *self.arg_list)

    def __hash__(self):
        return hash((self.action, self.fact_name, frozenset(self.arg_list)))

    def __eq__(self, other):
        b = self.action == other.action and \
                self.fact_name == other.fact_name and \
                    self.arg_list == other.arg_list
        return b

    def __deepcopy__(self, memo):
        new_conclusion = Conclusion(self.action, self.fact_name, *self.arg_list[:])
        memo[id(self)] = new_conclusion
        return new_conclusion

    def copy(self):
        return copy.deepcopy(self)

    def is_binded(self):
        if len(self.arg_list) == 2:
            value = self.arg_list[1]
            if isinstance(value, str) and value.startswith('?'):
                return False
        return not self.fact_name.startswith('?')

    def is_evaluated(self):
        if len(self.arg_list) == 2:
            value = self.arg_list[1]
            if isinstance(value, str):
                if '->' in value or ARITHMETIC_OP_REX.findall(value):
                    return False
        return True


class Condition(object):

    def __init__(self, predicate, fact_name, test_attr, value):
        self.predicate = predicate
        self.fact_name = fact_name
        self.test_attr = test_attr
        self.value = value

    def __str__(self):
        pred_name = re.sub('pred_', '', self.predicate.func_name)
        return '%s(%s, %s, %s)' % (pred_name, self.fact_name, self.test_attr, self.value)

    def __call__(self, facts):
        return self.predicate(facts, self.fact_name, self.test_attr, self.value)

    def __hash__(self):
        return hash((self.predicate, self.fact_name, self.test_attr, self.value))

    def __eq__(self, other):
        b = self.predicate == other.predicate and \
                self.fact_name == other.fact_name and \
                    self.test_attr == other.test_attr and \
                        self.value == other.value
        return b

    def __deepcopy__(self, memo):
        new_condition = Condition(self.predicate, self.fact_name, self.test_attr, self.value)
        memo[id(self)] = new_condition
        return new_condition

    def copy(self):
        return copy.deepcopy(self)

    def is_binded(self):
        if isinstance(self.value, str) and self.value.startswith('?'):
            return False
        return not self.fact_name.startswith('?')

    def is_evaluated(self):
        if isinstance(self.value, str):
            if '->' in self.value or ARITHMETIC_OP_REX.findall(self.value):
                return False
        return True


class Fact(object):

    def __init__(self, name):
        self.name = name
        self._attrs = {}

    def __getitem__(self, attr):
        return self._attrs.get(attr, None)

    def __setitem__(self, attr, value):
        self._attrs[attr] = value

    def __delitem__(self, attr):
        del self._attrs[attr]

    def __contains__(self, attr):
        return attr in self._attrs

    def __str__(self):
        return self.name + str(self._attrs)

    def __hash__(self):
        return hash( (self.name, frozenset(self._attrs.items())) )

    def __eq__(self, other):
        name_check = self.name == other.name
        return name_check and self._attrs == other._attrs

    def __ne__(self, other):
        return not self.__eq__(other)

    def __deepcopy__(self, memo):
        new_fact = Fact(self.name)
        new_fact._attrs = self._attrs.copy()
        memo[id(self)] = new_fact
        return new_fact