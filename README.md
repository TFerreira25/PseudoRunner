begin
declação de variaveis

# ⚙️ PseudoRunner

### Executable Pseudocode Interpreter 🔥

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-MIT-green)
![Made in Portugal](https://img.shields.io/badge/Made%20in-Portugal-red?style=flat&logo=portugal)

---

**PseudoRunner** is an **academic-style pseudocode interpreter** built in **Python 3**. It executes instructions written in a simple, educational pseudocode format, such as `Begin`, `If`, `While`, `Display`, and more.

Perfect for learning or teaching programming logic without converting pseudocode to another language.

---

## 🧩 Features

- Block structure: `begin ... end`
- Variable declaration and assignment: `set ... to ...`
- Input and output: `prompt`, `read`, `display`
- Conditional statements: `if`, `else if`, `else`, `endif`
- Loops: `while`, `for`
- Logical operators: `and`, `or`
- Relational operators: `>`, `<`, `equals`, `<>`, `>=`, `<=`
- Modulo operator: `Mod`
- Interactive execution via terminal
- Support for expressions with parentheses

---

## 🚀 Installation

### Requirements

- **Python 3**

Check if Python is installed:

```bash
python3 --version
```

Clone the repository:

```bash
git clone https://github.com/<your-username>/pseudoRunner.git
cd pseudoRunner
```

Project structure:

```
pseudoRunner/
│
├── interpreter.py   # Interpreter core
├── exercises/       # Example exercises (not tracked by Git)
└── README.md
```

---

## 📖 Syntax Overview

### Program Block

```pseudo
begin
  ...instructions...
end
```

### Variable Declaration & Assignment

```pseudo
set x to 0
set sum to a + b
set average to (a + b + c) / 3
```

### Supported Operators

- `+`, `-`, `*`, `/`, `%` (or `Mod`)

### Input & Output

```pseudo
prompt "Enter a number:"
read number
display "Number entered:", number
```

- `prompt` → shows text on screen
- `read` → reads user input
- `display` → prints text and values

### Conditionals

```pseudo
if a > b then
  display "a is greater"
else if b > a then
  display "b is greater"
else
  display "Equal"
endif
```

| Operator    | Meaning               | Example                    |
| ----------- | --------------------- | -------------------------- |
| `>`         | Greater than          | `if x > 5 then`            |
| `<`         | Less than             | `if x < 3 then`            |
| `equals`    | Equal                 | `if x equals 10 then`      |
| `<>`        | Not equal             | `if x <> 0 then`           |
| `>=` / `<=` | Greater/Less or equal | `if x >= 2 then`           |
| `and`, `or` | Logical operators     | `(a > 0) and (b < 5)`      |
| `Mod`       | Modulo (remainder)    | `if x Mod 2 equals 0 then` |

### While Loop

```pseudo
set x to 0
while (x < 5) then
  display "x =", x
  set x to x + 1
endwhile
```

### For Loop

```pseudo
for i from 1 to 5 do
  display "i =", i
endfor
```

---

## 🏃‍♂️ Try It

To run an exercise:

```bash
python3 interpreter.py exercises/yourExercise.pseudo
```

---

## 📂 Example Exercises

See the `exercises/` folder for ready-to-run pseudocode samples.

---

## 📄 License

MIT

---

## 🔧 Roadmap

- [ ] Functions & Procedures support
- [ ] Arrays and lists
- [ ] `repeat ... until` loop structure
- [ ] Native comments (`#`, `//`)
- [ ] Improved error messages
- [ ] Export results to file

---

## 👨‍💻 Author

[Tiago Gomes](https://www.linkedin.com/in/tiago-ferreira-gomes-dev/)
