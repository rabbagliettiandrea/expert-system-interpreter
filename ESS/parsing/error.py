class ParserSyntaxError(Exception):
    def __init__(self, in_error):
        Exception.__init__(self)
        self.in_error = in_error

    def __str__(self):
        return "%s: %s" % (type(self).__name__, self.in_error)

class FactSyntaxError(ParserSyntaxError):
    pass
class RuleSyntaxError(ParserSyntaxError):
    pass
class BadArgumentsError(RuleSyntaxError):
    pass
class UnnamedFactError(FactSyntaxError):
    pass
class UnnamedRuleError(FactSyntaxError):
    pass
class UnexpectedBeginFactError(FactSyntaxError):
    pass
class UnexpectedEndFactError(FactSyntaxError):
    pass
class UnexpectedAntecedentEndError(RuleSyntaxError):
    pass
class UnexpectedConsequentEndError(RuleSyntaxError):
    pass
class AttributeParsingError(ParserSyntaxError):
    pass
class ValueParsingError(ParserSyntaxError):
    pass
class EmptyAntecedentError(RuleSyntaxError):
    pass
class EmptyConsequentError(RuleSyntaxError):
    pass
class UnexpectedBeginGoalError(FactSyntaxError):
    pass