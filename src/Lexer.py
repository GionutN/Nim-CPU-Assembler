from Regex import Regex, parse_regex
from NFA import NFA, EPSILON
from DFA import DFA

class Lexer:
    def __init__(self, spec: list[tuple[str, str]]) -> None:
        # build the NFAs
        nfas: list[NFA[int]] = []
        for s in spec:
            r: Regex = parse_regex(s[1])
            nfas.append(r.thompson())

        self.dfas: list[tuple[str, DFA[frozenset[int]]]] = []
        for i in range(0, len(nfas)):
            dfa = nfas[i].subset_construction().minimize()
            self.dfas.append((spec[i][0], dfa))

    
    def lex(self, word: str) -> list[tuple[str, str]]:
        i = 1
        n = len(word)
        accepted: str = None
        accepted_idx = 0
        found_idx = 0
        accepted_token:str = None
        lexemes: list[tuple[str, str]] = list()
        register_found = False
            
        i = 1
        while i <= n:
            lexeme = word[found_idx:i]
            # check if there are any dfas that accept the word

            all_in_sink: bool = True
            for dfa in self.dfas:
                val = dfa[1].accept(lexeme)
                if val == True:
                    accepted = lexeme
                    accepted_idx = i
                    accepted_token = dfa[0]
                    all_in_sink = False
                    break
                elif val == False:
                    all_in_sink = False

            # if all dfas are in sink, then terminate search early
            add_lexeme = False
            if not all_in_sink:
                if i == n:
                    if accepted != None:
                        add_lexeme = True
                    else:
                        return [(EPSILON, "No viable alternative at character " + str(len(word) + 1))]
                else:
                    i = i + 1
                    
            elif accepted == None:
                return [(EPSILON, "No viable alternative at character " + str(i))]
            else:
                add_lexeme = True
            
            if add_lexeme:
                i = accepted_idx + 1
                if accepted_token != "SPACE" and accepted_token != "NEWLINE" and accepted_token != "COMMENT":
                    if accepted_token == "REGISTER":
                        if accepted in ["s2", "s1", "s1p", "rx"]:
                            accepted_token = "SOURCE"
                            register_found = True
                        elif register_found:
                            accepted_token = "SOURCE"
                        else:
                            accepted_token = "DESTINATION"
                            register_found = True
                    lexemes.append((accepted_token, accepted))
                found_idx = accepted_idx
                accepted = None

        return lexemes
