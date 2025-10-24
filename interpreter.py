import sys
import re

# Error mapping for user-friendly messages
ERROR_MAP = {
    "Variável usada antes de ser definida.": "Variable used before being defined.",
    "endwhile sem while correspondente.": "'endwhile' without matching 'while'.",
    "endfor sem for correspondente.": "'endfor' without matching 'for'.",
    "while sem fim correspondente (endwhile/endfor).": "'while' block missing 'endwhile'.",
    "for sem fim correspondente (endwhile/endfor).": "'for' block missing 'endfor'.",
    "Linha inválida (Set)": "Invalid 'set' statement.",
    "Instrução desconhecida": "Unknown instruction.",
    "Sintaxe IF inválida": "Invalid IF syntax.",
    "else if sem IF correspondente.": "'else if' without matching 'if'.",
    "Sintaxe ELSE IF inválida": "Invalid ELSE IF syntax.",
    "else sem IF correspondente.": "'else' without matching 'if'.",
    "endif sem IF correspondente.": "'endif' without matching 'if'.",
    "Sintaxe WHILE inválida": "Invalid WHILE syntax.",
    "Sintaxe FOR inválida": "Invalid FOR syntax."
}

def map_error_message(msg):
    for key in ERROR_MAP:
        if key in msg:
            return ERROR_MAP[key] + f" (Details: {msg})"
    return msg

# -------------------------
# Helpers
# -------------------------

def is_number(val):
    try:
        if "." in val:
            return float(val)
        return int(val)
    except:
        return None

def tokenize_display_args(s):
    args = []
    current = ""
    inside_quotes = False
    bracket_level = 0
    for ch in s:
        if ch == '"':
            inside_quotes = not inside_quotes
            current += ch
        elif ch == '[':
            bracket_level += 1
            current += ch
        elif ch == ']':
            bracket_level -= 1
            current += ch
        elif ch == ',' and not inside_quotes and bracket_level == 0:
            args.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip() != "" or s.strip() != "":
        args.append(current.strip())
    return args

def to_python_expr(expr, variables):

    rep = expr.strip()

    # Pre-process array accesses: replace var[expr] with their value
    def array_access_replacer(match):
        varname = match.group(1)
        idx_expr = match.group(2)
        idx_val = eval(to_python_expr(idx_expr, variables), {"__builtins__": {}})
        if varname not in variables:
            raise Exception(map_error_message(f"Variável '{varname}' usada antes de ser definida."))
        arr = variables[varname]
        if not isinstance(arr, list):
            raise Exception(f"'{varname}' is not an array.")
        if not isinstance(idx_val, int) or idx_val < 0 or idx_val >= len(arr):
            raise Exception(f"Index {idx_val} out of bounds for array '{varname}'.")
        return str(arr[idx_val])

    # This regex matches var[expr] where expr can be anything except a closing bracket
    rep = re.sub(r'([A-Za-z_]\w*)\[([^\]]+)\]', array_access_replacer, rep)

    rep = re.sub(r"\b-gt\b", ">", rep)
    rep = re.sub(r"\bgt\b", ">", rep)
    rep = rep.replace(">=", ">=")

    rep = re.sub(r"\b-lt\b", "<", rep)
    rep = re.sub(r"\blt\b", "<", rep)
    rep = rep.replace("<=", "<=")

    rep = re.sub(r"\bequals\b", "==", rep)
    rep = rep.replace("<>", "!=")

    rep = re.sub(r"\band\b", " and ", rep)
    rep = re.sub(r"\bor\b", " or ", rep)

    rep = re.sub(r"\bMod\b", "%", rep, flags=re.IGNORECASE)

    rep = rep.replace("==", " == ")
    rep = rep.replace(">=", " >= ")
    rep = rep.replace("<=", " <= ")
    rep = rep.replace("!=", " != ")
    rep = rep.replace(">", " > ")
    rep = rep.replace("<", " < ")
    rep = rep.replace("%", " % ")

    tokens = re.findall(r'"[^"]*"|\(|\)|[A-Za-z_]\w*|\d+(\.\d+)?|==|>=|<=|!=|>|<|%|\+|-|\*|/|and|or', rep)
    # o regex acima mete grupos, vamos limpar:
    cleaned = []
    for t in tokens:
        if isinstance(t, tuple):
            t = "".join(t)
        if t is None:
            continue

    tokens = re.findall(r'"[^"]*"|\(|\)|[A-Za-z_]\w*|\d+\.\d+|\d+|==|>=|<=|!=|>|<|%|\+|-|\*|/|and|or', rep)

    py_expr = ""
    i = 0
    while i < len(tokens):
        t = tokens[i]
        # Array access: var[index] where index can be an expression
        if re.match(r'^[A-Za-z_]\w*$', t):
            if t in ["and", "or"]:
                py_expr += f" {t} "
            elif i+1 < len(tokens) and tokens[i+1] == "[":
                # Find matching closing bracket
                bracket_count = 1
                idx_tokens = []
                j = i+2
                while j < len(tokens):
                    if tokens[j] == "[":
                        bracket_count += 1
                    elif tokens[j] == "]":
                        bracket_count -= 1
                        if bracket_count == 0:
                            break
                    idx_tokens.append(tokens[j])
                    j += 1
                if bracket_count != 0:
                    raise Exception(f"Unmatched [ in array access for {t}")
                idx_expr = "".join(idx_tokens)
                # Debug: print('Array index expr:', idx_expr)
                idx_val = eval(to_python_expr(idx_expr, variables), {"__builtins__": {}})
                if t not in variables:
                    raise Exception(map_error_message(f"Variável '{t}' usada antes de ser definida."))
                arr = variables[t]
                if not isinstance(arr, list):
                    raise Exception(f"'{t}' is not an array.")
                if not isinstance(idx_val, int) or idx_val < 0 or idx_val >= len(arr):
                    raise Exception(f"Index {idx_val} out of bounds for array '{t}'.")
                py_expr += str(arr[idx_val])
                i = j+1
                continue
            else:
                if t not in variables:
                    raise Exception(map_error_message(f"Variável '{t}' usada antes de ser definida."))
                py_expr += str(variables[t])
        else:
            py_expr += t
        i += 1
    return py_expr

# -------------------------
# Interpretador
# -------------------------

class Interpreter:
    def __init__(self, lines):
        self.lines = [line.rstrip() for line in lines]
        self.ip = 0
        self.vars = {}
        self.stack = []  # para while / for / if
        self.block_map = self._precompute_blocks()

    def _precompute_blocks(self):
        stack_tmp = []
        mapping = {}

        for idx, raw in enumerate(self.lines):
            line_up = raw.strip().lower()

            if line_up.startswith("while "):
                stack_tmp.append(("while", idx))
            elif line_up.startswith("for "):
                stack_tmp.append(("for", idx))
            elif line_up == "endif":
                pass
            elif line_up == "endwhile":
                if not stack_tmp or stack_tmp[-1][0] != "while":
                    raise Exception(map_error_message("endwhile sem while correspondente."))
                _, start_idx = stack_tmp.pop()
                mapping[start_idx] = idx
            elif line_up == "endfor":
                if not stack_tmp or stack_tmp[-1][0] != "for":
                    raise Exception(map_error_message("endfor sem for correspondente."))
                _, start_idx = stack_tmp.pop()
                mapping[start_idx] = idx

        for kind, start in stack_tmp:
            raise Exception(map_error_message(f"{kind} sem fim correspondente (endwhile/endfor). Linha {start+1}."))

        return mapping

    def run(self):
        while self.ip < len(self.lines):
            raw = self.lines[self.ip].strip()

            # Ignore empty lines
            if raw == "":
                self.ip += 1
                continue

            # Ignore comments (# or //)
            if raw.startswith("#") or raw.startswith("//"):
                self.ip += 1
                continue

            lower = raw.lower()

            if lower == "begin":
                self.ip += 1
                continue
            if lower == "end":
                break

            if lower.startswith("prompt "):
                msg = raw[6:].strip()
                msg = msg.strip()
                if msg.startswith('"') and msg.endswith('"'):
                    msg = msg[1:-1]
                print(msg)
                self.ip += 1
                continue

            if lower.startswith("read "):
                varname = raw[5:].strip()
                user_in = input("> ")

                maybe_num = is_number(user_in)
                if maybe_num is None:
                    self.vars[varname] = user_in
                else:
                    self.vars[varname] = maybe_num

                self.ip += 1
                continue

            if lower.startswith("display "):
                args_part = raw[7:].strip()
                parts = tokenize_display_args(args_part)

                output_bits = []
                for part in parts:
                    if part.startswith('"') and part.endswith('"'):
                        output_bits.append(part[1:-1])
                    elif re.match(r'^[A-Za-z_]\w*$', part):
                        # Display variable or array
                        if part in self.vars:
                            val = self.vars[part]
                            output_bits.append(str(val))
                        else:
                            output_bits.append(f"[undefined: {part}]")
                    elif re.match(r'^[A-Za-z_]\w*\[.+\]$', part):
                        # Display array element like arr[i]
                        m_elem = re.match(r'^([A-Za-z_]\w*)\[(.+)\]$', part)
                        if m_elem:
                            varname = m_elem.group(1)
                            idx_expr = m_elem.group(2)
                            idx_py = to_python_expr(idx_expr, self.vars)
                            idx = eval(idx_py, {"__builtins__": {}})
                            if varname in self.vars and isinstance(self.vars[varname], list):
                                arr = self.vars[varname]
                                if isinstance(idx, int) and 0 <= idx < len(arr):
                                    output_bits.append(str(arr[idx]))
                                else:
                                    output_bits.append(f"[out of bounds: {varname}[{idx}]]")
                            else:
                                output_bits.append(f"[not array: {varname}]")
                        else:
                            output_bits.append(f"[invalid array syntax: {part}]")
                    else:
                        expr_py = to_python_expr(part, self.vars)
                        val = eval(expr_py, {"__builtins__": {}})
                        output_bits.append(str(val))

                print(" ".join(output_bits))
                self.ip += 1
                continue

            if lower.startswith("set "):
                # Array element assignment: set arr[index] to value (index can be variable or expression)
                m_elem = re.match(r"set\s+([A-Za-z_]\w*)\[(.+)\]\s+to\s+(.+)", raw, re.IGNORECASE)
                if m_elem:
                    varname = m_elem.group(1)
                    idx_expr = m_elem.group(2)
                    expr = m_elem.group(3)
                    idx_py = to_python_expr(idx_expr, self.vars)
                    idx = eval(idx_py, {"__builtins__": {}})
                    expr_py = to_python_expr(expr, self.vars)
                    val = eval(expr_py, {"__builtins__": {}})
                    if varname not in self.vars:
                        raise Exception(map_error_message(f"Variável '{varname}' usada antes de ser definida."))
                    arr = self.vars[varname]
                    if not isinstance(arr, list):
                        raise Exception(f"'{varname}' is not an array.")
                    if not isinstance(idx, int) or idx < 0 or idx >= len(arr):
                        raise Exception(f"Index {idx} out of bounds for array '{varname}'.")
                    arr[idx] = val
                    self.ip += 1
                    continue
                # Array declaration: set arr to [1, 2, 3]
                m_arr = re.match(r"set\s+([A-Za-z_]\w*)\s+to\s+\[(.*)\]", raw, re.IGNORECASE)
                if m_arr:
                    varname = m_arr.group(1)
                    items = m_arr.group(2)
                    # Split items by comma, handle numbers and strings
                    arr = []
                    for item in re.split(r",", items):
                        item = item.strip()
                        if item.startswith('"') and item.endswith('"'):
                            arr.append(item[1:-1])
                        else:
                            num = is_number(item)
                            arr.append(num if num is not None else item)
                    self.vars[varname] = arr
                    self.ip += 1
                    continue
                # Regular variable assignment
                m = re.match(r"set\s+([A-Za-z_]\w*)\s+to\s+(.+)", raw, re.IGNORECASE)
                if not m:
                    raise Exception(map_error_message(f"Linha inválida (Set): {raw}"))
                varname = m.group(1)
                expr = m.group(2)

                expr_py = to_python_expr(expr, self.vars)
                val = eval(expr_py, {"__builtins__": {}})
                self.vars[varname] = val

                self.ip += 1
                continue

            if lower.startswith("if "):

                if lower.startswith("else if "):
                    self._handle_else_if(raw)
                else:
                    self._handle_if(raw)
                continue

            if lower.startswith("else if "):
                self._handle_else_if(raw)
                continue

            if lower == "else":
                self._handle_else()
                continue

            if lower == "endif":
                self._handle_endif()
                continue

            if lower.startswith("while "):
                self._handle_while(raw)
                continue

            if lower == "endwhile":
                self._handle_endwhile()
                continue

            if lower.startswith("for "):
                self._handle_for(raw)
                continue

            if lower == "endfor":
                self._handle_endfor()
                continue

            raise Exception(map_error_message(f"Instrução desconhecida na linha {self.ip+1}: {raw}"))

    # -------------- IF / ELSE IF / ELSE / ENDIF ----------------

    def _handle_if(self, raw):
        m = re.match(r"if\s+(.+?)\s+then\s*$", raw, re.IGNORECASE)
        if not m:
            raise Exception(map_error_message(f"Sintaxe IF inválida: {raw}"))

        cond_text = m.group(1)
        cond_py = to_python_expr(cond_text, self.vars)
        result = eval(cond_py, {"__builtins__": {}})

        self.stack.append(["if", bool(result), bool(result)])

        self.ip += 1

        if not result:
            self._skip_if_block_until_branch()

    def _handle_else_if(self, raw):
        if not self.stack or self.stack[-1][0] != "if":
            raise Exception(map_error_message("else if sem IF correspondente."))
        block = self.stack[-1]

        m = re.match(r"else\s+if\s+(.+?)\s+then\s*$", raw, re.IGNORECASE)
        if not m:
            raise Exception(map_error_message(f"Sintaxe ELSE IF inválida: {raw}"))

        cond_text = m.group(1)
        cond_py = to_python_expr(cond_text, self.vars)
        result = eval(cond_py, {"__builtins__": {}})

        if block[1] is True:
            block[2] = False
        else:
            block[1] = bool(result)
            block[2] = bool(result)

        self.ip += 1

        if not block[2]:
            self._skip_if_block_until_branch()

    def _handle_else(self):
        if not self.stack or self.stack[-1][0] != "if":
            raise Exception(map_error_message("else sem IF correspondente."))
        block = self.stack[-1]

        if block[1] is True:
            block[2] = False
        else:
            block[1] = True
            block[2] = True

        self.ip += 1

        if not block[2]:
            self._skip_if_block_until_branch()

    def _handle_endif(self):
        if not self.stack or self.stack[-1][0] != "if":
            raise Exception(map_error_message("endif sem IF correspondente."))
        self.stack.pop()
        self.ip += 1

    def _skip_if_block_until_branch(self):
        while self.ip < len(self.lines):
            peek = self.lines[self.ip].strip().lower()

            if peek.startswith("else if "):
                # vamos deixar o handler else_if tratar isto
                break
            if peek == "else":
                break
            if peek == "endif":
                break
            self.ip += 1

    # -------------- WHILE / ENDWHILE ----------------

    def _handle_while(self, raw):
        m = re.match(r"while\s+(.+?)\s+(do|then)\s*$", raw, re.IGNORECASE)
        if not m:
            m2 = re.match(r"while\s+(.+?)\s*$", raw, re.IGNORECASE)
            if not m2:
                raise Exception(map_error_message(f"Sintaxe WHILE inválida: {raw}"))
            cond_text = m2.group(1)
        else:
            cond_text = m.group(1)

        cond_py = to_python_expr(cond_text, self.vars)
        cond_val = eval(cond_py, {"__builtins__": {}})

        if cond_val:
            self.stack.append(["while", self.ip, cond_text])
            self.ip += 1
        else:
            end_ip = self.block_map[self.ip]
            self.ip = end_ip + 1

    def _handle_endwhile(self):
        if not self.stack or self.stack[-1][0] != "while":
            raise Exception("endwhile sem while correspondente.")

        kind, while_line, cond_text = self.stack[-1]
        cond_py = to_python_expr(cond_text, self.vars)
        cond_val = eval(cond_py, {"__builtins__": {}})

        if cond_val:
            self.ip = while_line + 1
        else:
            self.stack.pop()
            self.ip += 1

    # -------------- FOR / ENDFOR ----------------

    def _handle_for(self, raw):
        m = re.match(
            r"for\s+([A-Za-z_]\w*)\s+from\s+(.+?)\s+to\s+(.+?)\s+do\s*$",
            raw,
            re.IGNORECASE
        )
        if not m:
            raise Exception(map_error_message(f"Sintaxe FOR inválida: {raw}"))

        varname = m.group(1)
        start_expr = m.group(2)
        end_expr = m.group(3)

        start_val = eval(to_python_expr(start_expr, self.vars), {"__builtins__": {}})
        end_val = eval(to_python_expr(end_expr, self.vars), {"__builtins__": {}})

        self.vars[varname] = start_val

        self.stack.append(["for", self.ip, varname, start_val, end_val])

        if start_val > end_val:
            end_ip = self.block_map[self.ip]
            self.stack.pop()
            self.ip = end_ip + 1
        else:
            self.ip += 1

    def _handle_endfor(self):
        if not self.stack or self.stack[-1][0] != "for":
            raise Exception(map_error_message("endfor sem for correspondente."))

        kind, for_line, varname, current_val, end_val = self.stack[-1]

        current_val += 1
        if current_val <= end_val:
            self.stack[-1][3] = current_val
            self.vars[varname] = current_val
            self.ip = for_line + 1
        else:
            self.stack.pop()
            self.ip += 1


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 interpreter.py programa.pseudo")
        sys.exit(1)

    filename = sys.argv[1]

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    interp = Interpreter(lines)
    interp.run()

if __name__ == "__main__":
    main()
