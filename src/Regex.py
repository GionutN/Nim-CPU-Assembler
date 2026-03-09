from NFA import NFA, symbol_nfa, kleene_star, join_union_nfas, join_concat_nfas
from enum import Enum
import string

EPSILON = ''

class Token_types(str, Enum):
    CONCATENATION = "CONCATENATION"
    OR = "OR"
    STAR = "STAR"
    PLUS = "PLUS"
    OPTIONAL = "OPTIONAL"
    SYMBOL = "SYMBOL"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"

class Token:
    def __init__(self, type, value = None):
        self.type = type
        self.value = value

    def get_type(self):
        return self.type
    def get_value(self):
        return self.value

    def __repr__(self):
        if self.value:
            return f"Token({self.type}, {self.value})"
        return f"Token({self.type})"

class Regex:
    def __init__(self, regex):
        self.regex = regex
        self.tokens = []
        self.__parse_tokens()

        self.priorities = {Token_types.LPAREN:0, Token_types.RPAREN:0, Token_types.STAR:3,
                           Token_types.PLUS:3, Token_types.OPTIONAL:3, 
                           Token_types.CONCATENATION:2, Token_types.OR:1}
        self.rpn = []   # reverse polish notation
        self.__shunting_yard()

    def __should_add_concat(self, tok1, tok2):
        if tok1 == None:
            return False
        
        type1 = tok1.get_type()
        type2 = tok2.get_type()

        result = False
        result = result or type1 == Token_types.SYMBOL and type2 == Token_types.SYMBOL
        result = result or type1 == Token_types.SYMBOL and type2 == Token_types.LPAREN

        result = result or type1 == Token_types.STAR and type2 == Token_types.SYMBOL
        result = result or type1 == Token_types.STAR and type2 == Token_types.LPAREN

        result = result or type1 == Token_types.PLUS and type2 == Token_types.SYMBOL
        result = result or type1 == Token_types.PLUS and type2 == Token_types.LPAREN

        result = result or type1 == Token_types.OPTIONAL and type2 == Token_types.SYMBOL
        result = result or type1 == Token_types.OPTIONAL and type2 == Token_types.LPAREN

        result = result or type1 == Token_types.RPAREN and type2 == Token_types.SYMBOL
        result = result or type1 == Token_types.RPAREN and type2 == Token_types.LPAREN

        return result

    def __parse_tokens(self):   # also adds concatenations where necessary
        idx = 0
        n = len(self.regex)
        last_token = None
        while idx < n:
            c = self.regex[idx]
            last_token = None if idx == 0 else self.tokens[-1]

            # handle escapes
            if c == '\\':
                if idx + 1 >= n:
                    # '\' is the last character
                    crt_token = Token(Token_types.SYMBOL, '\\')
                    if self.__should_add_concat(last_token, crt_token):
                        self.tokens.append(Token(Token_types.CONCATENATION))
                    self.tokens.append(crt_token)
                    break
                elif self.regex[idx + 1] not in ['|', '*', '+', '?', '(', ')', ' ', '/']:
                    # the next char is not special
                    crt_token = Token(Token_types.SYMBOL, '\\')
                    if self.__should_add_concat(last_token, crt_token):
                        self.tokens.append(Token(Token_types.CONCATENATION))
                    self.tokens.append(crt_token)
                    idx += 1
                    continue
                else:
                    # the next char is special
                    crt_token = Token(Token_types.SYMBOL, self.regex[idx + 1])
                    if self.__should_add_concat(last_token, crt_token):
                        self.tokens.append(Token(Token_types.CONCATENATION))
                    self.tokens.append(crt_token)
                    idx += 2
                    continue
            
            # ignore non-escaped white spaces
            if c == ' ':
                idx += 1
                continue

            # handle shorthands
            if c == '[':
                if self.__should_add_concat(last_token, Token(Token_types.LPAREN)):
                        self.tokens.append(Token(Token_types.CONCATENATION))
                self.tokens.append(Token(Token_types.LPAREN))
                if self.regex[idx + 1] == '0':
                    # [0-9] found
                    for i in range(0, 9):
                        self.tokens.append(Token(Token_types.SYMBOL, str(i)))
                        self.tokens.append(Token(Token_types.OR))
                    self.tokens.append(Token(Token_types.SYMBOL, '9'))
                elif self.regex[idx + 1] == 'a':
                    # [a-z] found
                    all_lower = list(string.ascii_lowercase)
                    for i in range(0, len(all_lower) - 1):
                        self.tokens.append(Token(Token_types.SYMBOL, all_lower[i]))
                        self.tokens.append(Token(Token_types.OR))
                    self.tokens.append(Token(Token_types.SYMBOL, 'z'))
                elif self.regex[idx + 1] == 'A':
                    # [A-Z] found
                    all_caps = list(string.ascii_uppercase)
                    for i in range(0, len(all_caps) - 1):
                        self.tokens.append(Token(Token_types.SYMBOL, all_caps[i]))
                        self.tokens.append(Token(Token_types.OR))
                    self.tokens.append(Token(Token_types.SYMBOL, 'Z'))

                self.tokens.append(Token(Token_types.RPAREN))
                idx += 5
                continue

            # handle operators
            if c == '*':
                crt_token = Token(Token_types.STAR)
                if self.__should_add_concat(last_token, crt_token):
                    self.tokens.append(Token(Token_types.CONCATENATION))
                self.tokens.append(crt_token)
                idx += 1
                continue
            if c == '+':
                crt_token = Token(Token_types.PLUS)
                if self.__should_add_concat(last_token, crt_token):
                    self.tokens.append(Token(Token_types.CONCATENATION))
                self.tokens.append(crt_token)
                idx += 1
                continue
            if c == '?':
                crt_token = Token(Token_types.OPTIONAL)
                if self.__should_add_concat(last_token, crt_token):
                    self.tokens.append(Token(Token_types.CONCATENATION))
                self.tokens.append(crt_token)
                idx += 1
                continue
            if c == '|':
                crt_token = Token(Token_types.OR)
                if self.__should_add_concat(last_token, crt_token):
                    self.tokens.append(Token(Token_types.CONCATENATION))
                self.tokens.append(crt_token)
                idx += 1
                continue

            # handle parantheses
            if c == '(':
                crt_token = Token(Token_types.LPAREN)
                if self.__should_add_concat(last_token, crt_token):
                    self.tokens.append(Token(Token_types.CONCATENATION))
                self.tokens.append(crt_token)
                idx += 1
                continue
            if c == ')':
                crt_token = Token(Token_types.RPAREN)
                if self.__should_add_concat(last_token, crt_token):
                    self.tokens.append(Token(Token_types.CONCATENATION))
                self.tokens.append(crt_token)
                idx += 1
                continue

            # just a symbol
            crt_token = Token(Token_types.SYMBOL, c)
            if self.__should_add_concat(last_token, crt_token):
                self.tokens.append(Token(Token_types.CONCATENATION))
            self.tokens.append(crt_token)
            idx += 1

    def __shunting_yard(self):
        op_stack = []

        for token in self.tokens:
            if token.get_type() == Token_types.SYMBOL:
                self.rpn.append(token)
            elif token.get_type() == Token_types.LPAREN:
                op_stack.append(token)
            elif token.get_type() == Token_types.RPAREN:
                while op_stack[-1].get_type() != Token_types.LPAREN:
                    self.rpn.append(op_stack.pop())
                op_stack.pop()  # discard the opening parentheses
            
            # handle the unary operators, highest priority, right-associativity
            elif self.priorities[token.get_type()] == 3:
                op_stack.append(token)
            
            # handle concatenation/union, left-associativity
            elif self.priorities[token.get_type()] < 3:
                prio = self.priorities[token.get_type()]
                # remove all operations with >= priority
                if len(op_stack) != 0:
                    while self.priorities[op_stack[-1].get_type()] >= prio:
                        self.rpn.append(op_stack.pop())
                        if len(op_stack) == 0:
                            break
                op_stack.append(token)
        
        # pop the last remaining operations
        while len(op_stack) != 0:
            self.rpn.append(op_stack.pop())
 
    def thompson(self) -> NFA[int]:
        tag = 0 # used to mark the nfa states without having 2 states with the same tag
        tree_stack = []
        for token in self.rpn:
            if token.get_type() == Token_types.SYMBOL:
                # construct a nfa and add it to the stack
                tree_stack.append(symbol_nfa(token.get_value(), tag))
                tag += 2    # nfa creation adds 2 to the tag
            elif token.get_type() == Token_types.OR:
                # pop the right and left nfas from the stack, combine them into a new one and push
                nfa2 = tree_stack.pop()
                nfa1 = tree_stack.pop()
                tree_stack.append(join_union_nfas(nfa1, nfa2))
                tag += 2    # union joining adds to the tag (extra start/ends states)
            elif token.get_type() == Token_types.CONCATENATION:
                # pop the right and left nfas from the stack, combine them into a new one and push
                nfa2 = tree_stack.pop()
                nfa1 = tree_stack.pop()
                tree_stack.append(join_concat_nfas(nfa1, nfa2))
                tag -= 1
            elif token.get_type() == Token_types.STAR:
                # pop the operand from the stack, kleene star it and push
                nfa = tree_stack.pop()
                tree_stack.append(kleene_star(nfa))
                tag += 2
            elif token.get_type() == Token_types.PLUS:
                # e+ = ee*
                nfa = tree_stack.pop()

                offset = len(nfa.get_K())
                starred = nfa.remap_states(lambda x: x + offset)
                starred = kleene_star(starred)

                tree_stack.append(join_concat_nfas(nfa, starred))
                tag += offset + 1
            elif token.get_type() == Token_types.OPTIONAL:
                # e? = e | eps
                nfa = tree_stack.pop()
                eps = symbol_nfa(EPSILON, tag)
                tag += 2

                tree_stack.append(join_union_nfas(nfa, eps))
                tag += 2

        return tree_stack.pop()
                
def parse_regex(rgx) -> Regex:
    return Regex(rgx)
