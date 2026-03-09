from DFA import DFA

from dataclasses import dataclass
from collections.abc import Callable

EPSILON = ''

@dataclass
class NFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], set[STATE]]
    F: set[STATE]

    def get_S(self) -> set[str]:
        return self.S.copy()
    def get_K(self) -> set[STATE]:
        return self.K.copy()
    def get_d(self) -> dict[tuple[STATE, str], set[STATE]]:
        return self.d.copy()
    def get_q0(self) -> STATE:
        return self.q0
    def get_F(self) -> set[STATE]:
        return self.F.copy()

    def epsilon_closure(self, state: STATE) -> set[STATE]:
        closure = set([state])
        next = self.d.get((state, EPSILON), set())

        while len(next) != 0:
            closure |= next

            new_next = set()
            for s in next:
                new_next |= self.d.get((s, EPSILON), set())
            next = new_next - closure


        return closure

    def subset_construction(self) -> DFA[frozenset[STATE]]:
        dfa_start = self.epsilon_closure(self.q0)

        dfa_k = set()
        introduced_states = set([frozenset(dfa_start)]) # set of new dfa states
        used_states = set() # dfa states

        dfa_d = dict()
        while len(introduced_states) != 0:
            dfa_k |= introduced_states
            new_introduced_states = set()   # set of dfa states starting from the current one

            for dfa_state in introduced_states:
                if dfa_state not in used_states:
                    for c in self.S:
                        new_state = set()

                        # add all the states accessible from the current state by consuming a character
                        for nfa_state in dfa_state:
                            new_state |= self.d.get((nfa_state, c), set())

                        for nfa_state in new_state.copy():
                            new_state |= self.epsilon_closure(nfa_state)

                        # add the epsilon closure of this new state
                        new_introduced_states.add(frozenset(new_state))

                        # add the function entry to the dfa
                        dfa_d[(frozenset(dfa_state), c)] = frozenset(new_state)
                
                used_states.add(frozenset(dfa_state))

            introduced_states = new_introduced_states - dfa_k

        dfa_f = dfa_k.copy()
        for state in dfa_f.copy():
            is_final = False
            for nfa_state in state:
                if nfa_state in self.F:
                    is_final = True
                    break
            
            if not is_final:
                dfa_f.remove(state)

        return DFA(self.S.copy(), dfa_k, frozenset(dfa_start), dfa_d, dfa_f)

    def remap_states[OTHER_STATE](self, f: Callable[[STATE], 'OTHER_STATE']) -> 'NFA[OTHER_STATE]':
        new_K = {f(s) for s in self.K}
        new_q0 = f(self.q0)
        new_F = {f(s) for s in self.F}

        new_d = {}
        for (old_state, symbol), targets in self.d.items():
            new_state = f(old_state)
            new_targets = {f(t) for t in targets}
            new_d[(new_state, symbol)] = new_targets

        return NFA(self.S.copy(), new_K, new_q0, new_d, new_F)

def symbol_nfa(symbol, start_idx = 0) -> NFA[int]:
    S = set([symbol]) if symbol != EPSILON else set()
    K = set([start_idx, start_idx + 1])
    q0 = start_idx
    d = {(start_idx, symbol):set([start_idx + 1])}
    F = set([start_idx + 1])

    return NFA(S, K, q0, d, F)

def kleene_star(nfa) -> 'NFA[int]':
    # make sure the tags are greater than start_idx
    start_idx = nfa.get_q0()
    nfa = nfa.remap_states(lambda x: x + 1)
    S = nfa.get_S()

    K = nfa.get_K()
    end_idx = start_idx + len(K) + 1
    K.add(start_idx)
    K.add(end_idx)

    d = nfa.get_d()
    d[(start_idx, EPSILON)] = d.get((start_idx, EPSILON), set()) | set([start_idx + 1, end_idx])
    d[(end_idx - 1, EPSILON)] = d.get((end_idx - 1, EPSILON), set()) | set([start_idx + 1, end_idx])

    return NFA(S, K, start_idx, d, set([end_idx]))

def join_union_nfas(n1, n2) -> 'NFA[int]':
    start_idx = n1.get_q0()
    n1 = n1.remap_states(lambda x: x + 1)
    n2 = n2.remap_states(lambda x: x + 1)

    S = n1.get_S() | n2.get_S()

    K = n1.get_K() | n2.get_K()
    end_idx = start_idx + len(K) + 1
    # additional start and end states
    K.add(start_idx)
    K.add(end_idx)

    d = n1.get_d()
    d2 = n2.get_d()
    for key, targets in d2.items():
        d[key] = d.get(key, set()) | targets
    d[(start_idx, EPSILON)] = set([start_idx + 1, start_idx + len(n1.get_K()) + 1])
    d[(end_idx - 1, EPSILON)] = d.get((end_idx - 1, EPSILON), set()) | set([end_idx])
    d[(start_idx + len(n1.get_K()), EPSILON)] = set([end_idx])
    return NFA(S, K, start_idx, d, set([end_idx]))

def join_concat_nfas(n1, n2) -> 'NFA[int]':
    n2 = n2.remap_states(lambda x: x - 1)
    S = n1.get_S() | n2.get_S()
    K = n1.get_K() | n2.get_K()

    d = n1.get_d()
    d2 = n2.get_d()
    for key, targets in d2.items():
        d[key] = d.get(key, set()) | targets

    return NFA(S, K, n1.get_q0(), d, n2.get_F())
