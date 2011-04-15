# coding=UTF-8

from pyparsing import Literal, OneOrMore, ZeroOrMore, Regex, MatchFirst
from pyparsing import Forward, operatorPrecedence, opAssoc, Suppress, Keyword
from pyparsing import Optional
from string import ascii_lowercase, ascii_uppercase
import pyparsing
import itertools
# Importing ourselves; we end up using this to look up which function to call
# for each component of the AST
import jpath.engine #@UnresolvedImport

keychars = ascii_lowercase + ascii_uppercase


escape_map = {"\\": "\\", '"': '"', "n": "\n", "r": "\r"}
varNameRegex = r"\$[a-zA-Z][a-zA-Z0-9]*"

def trimTo(length, text):
    if len(text) < length:
        return text
    return text[:length] + "..."

def stringify(parser):
    """
    Adds a parse action to the specified parser to turn its matched token
    list into a single concatenated string. 
    """
    return parser.addParseAction(lambda t: "".join(t))

class InfixSeriesSuffixAction(object):
    def __init__(self, index):
        self.index = index
        
    def __call__(self, tokens):
        return {"i": self.index, "t": tokens[0]}

def InfixSeries(initial, operators):
    """
    Returns a parser that parses infix expressions. All the operators are
    assumed to have the same precedence level. initial is the parser
    representing the start of the expression. Each operator is a 2-tuple of:
    
    A parser that should parse both the operator and the expression on its
    right-hand side. It should have a parse action that causes it to return
    one and only one token.
    
    A function that accepts two parameters. We'll call them x and y. Once all
    of the operators are parsed, InfixSeries reduces from left to right (I may
    add an option for building right-associative InfixSeries instances at some
    point) each of the generated parse tokens. Since the initial parse token
    contributes to this, the first reduction will be the first infix operator
    that occurs in the parsed string. This function is then called, passing in
    x = either the initial token if no reductions have yet taken place, or the
    output generated by the last reduction performed, and y = the token that
    this operator's parser actually matched. The return value will then be
    passed as x to the next reduction that takes place, and so on.
    
    Once these reductions are complete, the result is returned as the parse
    token. If only the initial parser matches, then no reductions take place,
    and the token output of this parser is the token output of the initial
    parser.
    """
    if len(operators) == 0: # No operators, so just return the initial parser
        return initial
    parser = initial
    suffix_parsers = []
    for index, (operator_parser, function) in enumerate(operators):
        suffix_parsers.append(operator_parser.addParseAction(InfixSeriesSuffixAction(index)))
    parser = parser + ZeroOrMore(reduce(lambda x, y: x | y, suffix_parsers))
    def parse_action(t):
        results = list(t)
        return reduce(lambda x, y: operators[y["i"]][1](x, y["t"]), results)
    parser.addParseAction(parse_action)
    return parser

def SKeyword(text):
    """
    A suppressed keyword using keychars as the keyword end chars.
    """
    return Suppress(Keyword(text, keychars))

def NKeyword(text):
    """
    A non-suppressed keyword using keychars as the keyword end chars.
    """
    return Keyword(text, keychars)

def createPatternOrSpecial(pattern):
    if pattern == "true":
        return Boolean(True)
    elif pattern == "false":
        return Boolean(False)
    elif pattern == "null":
        return Null()
    return Pattern(pattern)

class Datatype(object):
    pass

def datatype(name, *varnames, **transformations):
    def __init__(self, *args):
        for index, var in enumerate(varnames):
            setattr(self, var, transformations.get(var, lambda t: t)(args[index]))
    def __repr__(self):
        return "<" + name + " " + ", ".join([var + ": " + repr(getattr(self, var)) for var in varnames]) + ">"
    return type(name, (Datatype,), {"__init__": __init__, "__str__": __repr__, "__repr__": __repr__})
    
Number = datatype("Number", "value", value=lambda t: float(t))
String = datatype("String", "value")
VarReference = datatype("VarReference", "name")
Boolean = datatype("Boolean", "value")
Null = datatype("Null")
ContextItem = datatype("ContextItem")
Children = datatype("Children")
PairChildren = datatype("PairChildren")
Pattern = datatype("Pattern", "value")
PairPattern = datatype("PairPattern", "value")
ParenExpr = datatype("ParenExpr", "expr")
ListConstructor = datatype("ListConstructor", "expr")
EmptyListConstructor = datatype("EmptyListConstructor")
MapConstructor = datatype("MapConstructor", "expr")
EmptyMapConstructor = datatype("EmptyMapConstructor")

Indexer = datatype("Indexer", "expr")
PairIndexer = datatype("PairIndexer", "expr")

Path = datatype("Path", "left", "right")
Predicate = datatype("Predicate", "left", "right")

Multiply = datatype("Multiply", "left", "right")
Divide = datatype("Divide", "left", "right")
Add = datatype("Add", "left", "right")
Subtract = datatype("Subtract", "left", "right")
Otherwise = datatype("Otherwise", "left", "right")

Equality = datatype("Equality", "left", "right")
Inequality = datatype("Inequality", "left", "right")
GreaterThan = datatype("GreaterThan", "left", "right")
LessThan = datatype("LessThan", "left", "right")
GreaterOrEqual = datatype("GreaterOrEqual", "left", "right")
LessOrEqual = datatype("LessOrEqual", "left", "right")

And = datatype("And", "left", "right")
Or = datatype("Or", "left", "right")

PairConstructor = datatype("PairConstructor", "left", "right")

CollectionConstructor = datatype("CollectionConstructor", "left", "right")

Flwor = datatype("Flwor", "constructs")
FlworFor = datatype("FlworFor", "name", "counter", "expr")
FlworLet = datatype("FlworLet", "name", "expr")
FlworWhere = datatype("FlworWhere", "expr")
# Add order by, let the ordering thing potentially be any arbitrary expression
# but note that ordering may slow down quite a bit if it's not a var, also
# consider defining ordering to be stable
FlworReturn = datatype("FlworReturn", "expr")


pExpr = Forward()

pNumber = Regex("[+-]?[0-9]+(\.[0-9]+)?").addParseAction(lambda t: Number("".join(t)))
pStringEscape = Regex(r"\\[a-zA-Z0-9]").addParseAction(lambda t: escape_map[t[0][1]])
pStringChar = Regex(r'[^\"\\]')
pString = stringify(Literal('"') + ZeroOrMore(pStringChar) + Literal('"')).addParseAction(lambda t: String(t[0][1:-1]))
pVarReference = Regex(varNameRegex).addParseAction(lambda t: VarReference(t[0][1:]))
pPattern = Regex("[a-zA-Z][a-zA-Z0-9]*").addParseAction(lambda t: createPatternOrSpecial(t[0]))
pPairPattern = Regex("@[a-zA-Z][a-zA-Z0-9]*").addParseAction(lambda t: PairPattern(t[0][1:])) # [1:] removes the leading "@"
pContextItem = Literal(".").addParseAction(lambda t: ContextItem())
pChildren = Literal("*").addParseAction(lambda t: Children())
pPairChildren = Literal("@*").addParseAction(lambda t: PairChildren())
pParenExpr = (Suppress("(") + pExpr + Suppress(")")).addParseAction(lambda t: ParenExpr(t[0]))
pListConstructor = (Suppress("[") + pExpr + Suppress("]")).addParseAction(lambda t: ListConstructor(t[0]))
pEmptyListConstructor = (Literal("[") + Literal("]")).addParseAction(lambda t: EmptyListConstructor())
pMapConstructor = (Suppress("{") + pExpr + Suppress("}")).addParseAction(lambda t: MapConstructor(t[0]))
pEmptyMapConstructor = (Literal("{") + Literal("}")).addParseAction(lambda t: EmptyMapConstructor())
pAtom = ( pParenExpr | pEmptyListConstructor | pListConstructor
        | pEmptyMapConstructor | pMapConstructor | pNumber | pString
        | pVarReference | pPattern | pPairPattern | pContextItem
        | pChildren | pPairChildren )

pIndexer = (Suppress("#") + pAtom).addParseAction(lambda t: Indexer(t[0]))
pPairIndexer = (Suppress("@#") + pAtom).addParseAction(lambda t: PairIndexer(t[0]))
pIndividual = pIndexer | pPairIndexer | pAtom

pInfix = pIndividual

pInfix = InfixSeries(pInfix,
        [
            ((Suppress("/") + pInfix), Path), 
            ((Suppress("[") + pExpr + Suppress("]")), Predicate)
        ])

pInfix = InfixSeries(pInfix,
        [
            ((Suppress(Literal(u"×") | Keyword("times", keychars) | Keyword("mul", keychars)) + pInfix), Multiply),
            ((Suppress(Literal(u"÷") | Keyword("divided by", keychars) | Keyword("div", keychars)) + pInfix), Divide)
        ])

pInfix = InfixSeries(pInfix,
        [
            ((Suppress(Literal(u"+") | Keyword("plus", keychars) | Keyword("add", keychars)) + pInfix), Add),
            ((Suppress(Literal(u"-") | Keyword("minus", keychars) | Keyword("sub", keychars)) + pInfix), Subtract)
        ])

pInfix = InfixSeries(pInfix,
        [
            ((Suppress(Keyword("otherwise", keychars)) + pInfix), Otherwise)
        ])

pInfix = InfixSeries(pInfix,
        [
            ((Suppress(Literal(">=")) + pInfix), GreaterOrEqual),
            ((Suppress(Literal("<=")) + pInfix), LessOrEqual),
            ((Suppress(Literal(">")) + pInfix), GreaterThan),
            ((Suppress(Literal("<")) + pInfix), LessThan),
            ((Suppress(Literal("!=")) + pInfix), Inequality),
            ((Suppress(Literal("=")) + pInfix), Equality)
        ])

pInfix = InfixSeries(pInfix,
        [
            ((Suppress(Keyword("and", keychars)) + pInfix), And),
            ((Suppress(Keyword("or", keychars)) + pInfix), Or)
        ])

pInfix = InfixSeries(pInfix,
        [
            ((Suppress(Literal(":")) + pInfix), PairConstructor)
        ])

pInfix = InfixSeries(pInfix,
        [
            ((Suppress(Literal(",")) + pInfix), CollectionConstructor)
        ])

pFlworFor = (SKeyword("for") + Regex(varNameRegex) + Optional(SKeyword("at") + Regex(varNameRegex), "") + SKeyword("in")
            + pInfix).addParseAction(lambda t: FlworFor(t[0][1:], t[1][1:], t[2]))
pFlworLet = (SKeyword("let") + Regex(varNameRegex) + Suppress(":=") + pInfix).addParseAction(lambda t: FlworLet(t[0][1:], t[1]))
pFlworWhere = (SKeyword("where") + pInfix).addParseAction(lambda t: FlworWhere(t[0]))
pFlworReturn = (Suppress(Keyword("return", keychars)) + pInfix).setParseAction(lambda t: FlworReturn(t[0]))
pFlwor = (OneOrMore(pFlworFor | pFlworLet | pFlworWhere) + pFlworReturn).addParseAction(lambda t: Flwor(list(t)))

pFlworOrInfix = pFlwor | pInfix

pExpr << (pFlworOrInfix)


def parse(text):
    results = list(pExpr.parseString(text, parseAll=True))
    if len(results) != 1:
        raise Exception("Problem while parsing results: precisely one "
                "result was expected, but " + str(len(results)) + " were "
                "provided by the parser")
    return results[0]



class Context(object):
    def __init__(self, item=None, vars=None):
        self.item = item
        self.vars = vars
        if self.vars is None:
            self.vars = {}
    
    def var(self, name):
        return self.vars[name]
    
    def new_with_var(self, name, value):
        if not isinstance(value, list):
            raise Exception("Variable values have to be collections "
                    "(represented in Python as lists). So, instead of, for "
                    "example, c.new_with_var('foo', 1), do "
                    "c.new_with_var('foo', [1]).")
        vars = dict(self.vars)
        vars.update({name: value})
        return Context(self.item, vars)
    
    def new_with_item(self, item):
        return Context(item, self.vars)
    
    def __repr__(self):
        return "Context(" + repr(self.item) + ", " + repr(self.vars) + ")"

class Pair(object):
    def __init__(self, key, value):
        self.key = key
        self.value = value
    
    def __repr__(self):
        return "Pair(" + repr(self.key) + ", " + repr(self.value) + ")"

def is_true_value(value):
    return value is not None and value != False # TODO: decide on a definition
    # of what values in JPath are true and what values are false

def is_true_collection(collection):
    if len(collection) == 0:
        return False
    return all(map(is_true_value, collection)) # A collection is true if it's
    # not empty and every one of its values is also true

def binary_comparison(context, left_expr, right_expr, function):
    left_value = evaluate(context, left_expr)
    right_value = evaluate(context, right_expr)
    return any([function(x, y) for x in left_value for y in right_value])

def evaluate(context, query):
    """
    Runs the specified query in the specified context, which should be a
    Context instance. The context can specify a context item and a set of
    variables that will already be assigned values when the query runs.
    
    The query can be either a string representing the query to run or the
    return value of parse(query_text). If you're going to be running the same
    query over and over again, you should generally call parse and store the
    result to avoid the delay of having to re-parse the query every time. I
    ran some benchmarks on a 1.66GHz Intel Core 2 Duo and storing the results
    of a call to parse and just evaluating that stored value resulted in
    queries running about 300 times faster (300 seconds, or 5 minutes, to run
    the query {{"a": "b", "c": "d"}/@a} 30000 times from text as opposed to
    1 second to run this query pre-parsed 30000 times). 
    
    This function returns a list of all of the items selected by the query.
    
    Some examples:
    
    >>> evaluate("foo", Context({"foo": "bar"}))
    ["bar"]
    
    >>> evaluate("foo/bar", Context({"foo": {"bar": "baz"}})
    ["baz"]
    
    >>> evaluate("*/foo", Context([{"foo": "bar"}, {"foo": "baz"}]))
    ["bar", "baz"]
    
    >>> evaluate('{{"a": "b", "c": "d"}/@a}', Context())
    {"a": "b"}
    """
    if isinstance(query, basestring):
        query = parse(query)
    # Figure out the method to dispatch to
    typename = type(query).__name__
    function = getattr(jpath.engine, "evaluate_" + typename, None)
    if function is None:
        raise Exception("Evaluate not implemented for AST component type " + 
                typename + " containing " + trimTo(200, repr(query)))
    result = function(context, query)
    if not isinstance(result, list):
        raise Exception("Result was not a list for AST component type " + 
                typename + " containing " + trimTo(200, repr(query)))
    return result

def evaluate_Number(context, query):
    return [query.value]

def evaluate_String(context, query):
    return [query.value]

def evaluate_VarReference(context, query):
    return context.var(query.name)

def evaluate_Boolean(context, query):
    return [query.value]

def evaluate_Null(context, query):
    return [None]
    
def evaluate_ContextItem(context, query):
    # Context item is a single item, not a collection
    return [context.item]

def evaluate_Children(context, query):
    if isinstance(context.item, dict):
        return context.item.values()
    elif isinstance(context.item, list):
        return context.item
    else:
        return []

def evaluate_PairChildren(context, query):
    if isinstance(context.item, dict):
        return [Pair(k, v) for k, v in context.item.items()]
    else:
        return []

def evaluate_Pattern(context, query):
    if isinstance(context.item, dict):
        if query.value in context.item:
            return [context.item[query.value]]
        else:
            return []
    elif isinstance(context.item, Pair):
        if query.value == "key":
            return [context.item.key]
        elif query.value == "value":
            return [context.item.value]
    return []

def evaluate_PairPattern(context, query):
    if isinstance(context.item, dict):
        if query.value in context.item:
            return [Pair(query.value, context.item[query.value])]
    return []

def evaluate_ParenExpr(context, query):
    return evaluate(context, query.expr)

def evaluate_ListConstructor(context, query):
    return [list(evaluate(context, query.expr))] # Create a list containing
    # the items present in the collection to be evaluated

def evaluate_EmptyListConstructor(context, query):
    return [[]]

def evaluate_MapConstructor(context, query):
    collection = evaluate(context, query.expr)
    result = {}
    for pair in collection:
        if not isinstance(pair, Pair):
            raise Exception("Maps (JSON objects) can only be constructed "
                    "from collections containing only pairs. The collection "
                    "being used to construct this map, however, contains an "
                    "item of type " + str(type(pair)) + ": " + repr(pair))
        result[pair.key] = pair.value
    return [result]

def evaluate_EmptyMapConstructor(context, query):
    return [{}]

def evaluate_Path(context, query):
    left_value = evaluate(context, query.left)
    result_collections = [evaluate(context.new_with_item(v), query.right) for v in left_value]
    return list(itertools.chain(*result_collections))

def evaluate_Predicate(context, query):
    left_value = evaluate(context, query.left)
    return [v for v in left_value if is_true_collection(evaluate(context.new_with_item(v), query.right))]

def evaluate_Equality(context, query):
    return [binary_comparison(context, query.left, query.right, lambda x, y: x == y)]

def evaluate_PairConstructor(context, query):
    left_value = evaluate(context, query.left)
    right_value = evaluate(context, query.right)
    if len(left_value) != len(right_value):
        raise Exception("The length of the collections on either side of a "
                "pair constructor must be the same. However, they were " +
                str(len(left_value)) + " and " + str(len(right_value)) +
                " for the key and the value, respectively.")
    return [Pair(k, v) for k, v in zip(left_value, right_value)]

def evaluate_CollectionConstructor(context, query):
    left_value = evaluate(context, query.left)
    right_value = evaluate(context, query.right)
    return left_value + right_value


































