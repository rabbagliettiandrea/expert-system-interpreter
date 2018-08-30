import inspect
from ESS.parsing.error import *
from ESS import entity, container, operation
from ESS.parsing import regex


def cast_trial(slice):
    if slice == 'NIL':
        return 'NIL'
    slice_matched = regex.STRING_CHECK.match(slice)
    if slice_matched and slice_matched.group() == slice:
        return slice.strip('"')
    if slice.capitalize() in 'True':
        return True
    if slice.capitalize() == 'False':
        return False
    if slice.isdigit():
        return int(slice)
    try:
        return float(slice)
    except ValueError:
        pass
    return slice


class Parser(object):

    COMMENT = '#'
    UNKNOWN, FACT, GOAL, ANTECEDENT, CONSEQUENT = range(5)

    def __init__(self):
        self._status = self.UNKNOWN

    def load_from_text(self, text):
        lines = self.purify(text.splitlines())
        return self.parse_facts(lines), self.parse_rules(lines), self.parse_goal(lines)

    def purify(self, lines):
        purifieds = []
        for line in lines:
            if line:
                line = line.strip()
                if not line.startswith(self.COMMENT):
                    search_res = regex.STRING_CHECK.search(line)
                    if search_res:
                        i, j = search_res.span()
                        head = line[:i].replace(' ', '')
                        body = line[i:j]
                        tail = line[j:].replace(' ', '')
                        line = head + body + tail
                    else:
                        line = line.replace(' ', '')
                    side_comment_index = line.find(self.COMMENT)
                    if side_comment_index != -1:
                        line = line[:side_comment_index]
                    purifieds.append(line)
        return purifieds

    def parse_facts(self, lines):
        facts = container.FactContainer()
        for line in lines:

            if self._status == self.GOAL:
                if line.startswith('endGoal'):
                    self._status = self.UNKNOWN
                continue

            if self._status == self.UNKNOWN:
                if line.startswith('beginGoal:'):
                    self._status = self.GOAL
                    continue
                if line.startswith('beginFact:'):
                    self._status = self.FACT
                    current_fact_name = line.split(':', 1)[1]
                    if not current_fact_name:
                        raise UnnamedFactError(line)
                    current_fact = entity.Fact(current_fact_name)
                    facts.add(current_fact)
                    continue
                if line.startswith('endFact'):
                    raise UnexpectedEndFactError(line)
                continue

            if self._status == self.FACT:
                if line.startswith('beginFact:'):
                    raise UnexpectedBeginFactError(line)
                if line.startswith('endFact'):
                    self._status = self.UNKNOWN
                    continue
                try:
                    k, v = [token.strip() for token in line.split('=', 1)]
                except:
                    raise FactSyntaxError(line)
                if not (k and v):
                    raise AttributeParsingError(line)
                v = cast_trial(v)
                current_fact[k] = v

        return facts

    def parse_rules(self, lines):
        rules = container.RuleContainer()
        for line in lines:

            if self._status == self.GOAL:
                if line.startswith('endGoal'):
                    self._status = self.UNKNOWN
                continue

            if self._status == self.UNKNOWN:
                if line.startswith('beginGoal:'):
                    self._status = self.GOAL
                    continue
                if line.startswith('beginRule:'):
                    self._status = self.ANTECEDENT
                    current_rule_name = line.split(':', 1)[1]
                    if not current_rule_name:
                        raise UnnamedRuleError(line)
                    antecedent = entity.Antecedent()
                    continue
                if line == 'then':
                    raise UnexpectedAntecedentEndError(line)
                if line == 'endRule':
                    raise UnexpectedConsequentEndError(line)
                continue

            if self._status == self.ANTECEDENT:
                if line == 'then':
                    if not antecedent.disjunctions:
                        raise EmptyAntecedentError(line)
                    self._status = self.CONSEQUENT
                    consequent = entity.Consequent()
                    continue
                antecedent.disjunctions.append(self._parse_disjunction(line))
                continue

            if self._status == self.CONSEQUENT:
                if line == 'endRule':
                    if not consequent.conclusions:
                        raise EmptyConsequentError(line)
                    rule = entity.Rule(current_rule_name, antecedent, consequent)
                    rules.add(rule)
                    self._status = self.UNKNOWN
                    continue
                consequent.conclusions.append(self._parse_conclusion(line))

        return rules

    def parse_goal(self, lines):
        goal_lines = []
        goal_facts = None
        goal = container.GoalContainer()
        for line in lines:

            if self._status == self.UNKNOWN:
                if line.startswith('beginGoal:'):
                    if goal_facts:
                        raise UnexpectedBeginGoalError(line)
                    self._status = self.GOAL
                continue

            if self._status == self.GOAL:
                if line.startswith('endGoal'):
                    self._status = self.UNKNOWN
                    goal_facts = self.parse_facts(goal_lines)
                    continue
                goal_lines.append(line)
        if goal_facts:
            goal.update(goal_facts)
        return goal

    def _parse_condition(self, line):
        matched = regex.CONDITION_CHECK.match(line)
        if not matched or matched.group() != line:
            raise RuleSyntaxError(line)
        predicate_name, arg_list = line[:-1].split('(')
        predicate = getattr(operation, 'pred_' + predicate_name)
        fact_name, attr, value = arg_list.split(',')
        value = cast_trial(value)
        return entity.Condition(predicate, fact_name, attr, value)

    def _parse_conclusion(self, line):
        action_matched = regex.ACTION_CHECK.match(line)
        if not action_matched or action_matched.group() != line:
            raise RuleSyntaxError(line)
        action_name, tail = line[:-1].split('(')
        arg_list = [parsed_arg for parsed_arg in tail.split(',') if parsed_arg]
        action = getattr(operation, 'actn_' + action_name)
        fun_arg_list = inspect.getargs(action.func_code).args[1:]
        if len(arg_list) != len(fun_arg_list):
            raise BadArgumentsError(line)
        fact_name = arg_list.pop(0)
        return entity.Conclusion(action, fact_name, *arg_list)

    def _parse_disjunction(self, line):
        conditions = []
        for condition_str in line.split('||'):
            conditions.append(self._parse_condition(condition_str))
        return entity.Disjunction(conditions)