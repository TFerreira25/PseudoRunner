# ⚙️ PseudoRunner JS

### Executable Pseudocode Interpreter 🔥

![Node.js](https://img.shields.io/badge/Node.js-18%2B-green?logo=node.js)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-MIT-blue)
![Made in Portugal](https://img.shields.io/badge/Made%20in-Portugal-red?style=flat&logo=portugal)

---

**PseudoRunner JS** is an **academic-style pseudocode interpreter** built with **Node.js**.  
It executes simple pseudocode instructions such as `Begin`, `If`, `While`, `Display`, etc. — perfect for learning or teaching programming logic without converting pseudocode into another language.

---

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
- Interactive terminal execution  
- Expression and array support (`arr[0]`, `arr[i+1]`, etc.)

---
## 🚀 Installation

### Requirements

- **Node.js 18+**
- **npm**

Check if Node.js is installed:

```bash
node -v
```

---

### Clone the repository

```bash
git clone https://github.com/<your-username>/pseudoRunner-js.git
cd pseudoRunner-js
```

### Install dependencies

```bash
npm install
```
    

---

## 📖 Syntax Overview

### Project structure

```
pseudoRunner/
│
├── interpreter.js   # Core interpreter
├── exercises/       # Example pseudocode files (not tracked by Git)
└── README.md
```

### Program Block

```pseudo
begin
  ...instructions...
end
```
### Variable Declaration & Assignment

```pseudo
set x to 0
```
 
---
### Input & Output

- `prompt` → prints text to the terminal  
- `read` → reads user input  
- `display` → prints text and variable values  

---

### Conditionals

| Operator    | Meaning               | Example                     |
| ------------ | -------------------- | ---------------------------- |
| `>` / `gt`         | Greater than         | `if x > 5 then`             |
| `<` / `lt`         | Less than            | `if x < 3 then`             |
| `equals` / `==`     | Equal to             | `if x equals 10 then`       |
| `<>`         | Not equal to         | `if x <> 0 then`            |
| `>=` / `<=`  | Greater/Less or equal| `if x >= 2 then`            |
| `and`, `or`  | Logical operators    | `(a > 0) and (b < 5)`       |
| `Mod`        | Modulo (remainder)   | `if x Mod 2 equals 0 then`  |

---

## 🏃‍♂️ Running the Interpreter

To run a pseudocode program:

```bash
node interpreter.js exercises/yourProgram.pseudo
```

Example:

```bash
node interpreter.js exercises/factorial.pseudo
```

---

## 📂 Example Programs

Check the `exercises/` folder for ready-to-run pseudocode examples.

---
## Demonstração

Insira um gif ou um link de alguma demonstração

### Input & Output

```pseudo
prompt "Enter a number:"
read number
display "You entered:", number
```
---
### Conditionals

```pseudo
if a > b then
  display "a is greater"
else if b > a then
  display "b is greater"
else
  display "They are equal"
endif
```
---

### While Loop

```pseudo
set x to 0
while (x < 5) then
  display "x =", x
  set x to x + 1
endwhile
```

---

### For Loop

```pseudo
for i from 1 to 5 do
  display "i =", i
endfor
```

---

### Arrays

```pseudo
set nums to [1, 2, 3, 4]
display nums[0]
set nums[2] to 10
```

---
## License

[MIT](https://choosealicense.com/licenses/mit/)
---

## 🔧 Roadmap

- [x] Full support for `if`, `for`, `while`
- [x] Arrays and expressions
- [ ] Functions & Procedures
- [ ] `repeat ... until` loop structure
- [ ] Better error messages
- [ ] Export output to file

---

## 👨‍💻 Author

LinkedIn: **[Tiago Gomes](https://www.linkedin.com/in/tiago-ferreira-gomes-dev/)**  
Github: **[TFerreira25](https://github.com/TFerreira25)**
