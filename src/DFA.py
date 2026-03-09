from dataclasses import dataclass
from typing import TypeVar

STATE = TypeVar('STATE')

@dataclass
class DFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], STATE]
    F: set[STATE]
    

    def accept(self, word: str):
        # the function returns -1 if the word ended in a sink state
        # returns true or false if the word is accepted or not
        crt_state = self.q0
        for c in word:
            next = self.d.get((crt_state, c), None)
            if next == None:
                return -1
            
            crt_state = next

        is_sink = True
        for c in self.S:
            if self.d[(crt_state, c)] != crt_state:
                is_sink = False
                break

        if is_sink and crt_state not in self.F:
            return -1
        
        return crt_state in self.F

    def __predecessors(self, state, c) -> set[STATE]:
        x = set()
        for s in self.K:
            if self.d[(s, c)] == state:
                x.add(s)

        return x

    def minimize(self) -> 'DFA[STATE]':
        P = set([frozenset(self.F), frozenset(self.K - self.F)])
        W = P.copy()
        while len(W) != 0:
            A = W.pop()
            for c in self.S:
                # get all the states that land on A on character c
                X = set()
                for state in A:
                    X |= self.__predecessors(state, c)

                new_P = set()
                for Y in P:
                    Y1 = Y & X
                    Y2 = Y - X
                    if len(Y1) != 0 and len(Y2) != 0:
                        new_P.add(frozenset(Y1))
                        new_P.add(frozenset(Y2))
                        if Y in W:
                            W.remove(Y)
                            W.add(frozenset(Y1))
                            W.add(frozenset(Y2))
                        elif len(Y1) <= len(Y2):
                            W.add(frozenset(Y1))
                        else:
                            W.add(frozenset(Y2))
                    
                    else:
                        new_P.add(Y)
                
                P = new_P

        listP = []
        for lp in P.copy():
            listP.append(list(lp))

        new_K = set()
        new_F = set()
        new_d = dict()

        i = 0
        # rebuild F' and K' by getting the first element inside the set of each block
        # except for the q0, this remains constant
        for block in listP:
            if len(block) == 0:
                i += 1
                continue
            is_final = len(set(block) & self.F) != 0

            elem = self.q0
            if self.q0 not in block:
                elem = listP[i][0]
            
            new_K.add(elem)
            if is_final:
                new_F.add(elem)
            
            i += 1

        # for every new state, get the first state from the block of states
        # where the destination is
        for state in new_K:
            for c in self.S:
                next_state = self.d[(state, c)]
                for block in listP:
                    if next_state in block:
                        if self.q0 in block:
                            next_state = self.q0
                        else:
                            next_state = block[0]

                new_d[(state, c)] = next_state

        return DFA(self.S.copy(), new_K, self.q0, new_d, new_F)
    