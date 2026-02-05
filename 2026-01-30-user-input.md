---
concepts: [input, user-input, interactive-programs]
source_repo: learning-programming
description: Getting input from the user with input(). Making programs interactive by asking questions and using the answers.
understanding_score: null
last_quizzed: null
prerequisites: [variables]
created: 30-01-2026
last_updated: 30-01-2026
---

# User Input: Making Programs Interactive

So far, your programs only talk *at* you. They print messages, but they don't listen.

Now you'll learn `input()` - how to make your program ask questions and use the answers.

## The `input()` Function

```python
name = input("What is your name? ")
print("Hello,", name)
```

When you run this:
1. Python displays: `What is your name? `
2. The program **waits** for you to type something
3. You type your answer and press Enter
4. Whatever you typed gets stored in the variable `name`
5. The program continues and prints the greeting

## How `input()` Works

```python
variable = input("Your question here: ")
```

- The text in quotes is the **prompt** - what the user sees
- The program **pauses** until the user types and presses Enter
- Whatever they type gets **stored** in the variable

Think of it as the opposite of `print()`:
- `print()` sends information OUT to the user
- `input()` brings information IN from the user

## A Simple Conversation

```python
name = input("What is your name? ")
city = input("What city do you live in? ")

print("Nice to meet you,", name)
print("I hear", city, "is a great place!")
```

The program asks two questions, remembers both answers, then uses them.

## For Your 3D City Project

Imagine letting the user design their city:

```python
building_name = input("What building do you want to create? ")
height = input("How tall should it be? ")
color = input("What color? ")

print("Creating a", color, building_name, "that is", height, "meters tall")
```

Now your city builder is interactive!

## Important: `input()` Always Returns Text

This surprises beginners. Even if the user types a number:

```python
age = input("How old are you? ")
```

If you type `25`, the variable `age` holds `"25"` (text), not `25` (number).

This matters if you want to do math. We'll learn how to convert text to numbers in a future lesson. For now, just know that `input()` gives you text.

## The Space Trick

Notice the space at the end of prompts:

```python
input("What is your name? ")   # Good - space before closing quote
input("What is your name?")    # Works, but cursor touches the question mark
```

The space makes the output look cleaner:
```
What is your name? Kenta     # With space - looks nice
What is your name?Kenta      # Without space - cramped
```

---

## Hands-On Exercise

Create a new file called `city_planner.py`:

```python
print("=== City Planner ===")
print()

city_name = input("What is your city called? ")
num_buildings = input("How many buildings should it have? ")
main_color = input("What is the main color theme? ")

print()
print("=== Your City Plan ===")
print("City:", city_name)
print("Buildings:", num_buildings)
print("Color theme:", main_color)
print()
print("Let's start building", city_name + "!")
```

### Run It

```
python city_planner.py
```

The program will ask you three questions. Answer them and see your city plan!

### New Thing: `print()`

Notice `print()` with nothing inside? It just prints a blank line - useful for spacing.

### New Thing: `+` with Text

`city_name + "!"` joins text together. If `city_name` is `"Tokyo"`, the result is `"Tokyo!"`. This is called **concatenation** (just a fancy word for joining text).

---

## Key Takeaways

1. **`input("prompt")` asks for user input** - program waits for an answer
2. **The answer gets stored in a variable** - use it like any other variable
3. **`input()` always returns text** - even if user types numbers
4. **Add a space at the end of prompts** - makes output cleaner

---

## Q&A

*(Questions asked during learning will be recorded here)*

## Quiz History

*(Quiz sessions will be recorded here)*
