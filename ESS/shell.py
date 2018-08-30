import inspect
from os import path
import time
from ESS.parsing.parser import Parser, ParserSyntaxError
from ESS.engine import WorkingMemory, Engine, EngineError
from ESS.container import FactContainer, RuleContainer, GoalContainer, NotExistentItemError

VERSION = "0.21 alpha"
MAXDEPTH_DEFAULT = 1000


class CommandError(Exception):
    def __init__(self, cause=''):
        Exception.__init__(self)
        self.cause = cause

    def __str__(self):
        return self.cause

class BadArgumentsError(CommandError):
    def __str__(self):
        if self.cause:
            return "Bad arguments error: %s" % self.cause
        return "Bad arguments error"

class NothingToDo(Exception):
    pass


class Shell(object):

    def __init__(self):
        self.parser = Parser()
        self.engine = Engine()
        self.handlers = self._get_handlers()
        self.w_memory = None

    def start(self):
        if not self.w_memory:
            self.w_memory = WorkingMemory(FactContainer(), RuleContainer(), GoalContainer())
        print "ESS - Expert System Shell v. %s" % VERSION
        input = None
        while True:
            try:
                input = raw_input('ESS >> ')
            except ((KeyboardInterrupt, EOFError), EOFError):
                self._handler_quit()
            print

            splitted_input = input.split()
            command, params = splitted_input[0], splitted_input[1:]

            callable = self.handlers.get('_handler_'+command, self._handler_unrecognized)
            compulsory_arg_n = \
                    len(inspect.getargspec(callable).args) - len(inspect.getargspec(callable).defaults or ()) - 1
            try:
                if callable != self._handler_unrecognized and \
                        len(params) < compulsory_arg_n:
                    raise BadArgumentsError()
                callable(*params)
            except (EOFError, KeyboardInterrupt):
                self._handler_quit()
            except (NothingToDo, SyntaxError):
                print "Nothing to do."
            except CommandError as cmd_error:
                print cmd_error
                print '\nCorrect usage is:\n' + inspect.getdoc(callable)
            except ParserSyntaxError as parser_error:
                print parser_error
            except EngineError as ng_error:
                print ng_error
            print

    def load_from_file(self, filepath):
        try:
            self._handler_load(filepath)
        except CommandError as e:
            print e

    def _get_handlers(self):
        return dict(function for function in inspect.getmembers(self, inspect.ismethod)
                        if function[0].startswith('_handler'))

    def _handler_help(self, *args):
        """help - print this usage"""
        usages = []
        handler_names = [name for name in self.handlers.keys() if name != '_handler_unrecognized']
        handler_names.sort()
        for name in handler_names:
            doc = '\n\t\t'.join((inspect.getdoc(self.handlers[name] or '')).splitlines())
            usages.append('\t'+doc)
        print "Available commands are:\n%s" % '\n'.join(usages)


    def _handler_unrecognized(self, *args):
        print "Unrecognized command.\nTyping 'help' could be useful for you.."

    def _handler_quit(self, *args):
        """quit - exit interactive shell"""
        time.sleep(0.01)
        try:
            print 'Have a good day :)'
        except Exception:
            pass
        finally:
            exit(0)

    def _handler_def_facts(self, *args):
        """def_facts - assert new world fact(s)"""
        print "Enter one or more facts, blank line when done\n\nESS (assert facts) >> "
        lines = []
        while True:
            try:
                line = raw_input('ESS >> ')
            except (KeyboardInterrupt, EOFError):
                self._handler_quit()
            if lines:
                if not lines[-1] and not line:
                    break
            else:
                if not line:
                    break
            lines.append(line)
        lines = self.parser.purify(lines)
        try:
            facts_parsed = self.parser.parse_facts(lines)
        except ParserSyntaxError:
            raise CommandError('Syntax error')
        if not facts_parsed:
            raise NothingToDo()
        self.w_memory.initial_state.update(facts_parsed)

    def _handler_del_fact(self, factname=None, *args):
        """del_fact [FACTNAME] - retract a fact"""
        if not self.w_memory.initial_state:
            raise NothingToDo()
        if not factname:
            try:
                factname = raw_input("Enter fact name to retract: ")
            except (KeyboardInterrupt, EOFError):
                self._handler_quit()
        if not factname:
            raise NothingToDo()
        try:
            self.w_memory.initial_state.remove(factname)
        except NotExistentItemError:
            raise CommandError('factname not found')
        print "%s retracted" % factname

    def _handler_def_rule(self, *args):
        """def_rule - define new rule(s)"""
        print "Enter one or more rules, blank line when done\n\nESS (assert rules) >> "
        lines = []
        while True:
            try:
                line = raw_input('ESS >> ')
            except (KeyboardInterrupt, EOFError):
                self._handler_quit()
            if lines:
                if not lines[-1] and not line:
                    break
            else:
                if not line:
                    break
            lines.append(line)
        lines = self.parser.purify(lines)
        rules_parsed = self.parser.parse_rules(lines)
        if not rules_parsed:
            raise NothingToDo()
        self.w_memory.rules.update(rules_parsed)

    def _handler_del_rule(self, rule_name=None, *args):
        """del_rule [RULENAME] - delete an existing rule"""
        if not self.w_memory.rules:
            raise NothingToDo()
        if not rule_name:
            try:
                rule_name = raw_input('Enter rule name to remove: ')
            except (KeyboardInterrupt, EOFError):
                self._handler_quit()
        if not rule_name:
            raise NothingToDo()
        try:
            self.w_memory.rules.remove(rule_name)
        except NotExistentItemError:
            raise CommandError('Rule not found')
        print 'Done'

    def _handler_facts(self, *args):
        """facts - print the entire facts list"""
        print self.w_memory.initial_state

    def _handler_rules(self, *args):
        """rules - print the entire rules list"""
        print self.w_memory.rules

    def _handler_clear_facts(self, *args):
        """clear_facts - clear the facts list"""
        if not self.w_memory.initial_state:
            raise NothingToDo()
        self.w_memory.initial_state.clear()
        print "Facts cleared"

    def _handler_clear_rules(self, *args):
        """clear_rules - clear the rules list"""
        if not self.w_memory.rules:
            raise NothingToDo()
        self.w_memory.rules.clear()
        print "Rules cleared"

    def _handler_run_AStar(self, h_name, h_attrs=None, max_depth=None, *args):
        """run_AStar {HAMMINGDISTANCE|(LINEARCONFLICT|MANHATTANDISTANCE) content,x,y} [MAX_DEPTH]
        Example (gioco_otto): run_AStar MANHATTANDISTANCE contenuto,riga,colonna
        Example (gioco_otto): run_AStar LINEARCONFLICT contenuto,riga,colonna
        Example (gioco_otto): run_AStar HAMMINGDISTANCE"""
        if not self.w_memory.initial_state or not self.w_memory.rules or not self.w_memory.goal:
            raise NothingToDo()
        if not max_depth:
            max_depth = MAXDEPTH_DEFAULT
        else:
            try:
                max_depth = int(max_depth)
            except ValueError:
                raise CommandError("Max rules to apply must be an integer")

        if h_name == 'HAMMINGDISTANCE':
            h_fun = Engine.h_hamming_distance
            if h_attrs is not None:
                raise BadArgumentsError()
        elif h_name == 'MANHATTANDISTANCE':
            h_fun = Engine.h_manhattan_distance
        elif h_name == 'LINEARCONFLICT':
            h_fun = Engine.h_linear_conflict
        else:
            raise BadArgumentsError('Unknown heuristic function')

        if h_name in ('MANHATTANDISTANCE', 'LINEARCONFLICT'):
            try:
                h_attrs = h_attrs.split(',')
                if len(h_attrs) != 3:
                    raise'LINEARCONFLICT'
            except:
                raise BadArgumentsError('Wrong heuristic attributes')

        self.engine.run(self.w_memory, Engine.a_star_search, max_depth, h_fun, h_attrs)


    def _handler_run_BestFirst(self, h_name, h_attrs=None, max_depth=None, *args):
        """run_BestFirst {HAMMINGDISTANCE|(LINEARCONFLICT|MANHATTANDISTANCE) content,x,y} [MAX_DEPTH]"""
        if not self.w_memory.initial_state or not self.w_memory.rules or not self.w_memory.goal:
            raise NothingToDo()
        if not max_depth:
            max_depth = MAXDEPTH_DEFAULT
        else:
            try:
                max_depth = int(max_depth)
            except ValueError:
                raise CommandError("Max rules to apply must be an integer")

        if h_name == 'HAMMINGDISTANCE':
            h_fun = Engine.h_hamming_distance
            if h_attrs is not None:
                raise BadArgumentsError()
        elif h_name == 'MANHATTANDISTANCE':
            h_fun = Engine.h_manhattan_distance
        elif h_name == 'LINEARCONFLICT':
            h_fun = Engine.h_linear_conflict
        else:
            raise BadArgumentsError('Unknown heuristic function')

        if h_name in ('MANHATTANDISTANCE', 'LINEARCONFLICT'):
            try:
                h_attrs = h_attrs.split(',')
                if len(h_attrs) != 3:
                    raise'LINEARCONFLICT'
            except:
                raise BadArgumentsError('Wrong heuristic attributes')
        self.engine.run(self.w_memory, Engine.best_first_search, max_depth, h_fun, h_attrs)

    def _handler_run_DFS(self, max_depth=None, *args):
        """run_DFS [MAX_DEPTH]"""
        if not self.w_memory.initial_state or not self.w_memory.rules or not self.w_memory.goal:
            raise NothingToDo()
        if not max_depth:
            max_depth = MAXDEPTH_DEFAULT
        else:
            try:
                max_depth = int(max_depth)
            except ValueError:
                raise CommandError("Max rules to apply must be an integer")
        self.engine.run(self.w_memory, Engine.depth_first_search, max_depth)

    def _handler_run_BFS(self, max_depth=None, *args):
        """run_BFS [MAX_DEPTH]"""
        if not self.w_memory.initial_state or not self.w_memory.rules or not self.w_memory.goal:
            raise NothingToDo()
        if not max_depth:
            max_depth = MAXDEPTH_DEFAULT
        else:
            try:
                max_depth = int(max_depth)
            except ValueError:
                raise CommandError("Max rules to apply must be an integer")
        self.engine.run(self.w_memory, Engine.breadth_first_search, max_depth)

    def _handler_load(self, filepath, *args):
        """load FILEPATH - load the knowledge base (facts, rules, goal) from a file"""
        filepath = path.normpath(filepath)
        try:
            with open(filepath) as f:
                file_content = f.read()
        except IOError:
            raise CommandError("File path given doesn't exist")
        facts, rules, goal = self.parser.load_from_text(file_content)
        self.w_memory = WorkingMemory(facts, rules, goal)
        print "\nFile %s loaded succesfully\n" % filepath

    def _handler_def_goal(self, *args):
        """def_goal - set the goal"""
        print "Enter the goal, blank line when done\n\nESS (set goal) >> "
        lines = []
        while True:
            try:
                line = raw_input('ESS >> ')
            except (KeyboardInterrupt, EOFError):
                self._handler_quit()
            if lines:
                if not lines[-1] and not line:
                    break
            else:
                if not line:
                    break
            lines.append(line)
        lines = self.parser.purify(lines)
        goal = self.parser.parse_goal(lines)
        if not goal:
            raise NothingToDo()
        self.w_memory.goal.update(goal)

    def _handler_del_goal(self, *args):
        """del_goal - unset the goal"""
        if not self.w_memory.goal:
            raise NothingToDo()
        self.w_memory.goal.clear()
        print "Goal cleared"

    def _handler_goal(self, *args):
        """goal - print the goal"""
        print self.w_memory.goal