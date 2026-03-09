import sys
import json
from Lexer import Lexer

# operands per instruction
INSTRUCTION_SET = {
    "ldi": 2, "mov": 2,
    "jmp": 1, "jnz": 1, "jle": 1, "jge": 1,
    "sub": 0, "xor": 0, "kcl": 0, "nop": 0
}

LINE_GRAMMAR = [
    (["TAG", "COLON"], "[tag_name]:"),
    (["NOOPS"], "nop/kcl"),
    (["JUMP", "IMMEDIATE"], "jmp/jnz/jle/jge [immediate]"),
    (["JUMP", "TAG"], "jmp/jnz/jle/jge [tag_name]"),
    (["LOAD", "DESTINATION", "IMMEDIATE"], "ldi [dest_reg] [immediate]"),
    (["MOVE", "DESTINATION", "SOURCE"], "mov [dest_reg] [src_reg]")
]

class Assembler:
    def __init__(self, input: str, output: str):
        self.input = input
        self.output = output
        self.lexemes = []
        self.labels = {}
        self.machine_code = []

    def run(self) -> bool:
        self.__lexical_pass()
        self.__syntactical_pass()
        self.__labels_pass()
        self.__encoding_pass()
        self.__output_code()

    def __lexical_pass(self):
        with open(self.input, "r") as f:
            lines = f.readlines()

        with open("lexer_spec.json", "r") as f:
            spec = json.load(f)
            spec = list(spec.items())

        lexer = Lexer(spec)
        for i in range(len(lines)):
            res = lexer.lex(lines[i])
            if len(res) != 0:
                if (res[0][1].startswith("No")):
                    print(res[0][1] + ", line " + str(i + 1))
                    sys.exit(1)
                self.lexemes.append(res)
    
    def __syntactical_pass(self):
        for line in self.lexemes:
            matches_grammar = False
            rule = -1
            for i in range(len(LINE_GRAMMAR)):
                if line[0][0] == LINE_GRAMMAR[i][0][0]:
                    if line[0][0] == "JUMP" and line[1][0] != LINE_GRAMMAR[i][0][1]:
                        continue
                    else:   
                        matches_grammar = True
                        rule = i
                        break
            
            lexemes = [lexs for (_, lexs) in line]
            if not matches_grammar:
                print(f"In line {lexemes}")
                print("Line must start with a tag name or instruction")
                sys.exit(1)

            tokens = [toks for (toks, _) in line]
            if tokens != LINE_GRAMMAR[rule][0]:
                print(f"In line {lexemes}")
                print(f"Expected line format: {LINE_GRAMMAR[rule][1]}")
                sys.exit(1)

    def __labels_pass(self):
        # collect labels
        address = 0

        for line in self.lexemes:
            line_start = line[0]

            if line_start[0] == "TAG":
                self.labels[line_start[1]] = address
            else:
                address += 1

    def __immediate_to_dec(self, immediate) -> int:
        if len(immediate) == 1:
            return int(immediate)
        
        if immediate[1] == 'b':
            return int(immediate, 2)
        
        return int(immediate, 16)

    def __encode_instruction(self, instruction, operands):
        instruction_code = {
            "ldi": 0, "mov": 1, "sub": 2, "xor": 2,
            "jmp": 3, "jnz": 3, "jle": 3, "jge": 3,
            "kcl": 4,
            "nop": 5
        }
        register_code = {
            "h0": 0, "h1": 1, "h2": 2, "h3": 3, "rm": 4, "rr": 5, "rj": 6,
            "ro": 7, "s2": 8, "s1p": 9, "rx": 10, "s1": 11
        }
        jump_type = {
            "jmp": 0, "jnz": 1,
            "jle": 2, "jge": 3
        }
        op_type = {
            "sub": 0,
            "xor": 1
        }

        bin_code = instruction_code[instruction] << 13
        if instruction == "nop":
            bin_code = 40960
        elif instruction == "kcl":
            bin_code = 36864
        elif instruction == "sub" or instruction == "xor":
            bin_code |= (op_type[instruction] << 8)
        elif instruction[0] == 'j':
            if operands[0][0] == '.':
                bin_code |= (jump_type[instruction] << 8) | self.labels[operands[0]]
            else:
                imm = self.__immediate_to_dec(operands[0])
                bin_code |= (jump_type[instruction] << 8) | imm
        elif instruction == "mov":
            bin_code |= (register_code[operands[0]] << 10) | (register_code[operands[1]] << 4)
        else:
            imm = self.__immediate_to_dec(operands[1])
            bin_code |= (register_code[operands[0]] << 10) | imm

        machine_code = hex(bin_code)[2:]
        machine_code = (4 - len(machine_code)) * "0" + machine_code
        return machine_code

    def __encoding_pass(self):
        # generate machine code
        for line in self.lexemes:
            if line[0][0] == "TAG":
                continue

            instruction = line[0][1]
            operands = [pair[1] for pair in line[1:]]
            if line[0][0] == "JUMP" and operands[0] not in self.labels:
                print(f"In line {[lexs for (_, lexs) in line]}")
                print(f"Label {operands[0]} not defined")
                sys.exit(1)

            code = self.__encode_instruction(instruction, operands)
            self.machine_code.append(code)
        
    def __output_code(self):
        written_per_line = 0
        crt_line = 0
        with open(self.output, "w") as f:
            f.write("v3.0 hex words addressed\n")
            for code in self.machine_code:
                if written_per_line == 0:
                    if crt_line == 0:
                        f.write("00: ")
                    else:
                        f.write(hex(16 * crt_line)[2:] + ": ")
                f.write(code + " ")
                written_per_line += 1
                if written_per_line == 16:
                    written_per_line = 0
                    crt_line += 1
                    f.write("\n")

            while crt_line < 16:
                while written_per_line != 16:
                    if written_per_line == 0:
                        f.write(hex(16 * crt_line)[2:] + ": ")
                    f.write("0000 ")
                    written_per_line += 1
            
                if written_per_line == 16:
                    written_per_line = 0
                    crt_line += 1
                    f.write("\n")

        print(f"Assembled {len(self.machine_code)} instructions.")
        print(f"Output written to {self.output}")
    
def main():
    if len(sys.argv) != 3:
        print("Usage: python assembler.py input.txt output")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    assembler = Assembler(input_file, output_file)
    assembler.run()

if __name__ == "__main__":
    main()
