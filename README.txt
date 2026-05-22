    Overview
    This project is a more complete assembler for my Nim CPU. Not only does it go through the code, translating assembly
to machine code one-to-one, but it also checks for lexical and grammatical errors inside it.

    Requirements
    Python 3.13+ interpreter

    Project description
    The assembler goes through the code similar to how a compiler would. Regexes, deterministic finite automatons and
lexical and syntactical passes are used so that the programmer gets a correct output or help finding language errors.

    Architecture overview
    The assembler always follows the same steps: lexical definitions written by the user inside a .json file, regexes are
then parsed and transformed into an NFA, the NFA gets turned into a DFA, and then the DFAs are used inside the Lexer to
get the actual language token or an error.
    While it would have been more efficient to have the DFAs precomputed and used as is, I chose to compute them every
time the assembler is used because this allows other people to define their own assembly languages with minimal knolwedge
regarding formal languages and automatas.
    Inside "lexer_spec.json" I defined the regexes I used in my assembler. Some design choices I made were that:
        - tags must start with a dot (inspired by how GCC compilers use .Ln tags), followed by any number of lower case letters
            numbers and underscores
        - immediates can be defined in decimal, hexadecimal (0x...) and binary (0b...) for convenience
        - i also added support for comments
        - only lower case letters are allowed

    The next step is the regex parsing, done inside the Regex class. First, it goes through the whole string and adds
concatenation operations where needed (because humans usually write "ab" for concatenation). Then a shunting yard
algorithm reorders the tokens in reverse polish notations so that building the NFA takes into account the order of
operations. Finally, using Thompson's algorithm, the entire regex is turned into an NFA.
    The NFA class's role is to turn itself into a DFA, using the subset construction algorithm, but the NFA.py file also
comes with helper functions that combine two NFAs into a single one depending on the operation.
    After the DFA was built, its minimize() method gets called so that it gets simplified when used later. Its main job
is to check if it accepts or not a word given as input.

    These three classes are then used together inside the Lexer class. Its lex() method is used to split an entire line
of assembly code in tokens, used later by the syntactical pass. This method always returns the largest token found until
failure. If none is found, an error message is returned, telling the user the exact character where the lexer failed to
find any new token, making it easier for the programmer to fix typos.
    Because turning assembly code into machine code is usually done one-to-one, no complex grammar is used. These are
some grammar design choices i made:
        - a line of code can not contain both a tag and an instruction
        - a tag is followed by a double colon
        - jumps can use both immediates and tags as parameters
    The grammar also ensures that all instructions are always written correctly.

    The assembler then uses these rules to turn the assembly code into machine code in four passes:
        - lexical pass: ensures all tokens match their regex expression
        - syntactical pass: the context in which lexemes are used makes sense
        - labels pass: remembers the address of each tag
        - encoding pass: the assembler has all the data it needs to transform the code
        - writing the output: the resulting machine code is written in the same format used by Logisim Evolution's
            memory components
