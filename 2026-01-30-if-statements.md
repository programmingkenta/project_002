---
concepts: [if-statements, conditions, comparison, decisions]
source_repo: learning-programming
description: Making decisions in code with if statements. Programs that do different things based on conditions.
understanding_score: null
last_quizzed: null
prerequisites: [user-input, variables]
created: 30-01-2026
last_updated: 30-01-2026
---

# If Statements: Making Decisions

Until now, your programs run every line from top to bottom. But real programs need to make decisions:

- *If* the building is tall, paint it blue
- *If* the user says yes, continue
- *If* the score is high enough, you win

This is what `if` statements do.

## The Basic Pattern

```python
if condition:
    do this
```

In real code:

```python
height = 100

if height > 50:
    print("That's a tall building!")
```

Output: `That's a tall building!`

Because 100 is greater than 50, the condition is true, so the print runs.

## Breaking It Down

```python
if height > 50:
    print("That's a tall building!")
```

| Part | Meaning |
|------|---------|
| `if` | Start of the decision |
| `height > 50` | The condition to check |
| `:` | Required - marks the end of the condition |
| `    print(...)` | What to do if true (must be indented) |

## The Colon and Indentation

Two things beginners often miss:

1. **The colon `:`** - You must have it at the end of the `if` line
2. **The indentation** - The code inside must be indented (press Tab or 4 spaces)

```python
# Wrong - missing colon
if height > 50
    print("Tall!")

# Wrong - not indented
if height > 50:
print("Tall!")

# Correct
if height > 50:
    print("Tall!")
```

The indentation tells Python "this code belongs inside the if."

## Comparison Operators

You can compare values in different ways:

| Operator | Meaning | Example |
|----------|---------|---------|
| `>` | Greater than | `height > 50` |
| `<` | Less than | `height < 50` |
| `==` | Equal to | `color == "blue"` |
| `!=` | Not equal to | `color != "red"` |
| `>=` | Greater than or equal | `height >= 50` |
| `<=` | Less than or equal | `height <= 50` |

**Important:** Equals is `==` (two equals signs), not `=` (one equals sign).
- `=` means "store this value" (assignment)
- `==` means "check if these are equal" (comparison)

## If with Text

You can check text too:

```python
color = "blue"

if color == "blue":
    print("The sky color!")
```

Note the quotes around `"blue"` - you're comparing to text.

## What If the Condition is False?

If the condition is false, Python skips the indented code:

```python
height = 30

if height > 50:
    print("Tall building!")

print("Done")
```

Output: `Done`

The "Tall building!" line is skipped because 30 is not greater than 50.

## If-Else: Two Paths

What if you want to do something when the condition is false?

```python
height = 30

if height > 50:
    print("Tall building!")
else:
    print("Short building!")
```

Output: `Short building!`

The `else` block runs when the `if` condition is false.

## For Your 3D City

Imagine categorizing buildings:

```python
height = int(input("Enter building height: "))

if height > 100:
    print("Skyscraper!")
else:
    print("Regular building")
```

Note: `int()` converts the text from `input()` into a number so we can compare it. More on this soon.

---

## Hands-On Exercise

Create a new file called `building_checker.py`:

```python
print("=== Building Checker ===")
print()

height = int(input("Enter building height in meters: "))

if height > 100:
    print("Wow! That's a skyscraper!")
else:
    print("That's a regular building.")

if height > 500:
    print("One of the tallest in the world!")
```

### Try These Inputs

Run the program three times with different heights:
1. `50` - what do you see?
2. `150` - what do you see?
3. `600` - what do you see?

---

## Key Takeaways

1. **`if condition:` checks if something is true** - runs the indented code only if true
2. **Don't forget the colon `:`** - it's required after the condition
3. **Indentation matters** - code inside the if must be indented
4. **`==` for comparison, `=` for assignment** - two different things
5. **`else:` handles the false case** - optional, runs when if is false

---

## Q&A

*(Questions asked during learning will be recorded here)*

## Quiz History

*(Quiz sessions will be recorded here)*
