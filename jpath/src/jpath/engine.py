
from pyparsing import Literal, OneOrMore, ZeroOrMore, Regex, MatchFirst
from pyparsing import Forward, operatorPrecedence, opAssoc, Suppress
import pyparsing


escape_map = {"\\": "\\", '"': '"', "n": "\n", "r": "\r"}

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

def InfixSeries(initial, *operators):
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

def createPatternOrSpecial(pattern):
    if pattern == "true":
        return Boolean(True)
    elif pattern == "false":
        return Boolean(False)
    elif pattern == "null":
        return Null()
    return Pattern(pattern)

def datatype(name, *varnames, **transformations):
    def __init__(self, *args):
        for index, var in enumerate(varnames):
            setattr(self, var, transformations.get(var, lambda t: t)(args[index]))
    def __repr__(self):
        return "<" + name + " " + ", ".join([var + ": " + repr(getattr(self, var)) for var in varnames]) + ">"
    return type(name, (object,), {"__init__": __init__, "__str__": __repr__, "__repr__": __repr__})
    
Number = datatype("Number", "value", value=lambda t: float(t))

String = datatype("String", "value")

VarReference = datatype("VarReference", "name")

Boolean = datatype("Boolean", "value")

Null = datatype("Null") 

Pattern = datatype("Pattern", "value")

PairPattern = datatype("PairPattern", "value")

Indexer = datatype("Indexer", "expr")

PairIndexer = datatype("PairIndexer", "expr")

ParenExpr = datatype("ParenExpr", "expr")

ListConstructor = datatype("ListConstructor", "expr")

MapConstructor = datatype("MapConstructor", "expr")

Path = datatype("Path", "left", "right")

Predicate = datatype("Predicate", "left", "right")

pExpr = Forward()

pNumber = Regex("[+-]?[0-9]+(\.[0-9]+)?").addParseAction(lambda t: Number("".join(t)))
pStringEscape = Regex(r"\\[a-zA-Z0-9]").addParseAction(lambda t: escape_map[t[0][1]])
pStringChar = Regex(r'[^\"\\]')
pString = stringify(Literal('"') + ZeroOrMore(pStringChar) + Literal('"')).addParseAction(lambda t: String(t[0][1:-1]))
pVarReference = Regex(r"\$[a-zA-Z][a-zA-Z0-9]*").addParseAction(lambda t: VarReference(t[0][1:]))
pPattern = Regex("[a-zA-Z][a-zA-Z0-9]*").addParseAction(lambda t: createPatternOrSpecial(t[0]))
pPairPattern = Regex("@[a-zA-Z][a-zA-Z0-9]").addParseAction(lambda t: PairPattern(t[0]))
pParenExpr = (Suppress("(") + pExpr + Suppress(")")).addParseAction(lambda t: ParenExpr(t[0]))
pListConstructor = (Suppress("[") + pExpr + Suppress("]")).addParseAction(lambda t: ListConstructor(t[0]))
pMapConstructor = (Suppress("{") + pExpr + Suppress("}")).addParseAction(lambda t: MapConstructor(t[0]))
pAtom = ( pParenExpr | pListConstructor | pMapConstructor | pNumber | pString
        | pVarReference | pPattern | pPairPattern)

pIndexer = (Suppress("#") + pAtom).addParseAction(lambda t: Indexer(t[0]))
pPairIndexer = (Suppress("@#") + pAtom).addParseAction(lambda t: PairIndexer(t[0]))
pIndividual = pIndexer | pPairIndexer | pAtom

pPath = InfixSeries(pIndividual, 
                                 ((Suppress("/") + pIndividual), Path), 
                                 ((Suppress("[") + pExpr + Suppress("]")), Predicate))

pExpr << (pPath)











































