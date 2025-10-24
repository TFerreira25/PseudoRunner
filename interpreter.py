import sys
import re

# -------------------------
# Helpers
# -------------------------

def is_number(val):
    # tenta converter para int ou float
    try:
        if "." in val:
            return float(val)
        return int(val)
    except:
        return None

def tokenize_display_args(s):
    # separa por vírgulas, mas respeita aspas
    args = []
    current = ""
    inside_quotes = False
    for ch in s:
        if ch == '"':
            inside_quotes = not inside_quotes
            current += ch
        elif ch == ',' and not inside_quotes:
            args.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip() != "" or s.strip() != "":
        args.append(current.strip())
    return args

def to_python_expr(expr, variables):
    # Converte algo tipo:
    #   (num -gt num2) and (num -gt num3)
    #   number Mod 2
    #   count <= 5
    #   num equals 0
    #   num <> num2
    #
    # para uma expressão python válida

    # substituir operadores por python
    rep = expr.strip()

    # normalizar espaços
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

    # Mod → %
    rep = re.sub(r"\bMod\b", "%", rep, flags=re.IGNORECASE)

    # garantir espaços nos operadores principais
    rep = rep.replace("==", " == ")
    rep = rep.replace(">=", " >= ")
    rep = rep.replace("<=", " <= ")
    rep = rep.replace("!=", " != ")
    rep = rep.replace(">", " > ")
    rep = rep.replace("<", " < ")
    rep = rep.replace("%", " % ")

    # agora vamos partir em tokens e trocar variáveis por valor
    tokens = re.findall(r'"[^"]*"|\(|\)|[A-Za-z_]\w*|\d+(\.\d+)?|==|>=|<=|!=|>|<|%|\+|-|\*|/|and|or', rep)
    # o regex acima mete grupos, vamos limpar:
    cleaned = []
    for t in tokens:
        if isinstance(t, tuple):
            t = "".join(t)
        if t is None:
            continue

    # melhor: usar findall sem grupo capturador:
    tokens = re.findall(r'"[^"]*"|\(|\)|[A-Za-z_]\w*|\d+\.\d+|\d+|==|>=|<=|!=|>|<|%|\+|-|\*|/|and|or', rep)

    py_expr = ""
    for t in tokens:
        if re.match(r'^[A-Za-z_]\w*$', t):
            # pode ser variável ou palavra reservada (and/or)
            if t in ["and", "or"]:
                py_expr += f" {t} "
            else:
                # variável
                if t not in variables:
                    raise Exception(f"Variável '{t}' usada antes de ser definida.")
                py_expr += str(variables[t])
        else:
            py_expr += t
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
        # vamos mapear blocos tipo While->EndWhile e For->EndFor e If/endif?:
        # While e For precisamos saber saltar quando falha condição
        stack_tmp = []
        mapping = {}

        for idx, raw in enumerate(self.lines):
            line_up = raw.strip().lower()

            if line_up.startswith("while "):
                stack_tmp.append(("while", idx))
            elif line_up.startswith("for "):
                stack_tmp.append(("for", idx))
            elif line_up == "endif":
                # if não precisa map para salto condicional directo (vamos gerir via stack runtime)
                pass
            elif line_up == "endwhile":
                # última coisa tem de ser um while
                if not stack_tmp or stack_tmp[-1][0] != "while":
                    raise Exception("endwhile sem while correspondente.")
                _, start_idx = stack_tmp.pop()
                mapping[start_idx] = idx
            elif line_up == "endfor":
                if not stack_tmp or stack_tmp[-1][0] != "for":
                    raise Exception("endfor sem for correspondente.")
                _, start_idx = stack_tmp.pop()
                mapping[start_idx] = idx

        # se sobrou algum while/for sem fechar
        for kind, start in stack_tmp:
            raise Exception(f"{kind} sem fim correspondente (endwhile/endfor). Linha {start+1}.")

        return mapping

    def run(self):
        # corre até acabar ou bater em "end"
        while self.ip < len(self.lines):
            raw = self.lines[self.ip].strip()

            # ignorar linhas vazias
            if raw == "":
                self.ip += 1
                continue

            lower = raw.lower()

            # Begin / End
            if lower == "begin":
                self.ip += 1
                continue
            if lower == "end":
                break

            # Prompt "msg"
            if lower.startswith("prompt "):
                msg = raw[6:].strip()
                # tirar aspas se tiver
                msg = msg.strip()
                if msg.startswith('"') and msg.endswith('"'):
                    msg = msg[1:-1]
                print(msg)
                self.ip += 1
                continue

            # Read var
            if lower.startswith("read "):
                varname = raw[5:].strip()
                user_in = input("> ")

                # tentar número, se não der fica string
                maybe_num = is_number(user_in)
                if maybe_num is None:
                    self.vars[varname] = user_in
                else:
                    self.vars[varname] = maybe_num

                self.ip += 1
                continue

            # Display ...
            if lower.startswith("display "):
                args_part = raw[7:].strip()
                parts = tokenize_display_args(args_part)

                output_bits = []
                for part in parts:
                    if part.startswith('"') and part.endswith('"'):
                        output_bits.append(part[1:-1])
                    else:
                        # pode ser var ou expressão
                        expr_py = to_python_expr(part, self.vars)
                        val = eval(expr_py, {"__builtins__": {}})
                        output_bits.append(str(val))

                print(" ".join(output_bits))
                self.ip += 1
                continue

            # Set var to expr
            if lower.startswith("set "):
                # formato: Set count to count + 1
                m = re.match(r"set\s+([A-Za-z_]\w*)\s+to\s+(.+)", raw, re.IGNORECASE)
                if not m:
                    raise Exception(f"Linha inválida (Set): {raw}")
                varname = m.group(1)
                expr = m.group(2)

                expr_py = to_python_expr(expr, self.vars)
                val = eval(expr_py, {"__builtins__": {}})
                self.vars[varname] = val

                self.ip += 1
                continue

            # If ... then
            if lower.startswith("if "):
                # suporta "if cond then"
                # e também "else if cond then"
                # mas "else if" vai cair aqui mais à frente? não, vamos apanhar else if antes
                if lower.startswith("else if "):
                    # isto só corre se o último IF chain ainda está aberto e a(s) anterior(es) não correram
                    # se já correu uma branch, saltamos este bloco
                    self._handle_else_if(raw)
                else:
                    self._handle_if(raw)
                continue

            # else if ... then
            if lower.startswith("else if "):
                self._handle_else_if(raw)
                continue

            # else
            if lower == "else":
                self._handle_else()
                continue

            # endif
            if lower == "endif":
                self._handle_endif()
                continue

            # While cond do  /  While (cond) then
            if lower.startswith("while "):
                self._handle_while(raw)
                continue

            if lower == "endwhile":
                self._handle_endwhile()
                continue

            # For i from 1 to 5 do
            if lower.startswith("for "):
                self._handle_for(raw)
                continue

            if lower == "endfor":
                self._handle_endfor()
                continue

            raise Exception(f"Instrução desconhecida na linha {self.ip+1}: {raw}")

    # -------------- IF / ELSE IF / ELSE / ENDIF ----------------

    def _handle_if(self, raw):
        # If <cond> then
        m = re.match(r"if\s+(.+?)\s+then\s*$", raw, re.IGNORECASE)
        if not m:
            raise Exception(f"Sintaxe IF inválida: {raw}")

        cond_text = m.group(1)
        cond_py = to_python_expr(cond_text, self.vars)
        result = eval(cond_py, {"__builtins__": {}})

        # guardamos no stack o estado do bloco if atual:
        # ("if", passou_algum_branch, estou_a_executar)
        self.stack.append(["if", bool(result), bool(result)])

        self.ip += 1

        # se não estamos a executar este ramo, vamos saltar linhas até encontrarmos:
        # - else if ... then
        # - else
        # - endif
        # ou até encontrar um ramo que execute
        if not result:
            self._skip_if_block_until_branch()

    def _handle_else_if(self, raw):
        # else if <cond> then
        if not self.stack or self.stack[-1][0] != "if":
            raise Exception("else if sem IF correspondente.")
        block = self.stack[-1]

        m = re.match(r"else\s+if\s+(.+?)\s+then\s*$", raw, re.IGNORECASE)
        if not m:
            raise Exception(f"Sintaxe ELSE IF inválida: {raw}")

        cond_text = m.group(1)
        cond_py = to_python_expr(cond_text, self.vars)
        result = eval(cond_py, {"__builtins__": {}})

        if block[1] is True:
            # já houve branch executada antes
            block[2] = False
        else:
            # ainda não houve branch executada
            block[1] = bool(result)
            block[2] = bool(result)

        self.ip += 1

        if not block[2]:
            self._skip_if_block_until_branch()

    def _handle_else(self):
        # else
        if not self.stack or self.stack[-1][0] != "if":
            raise Exception("else sem IF correspondente.")
        block = self.stack[-1]

        if block[1] is True:
            # já houve um ramo que correu
            block[2] = False
        else:
            # nenhum ramo correu ainda -> este vai correr
            block[1] = True
            block[2] = True

        self.ip += 1

        if not block[2]:
            self._skip_if_block_until_branch()

    def _handle_endif(self):
        if not self.stack or self.stack[-1][0] != "if":
            raise Exception("endif sem IF correspondente.")
        self.stack.pop()
        self.ip += 1

    def _skip_if_block_until_branch(self):
        # saltar linhas até encontrarmos:
        # - else if ...
        # - else
        # - endif
        # ou até que uma branch seja escolhida
        # MAS: se já estamos em modo "não executar este ramo específico"
        # temos de saltar só este bloco simples, não o if todo.
        # Simplificação: vamos só não executar linhas normais enquanto
        # o topo stack tiver block[2] == False
        while self.ip < len(self.lines):
            peek = self.lines[self.ip].strip().lower()

            if peek.startswith("else if "):
                # vamos deixar o handler else_if tratar isto
                break
            if peek == "else":
                break
            if peek == "endif":
                break

            # se for outra coisa (set, display, etc) e não estamos a executar -> saltar
            # se entrar um while/for aí dentro? honestamente: não suportamos if que abre while/for
            # enquanto estamos a saltar. (Podemos suportar, mas fica muito mais complexo)
            self.ip += 1

    # -------------- WHILE / ENDWHILE ----------------

    def _handle_while(self, raw):
        # While <cond> do
        # ou While (cond) then
        m = re.match(r"while\s+(.+?)\s+(do|then)\s*$", raw, re.IGNORECASE)
        if not m:
            # try sem do/then (tipo While count <= 5)
            m2 = re.match(r"while\s+(.+?)\s*$", raw, re.IGNORECASE)
            if not m2:
                raise Exception(f"Sintaxe WHILE inválida: {raw}")
            cond_text = m2.group(1)
        else:
            cond_text = m.group(1)

        cond_py = to_python_expr(cond_text, self.vars)
        cond_val = eval(cond_py, {"__builtins__": {}})

        if cond_val:
            # corre o corpo
            # stack: ("while", linha_do_while, cond_text)
            self.stack.append(["while", self.ip, cond_text])
            self.ip += 1
        else:
            # saltar para depois do endwhile correspondente
            end_ip = self.block_map[self.ip]
            self.ip = end_ip + 1

    def _handle_endwhile(self):
        if not self.stack or self.stack[-1][0] != "while":
            raise Exception("endwhile sem while correspondente.")

        kind, while_line, cond_text = self.stack[-1]
        cond_py = to_python_expr(cond_text, self.vars)
        cond_val = eval(cond_py, {"__builtins__": {}})

        if cond_val:
            # repetir o loop: volta para depois do while_line
            self.ip = while_line + 1
        else:
            # sair do loop
            self.stack.pop()
            self.ip += 1

    # -------------- FOR / ENDFOR ----------------

    def _handle_for(self, raw):
        # For i from 1 to 5 do
        m = re.match(
            r"for\s+([A-Za-z_]\w*)\s+from\s+(.+?)\s+to\s+(.+?)\s+do\s*$",
            raw,
            re.IGNORECASE
        )
        if not m:
            raise Exception(f"Sintaxe FOR inválida: {raw}")

        varname = m.group(1)
        start_expr = m.group(2)
        end_expr = m.group(3)

        start_val = eval(to_python_expr(start_expr, self.vars), {"__builtins__": {}})
        end_val = eval(to_python_expr(end_expr, self.vars), {"__builtins__": {}})

        # inicializar a variável do loop se ainda não existir
        self.vars[varname] = start_val

        # stack do for:
        # ("for", linhaFor, varname, current, end_val)
        self.stack.append(["for", self.ip, varname, start_val, end_val])

        # se já começou maior que o end -> saltar corpo
        if start_val > end_val:
            end_ip = self.block_map[self.ip]
            self.stack.pop()
            self.ip = end_ip + 1
        else:
            self.ip += 1

    def _handle_endfor(self):
        if not self.stack or self.stack[-1][0] != "for":
            raise Exception("endfor sem for correspondente.")

        kind, for_line, varname, current_val, end_val = self.stack[-1]

        # incrementar
        current_val += 1
        if current_val <= end_val:
            # repetir loop
            self.stack[-1][3] = current_val
            self.vars[varname] = current_val
            self.ip = for_line + 1
        else:
            # sair
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
