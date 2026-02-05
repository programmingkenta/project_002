---
concepts: [variables, assignment, naming, data-types]
source_repo: learning-programming
description: Understanding variables - how to store and reuse information in your programs. Like labeled boxes that hold values.
understanding_score: null
last_quizzed: null
prerequisites: [your-first-python-program]
created: 30-01-2026
last_updated: 30-01-2026
---

# Variables: Storing Information

In your first program, you printed a message. But what if you want to use that message again? Or change it later? Or do math with numbers?

You need a way to **store** information. That's what variables do.

## What is a Variable?

A variable is a **labeled box** that holds a value.

```
┌─────────────┐
│   "Kenta"   │   ← the value (what's inside)
└─────────────┘
    name          ← the label (the variable name)
```

In Python, you create a variable like this:

```python
name = "Kenta"
```

This says: "Create a box labeled `name` and put the text `Kenta` inside it."

## The `=` Sign Means "Store"

In math, `=` means "equals." In programming, `=` means **"store this value in this variable."**

```python
age = 30
```

This doesn't mean "age equals 30" in the math sense. It means "store the number 30 in a box labeled age."

Read it as: "age **gets** 30" or "age **becomes** 30."

## Using Variables

Once you store a value, you can use the variable name to get it back:

```python
name = "Kenta"
print(name)
```

Output:
```
Kenta
```

Notice: no quotes around `name` in the print. That's because we want the **value inside the box**, not the word "name" itself.

Compare:
```python
print(name)    # Prints: Kenta (the value inside the variable)
print("name")  # Prints: name (literally the word "name")
```

## Why Variables Matter for Your 3D City

Imagine building your city:

```python
building_height = 50
building_width = 20
building_color = "blue"
number_of_windows = 12

print("Building a tower that is")
print(building_height)
print("meters tall")
```

Variables let you:
- **Store** building properties
- **Reuse** values without retyping them
- **Change** values in one place (update `building_height` once, it updates everywhere)

## Variable Naming Rules

You choose the variable name. But there are rules:

**Must follow:**
- Start with a letter or underscore (not a number)
- Only letters, numbers, and underscores
- No spaces

**Good names:**
```python
city_name = "Tokyo"
building_count = 42
player_score = 100
```

**Bad names (will cause errors):**
```python
2nd_place = "silver"    # ❌ Can't start with number
my name = "Kenta"       # ❌ No spaces allowed
my-score = 50           # ❌ No hyphens allowed
```

## PM Analogy: Variables are Like Project Resources

Think of variables like resources in a project:

| Project Management | Programming |
|-------------------|-------------|
| Budget: $50,000 | `budget = 50000` |
| Team size: 5 people | `team_size = 5` |
| Project name: "Website Redesign" | `project_name = "Website Redesign"` |

You define them once, reference them throughout the project, and update them when things change.

## Variables Can Change

That's why they're called "variables" - the value can vary:

```python
score = 0
print(score)    # Prints: 0

score = 10
print(score)    # Prints: 10

score = 25
print(score)    # Prints: 25
```

Each time you use `=`, you replace what was in the box with a new value.

## Numbers vs Text

Python treats numbers and text differently:

```python
age = 30           # Number (no quotes)
name = "Kenta"     # Text (needs quotes)
```

- **Numbers** - just type them: `42`, `3.14`, `-10`
- **Text (strings)** - wrap in quotes: `"hello"`, `'world'`

This matters because you can do math with numbers:

```python
width = 10
height = 5
area = width * height
print(area)    # Prints: 50
```

But not with text:
```python
word = "hello"
result = word * 2
print(result)    # Prints: hellohello (repeats the text, doesn't do math)
```

---

## Hands-On Exercise

Create a new file called `city_building.py` and try this:

### Step 1: Define your building

```python
building_name = "City Hall"
height = 100
width = 40
color = "gray"
```

### Step 2: Print the details

```python
print("Building:")
print(building_name)
print("Height:")
print(height)
print("Width:")
print(width)
print("Color:")
print(color)
```

### Step 3: Run it

```
python city_building.py
```

### Step 4: Change the values

Edit the variables at the top to describe a different building (a house, a skyscraper, a shop). Run again.

Notice how you only changed the values once, but all the prints updated.

---

## Key Takeaways

1. **A variable is a labeled box** - it stores a value you can use later
2. **`=` means "store"** - not "equals" like in math
3. **Use the name without quotes** - `print(name)` gets the value, `print("name")` prints the word
4. **Names have rules** - no spaces, no starting with numbers
5. **Values can change** - that's why they're called variables

---

## Q&A

*(Questions asked during learning will be recorded here)*

## Quiz History

*(Quiz sessions will be recorded here)*
