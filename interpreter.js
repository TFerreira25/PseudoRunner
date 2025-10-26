const fs = require("fs");

// Error mapping for user-friendly messages
const ERROR_MAP = {
  "Variável usada antes de ser definida.":
    "Variable used before being defined.",
  "endwhile sem while correspondente.": "'endwhile' without matching 'while'.",
  "endfor sem for correspondente.": "'endfor' without matching 'for'.",
  "while sem fim correspondente (endwhile/endfor).":
    "'while' block missing 'endwhile'.",
  "for sem fim correspondente (endwhile/endfor).":
    "'for' block missing 'endfor'.",
  "Linha inválida (Set)": "Invalid 'set' statement.",
  "Instrução desconhecida": "Unknown instruction.",
  "Sintaxe IF inválida": "Invalid IF syntax.",
  "else if sem IF correspondente.": "'else if' without matching 'if'.",
  "Sintaxe ELSE IF inválida": "Invalid ELSE IF syntax.",
  "else sem IF correspondente.": "'else' without matching 'if'.",
  "endif sem IF correspondente.": "'endif' without matching 'if'.",
  "Sintaxe WHILE inválida": "Invalid WHILE syntax.",
  "Sintaxe FOR inválida": "Invalid FOR syntax.",
};

function mapErrorMessage(msg) {
  for (const key of Object.keys(ERROR_MAP)) {
    if (msg.includes(key)) {
      return ERROR_MAP[key] + ` (Details: ${msg})`;
    }
  }
  return msg;
}

// -------------------------
// Helpers
// -------------------------

function isNumber(val) {
  if (typeof val !== "string") return null;
  if (val.includes(".")) {
    const num = parseFloat(val);
    return isNaN(num) ? null : num;
  }
  const num = parseInt(val);
  return isNaN(num) ? null : num;
}

function tokenizeDisplayArgs(s) {
  const args = [];
  let current = "";
  let insideQuotes = false;
  let bracketLevel = 0;

  for (const ch of s) {
    if (ch === '"') {
      insideQuotes = !insideQuotes;
      current += ch;
    } else if (ch === "[") {
      bracketLevel++;
      current += ch;
    } else if (ch === "]") {
      bracketLevel--;
      current += ch;
    } else if (ch === "," && !insideQuotes && bracketLevel === 0) {
      args.push(current.trim());
      current = "";
    } else {
      current += ch;
    }
  }

  if (current.trim() !== "" || s.trim() !== "") {
    args.push(current.trim());
  }
  return args;
}

function toPythonExpr(expr, variables) {
  let rep = expr.trim();

  // Pre-process array accesses: replace var[expr] with their value
  function arrayAccessReplacer(match, varname, idx_expr) {
    const idx_val = eval(toPythonExpr(idx_expr, variables));
    if (!(varname in variables)) {
      throw new Error(
        mapErrorMessage(`Variável '${varname}' usada antes de ser definida.`)
      );
    }
    const arr = variables[varname];
    if (!Array.isArray(arr)) {
      throw new Error(`'${varname}' is not an array.`);
    }
    if (typeof idx_val !== "number" || idx_val < 0 || idx_val >= arr.length) {
      throw new Error(`Index ${idx_val} out of bounds for array '${varname}'.`);
    }
    return String(arr[idx_val]);
  }

  // This regex matches var[expr] where expr can be anything except a closing bracket
  rep = rep.replace(/([A-Za-z_]\w*)\[([^\]]+)\]/g, arrayAccessReplacer);

  rep = rep.replace(/\b-gt\b/g, ">");
  rep = rep.replace(/\bgt\b/g, ">");
  rep = rep.replace(/\b-ge\b/g, ">=");
  rep = rep.replace(/\bge\b/g, ">=");
  rep = rep.replace(/>=/, ">=");

  rep = rep.replace(/\b-lt\b/g, "<");
  rep = rep.replace(/\blt\b/g, "<");
  rep = rep.replace(/\b-le\b/g, "<=");
  rep = rep.replace(/\ble\b/g, "<=");
  rep = rep.replace(/<=/, "<=");
  rep = rep.replace(/\bequals\b/g, "==");
  rep = rep.replace(/<>/, "!=");

  rep = rep.replace(/\band\b/g, "&&");
  rep = rep.replace(/\bor\b/g, "||");

  rep = rep.replace(/\bMod\b/gi, "%");

  // Add spaces around operators for proper parsing
  rep = rep.replace(/([<>]=?|==|!=|%)/g, " $1 ");
  const tokens = [
    ...rep.matchAll(
      /"[^"]*"|\(|\)|[A-Za-z_]\w*|\d+(?:\.\d+)?|==|>=|<=|!=|>|<|%|\+|-|\*|\/|&&|\|\|/g
    ),
  ].map((m) => m[0]);

  let py_expr = "";
  let i = 0;
  while (i < tokens.length) {
    const t = tokens[i];
    if (t.match(/^[A-Za-z_]\w*$/)) {
      if (t === "and") {
        py_expr += " && ";
      } else if (t === "or") {
        py_expr += " || ";
      } else if (i + 1 < tokens.length && tokens[i + 1] === "[") {
        // Find matching closing bracket
        let bracketCount = 1;
        let idx_tokens = [];
        let j = i + 2;
        while (j < tokens.length) {
          if (tokens[j] === "[") bracketCount++;
          else if (tokens[j] === "]") {
            bracketCount--;
            if (bracketCount === 0) break;
          }
          idx_tokens.push(tokens[j]);
          j++;
        }
        if (bracketCount !== 0) {
          throw new Error(`Unmatched [ in array access for ${t}`);
        }
        const idx_expr = idx_tokens.join("");
        const idx_val = eval(toPythonExpr(idx_expr, variables));
        if (!(t in variables)) {
          throw new Error(
            mapErrorMessage(`Variável '${t}' usada antes de ser definida.`)
          );
        }
        const arr = variables[t];
        if (!Array.isArray(arr)) {
          throw new Error(`'${t}' is not an array.`);
        }
        if (
          typeof idx_val !== "number" ||
          idx_val < 0 ||
          idx_val >= arr.length
        ) {
          throw new Error(`Index ${idx_val} out of bounds for array '${t}'.`);
        }
        py_expr += String(arr[idx_val]);
        i = j + 1;
        continue;
      } else {
        if (!(t in variables)) {
          throw new Error(
            mapErrorMessage(`Variável '${t}' usada antes de ser definida.`)
          );
        }
        py_expr += String(variables[t]);
      }
    } else {
      py_expr += t;
    }
    i++;
  }
  return py_expr;
}

class Interpreter {
  constructor(lines) {
    this.lines = lines.map((line) => line.trimEnd());
    this.ip = 0;
    this.vars = {};
    this.stack = []; // para while / for / if
    this.block_map = this._precomputeBlocks();
  }

  _precomputeBlocks() {
    const stack_tmp = [];
    const mapping = {};

    for (let idx = 0; idx < this.lines.length; idx++) {
      const line_up = this.lines[idx].trim().toLowerCase();

      if (line_up.startsWith("while ")) {
        stack_tmp.push(["while", idx]);
      } else if (line_up.startsWith("for ")) {
        stack_tmp.push(["for", idx]);
      } else if (line_up === "endif") {
        // pass
      } else if (line_up === "endwhile") {
        if (
          !stack_tmp.length ||
          stack_tmp[stack_tmp.length - 1][0] !== "while"
        ) {
          throw new Error(
            mapErrorMessage("endwhile sem while correspondente.")
          );
        }
        const [, start_idx] = stack_tmp.pop();
        mapping[start_idx] = idx;
      } else if (line_up === "endfor") {
        if (!stack_tmp.length || stack_tmp[stack_tmp.length - 1][0] !== "for") {
          throw new Error(mapErrorMessage("endfor sem for correspondente."));
        }
        const [, start_idx] = stack_tmp.pop();
        mapping[start_idx] = idx;
      }
    }

    for (const [kind, start] of stack_tmp) {
      throw new Error(
        mapErrorMessage(
          `${kind} sem fim correspondente (endwhile/endfor). Linha ${
            start + 1
          }.`
        )
      );
    }

    return mapping;
  }

  run() {
    while (this.ip < this.lines.length) {
      const raw = this.lines[this.ip].trim();

      // Ignore empty lines
      if (raw === "") {
        this.ip++;
        continue;
      }

      // Ignore comments (# or //)
      if (raw.startsWith("#") || raw.startsWith("//")) {
        this.ip++;
        continue;
      }

      const lower = raw.toLowerCase();

      if (lower === "begin") {
        this.ip++;
        continue;
      }
      if (lower === "end") {
        break;
      }

      if (lower.startsWith("prompt ")) {
        let msg = raw.substring(6).trim();
        msg = msg.trim();
        if (msg.startsWith('"') && msg.endsWith('"')) {
          msg = msg.slice(1, -1);
        }
        console.log(msg);
        this.ip++;
        continue;
      }

      if (lower.startsWith("read ")) {
        const varname = raw.substring(5).trim();
        // In Node.js, synchronous input can be done with:
        const user_in = require("readline-sync").question("> ");

        const maybe_num = isNumber(user_in);
        this.vars[varname] = maybe_num === null ? user_in : maybe_num;

        this.ip++;
        continue;
      }

      if (lower.startsWith("display ")) {
        const args_part = raw.substring(7).trim();
        const parts = tokenizeDisplayArgs(args_part);

        const output_bits = [];
        for (const part of parts) {
          if (part.startsWith('"') && part.endsWith('"')) {
            output_bits.push(part.slice(1, -1));
          } else if (part.match(/^[A-Za-z_]\w*$/)) {
            // Display variable or array
            if (part in this.vars) {
              const val = this.vars[part];
              output_bits.push(String(val));
            } else {
              output_bits.push(`[undefined: ${part}]`);
            }
          } else if (part.match(/^[A-Za-z_]\w*\[.+\]$/)) {
            // Display array element like arr[i]
            const m_elem = part.match(/^([A-Za-z_]\w*)\[(.+)\]$/);
            if (m_elem) {
              const [, varname, idx_expr] = m_elem;
              const idx_py = toPythonExpr(idx_expr, this.vars);
              const idx = eval(idx_py);
              if (varname in this.vars && Array.isArray(this.vars[varname])) {
                const arr = this.vars[varname];
                if (typeof idx === "number" && idx >= 0 && idx < arr.length) {
                  output_bits.push(String(arr[idx]));
                } else {
                  output_bits.push(`[out of bounds: ${varname}[${idx}]]`);
                }
              } else {
                output_bits.push(`[not array: ${varname}]`);
              }
            } else {
              output_bits.push(`[invalid array syntax: ${part}]`);
            }
          } else {
            const expr_py = toPythonExpr(part, this.vars);
            const val = eval(expr_py);
            output_bits.push(String(val));
          }
        }

        console.log(output_bits.join(" "));
        this.ip++;
        continue;
      }

      if (lower.startsWith("set ")) {
        // Array element assignment: set arr[index] to value (index can be variable or expression)
        let m_elem = raw.match(/set\s+([A-Za-z_]\w*)\[(.+)\]\s+to\s+(.+)/i);
        if (m_elem) {
          const [, varname, idx_expr, expr] = m_elem;
          const idx_py = toPythonExpr(idx_expr, this.vars);
          const idx = eval(idx_py);
          const expr_py = toPythonExpr(expr, this.vars);
          const val = eval(expr_py);
          if (!(varname in this.vars)) {
            throw new Error(
              mapErrorMessage(
                `Variável '${varname}' usada antes de ser definida.`
              )
            );
          }
          const arr = this.vars[varname];
          if (!Array.isArray(arr)) {
            throw new Error(`'${varname}' is not an array.`);
          }
          if (typeof idx !== "number" || idx < 0 || idx >= arr.length) {
            throw new Error(
              `Index ${idx} out of bounds for array '${varname}'.`
            );
          }
          arr[idx] = val;
          this.ip++;
          continue;
        }

        // Array declaration: set arr to [1, 2, 3]
        m_elem = raw.match(/set\s+([A-Za-z_]\w*)\s+to\s+\[(.*)\]/i);
        if (m_elem) {
          const [, varname, items] = m_elem;
          // Split items by comma, handle numbers and strings
          const arr = [];
          for (const item of items.split(",")) {
            const trimmed = item.trim();
            if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
              arr.push(trimmed.slice(1, -1));
            } else {
              const num = isNumber(trimmed);
              arr.push(num === null ? trimmed : num);
            }
          }
          this.vars[varname] = arr;
          this.ip++;
          continue;
        }

        // Regular variable assignment
        m_elem = raw.match(/set\s+([A-Za-z_]\w*)\s+to\s+(.+)/i);
        if (!m_elem) {
          throw new Error(mapErrorMessage(`Linha inválida (Set): ${raw}`));
        }
        const [, varname, expr] = m_elem;

        const expr_py = toPythonExpr(expr, this.vars);
        const val = eval(expr_py);
        this.vars[varname] = val;

        this.ip++;
        continue;
      }

      if (lower.startsWith("if ")) {
        if (lower.startsWith("else if ")) {
          this._handleElseIf(raw);
        } else {
          this._handleIf(raw);
        }
        continue;
      }

      if (lower.startsWith("else if ")) {
        this._handleElseIf(raw);
        continue;
      }

      if (lower === "else") {
        this._handleElse();
        continue;
      }

      if (lower === "endif") {
        this._handleEndif();
        continue;
      }

      if (lower.startsWith("while ")) {
        this._handleWhile(raw);
        continue;
      }

      if (lower === "endwhile") {
        this._handleEndwhile();
        continue;
      }

      if (lower.startsWith("for ")) {
        this._handleFor(raw);
        continue;
      }

      if (lower === "endfor") {
        this._handleEndfor();
        continue;
      }

      throw new Error(
        mapErrorMessage(
          `Instrução desconhecida na linha ${this.ip + 1}: ${raw}`
        )
      );
    }
  }

  // -------------- IF / ELSE IF / ELSE / ENDIF ----------------

  _handleIf(raw) {
    const m = raw.match(/if\s+(.+?)\s+then\s*$/i);
    if (!m) {
      throw new Error(mapErrorMessage(`Sintaxe IF inválida: ${raw}`));
    }

    const cond_text = m[1];
    const cond_py = toPythonExpr(cond_text, this.vars);
    const result = eval(cond_py);

    this.stack.push(["if", Boolean(result), Boolean(result)]);

    this.ip++;

    if (!result) {
      this._skipIfBlockUntilBranch();
    }
  }

  _handleElseIf(raw) {
    if (!this.stack.length || this.stack[this.stack.length - 1][0] !== "if") {
      throw new Error(mapErrorMessage("else if sem IF correspondente."));
    }
    const block = this.stack[this.stack.length - 1];

    const m = raw.match(/else\s+if\s+(.+?)\s+then\s*$/i);
    if (!m) {
      throw new Error(mapErrorMessage(`Sintaxe ELSE IF inválida: ${raw}`));
    }

    const cond_text = m[1];
    const cond_py = toPythonExpr(cond_text, this.vars);
    const result = eval(cond_py);

    if (block[1] === true) {
      block[2] = false;
    } else {
      block[1] = Boolean(result);
      block[2] = Boolean(result);
    }

    this.ip++;

    if (!block[2]) {
      this._skipIfBlockUntilBranch();
    }
  }

  _handleElse() {
    if (!this.stack.length || this.stack[this.stack.length - 1][0] !== "if") {
      throw new Error(mapErrorMessage("else sem IF correspondente."));
    }
    const block = this.stack[this.stack.length - 1];

    if (block[1] === true) {
      block[2] = false;
    } else {
      block[1] = true;
      block[2] = true;
    }

    this.ip++;

    if (!block[2]) {
      this._skipIfBlockUntilBranch();
    }
  }

  _handleEndif() {
    if (!this.stack.length || this.stack[this.stack.length - 1][0] !== "if") {
      throw new Error(mapErrorMessage("endif sem IF correspondente."));
    }
    this.stack.pop();
    this.ip++;
  }

  _skipIfBlockUntilBranch() {
    while (this.ip < this.lines.length) {
      const peek = this.lines[this.ip].trim().toLowerCase();

      if (peek.startsWith("else if ") || peek === "else" || peek === "endif") {
        break;
      }
      this.ip++;
    }
  }

  // -------------- WHILE / ENDWHILE ----------------

  _handleWhile(raw) {
    let m = raw.match(/while\s+(.+?)\s+(do|then)\s*$/i);
    if (!m) {
      m = raw.match(/while\s+(.+?)\s*$/i);
      if (!m) {
        throw new Error(mapErrorMessage(`Sintaxe WHILE inválida: ${raw}`));
      }
    }

    const cond_text = m[1];
    const cond_py = toPythonExpr(cond_text, this.vars);
    const cond_val = eval(cond_py);

    if (cond_val) {
      this.stack.push(["while", this.ip, cond_text]);
      this.ip++;
    } else {
      const end_ip = this.block_map[this.ip];
      this.ip = end_ip + 1;
    }
  }

  _handleEndwhile() {
    if (
      !this.stack.length ||
      this.stack[this.stack.length - 1][0] !== "while"
    ) {
      throw new Error("endwhile sem while correspondente.");
    }

    const [, while_line, cond_text] = this.stack[this.stack.length - 1];
    const cond_py = toPythonExpr(cond_text, this.vars);
    const cond_val = eval(cond_py);

    if (cond_val) {
      this.ip = while_line + 1;
    } else {
      this.stack.pop();
      this.ip++;
    }
  }

  // -------------- FOR / ENDFOR ----------------

  _handleFor(raw) {
    const m = raw.match(
      /for\s+([A-Za-z_]\w*)\s+from\s+(.+?)\s+to\s+(.+?)\s+do\s*$/i
    );
    if (!m) {
      throw new Error(mapErrorMessage(`Sintaxe FOR inválida: ${raw}`));
    }

    const [, varname, start_expr, end_expr] = m;

    const start_val = eval(toPythonExpr(start_expr, this.vars));
    const end_val = eval(toPythonExpr(end_expr, this.vars));

    this.vars[varname] = start_val;

    this.stack.push(["for", this.ip, varname, start_val, end_val]);

    if (start_val > end_val) {
      const end_ip = this.block_map[this.ip];
      this.stack.pop();
      this.ip = end_ip + 1;
    } else {
      this.ip++;
    }
  }

  _handleEndfor() {
    if (!this.stack.length || this.stack[this.stack.length - 1][0] !== "for") {
      throw new Error(mapErrorMessage("endfor sem for correspondente."));
    }

    const [, for_line, varname, current_val, end_val] =
      this.stack[this.stack.length - 1];

    const next_val = current_val + 1;
    if (next_val <= end_val) {
      this.stack[this.stack.length - 1][3] = next_val;
      this.vars[varname] = next_val;
      this.ip = for_line + 1;
    } else {
      this.stack.pop();
      this.ip++;
    }
  }
}

// Main
function main() {
  if (process.argv.length < 3) {
    console.log("Usage: node interpreter.js programa.pseudo");
    process.exit(1);
  }

  const filename = process.argv[2];

  try {
    const lines = fs.readFileSync(filename, "utf8").split("\n");
    const interp = new Interpreter(lines);
    interp.run();
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}
