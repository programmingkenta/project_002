---
concepts: [print, running-code, strings, syntax]
source_repo: learning-programming
description: Writing and running your very first Python program. We make the computer display a message, proving you can give it instructions.
understanding_score: null
last_quizzed: null
prerequisites: [what-is-programming]
created: 30-01-2026
last_updated: 30-01-2026
---

# Your First Python Program

In the last tutorial, we talked about programming being instructions for a very literal assistant. Today, you give your first instruction.

By the end of this tutorial, you will have made a computer do something because *you* told it to. That's a real milestone.

## One Line of Code

Here is a complete Python program:

```python
print("Hello, I am learning Python!")
```

That's it. One line. Let's understand every piece.

## Breaking Down `print("Hello, I am learning Python!")`

### Part 1: `print`

`print` is a **command** (Python calls these "functions"). It tells Python: "Display something on the screen."

Think of it like a megaphone. Whatever you hand to `print`, it broadcasts to the screen.

### Part 2: The parentheses `( )`

The parentheses hold what you want to print. They're like a container - you put something inside, and `print` knows that's what to display.

```
print( thing to display goes here )
```

### Part 3: The quotes `" "`

The quotes tell Python: "This is text, not a command."

Without quotes, Python thinks you're giving it instructions. With quotes, Python knows it's just words to display.

```python
print(Hello)   # ❌ Python thinks "Hello" is a command (error!)
print("Hello") # ✅ Python knows "Hello" is just text to display
```

Text inside quotes is called a **string** - just a fancy programming word for "a sequence of characters."

### Part 4: The message `Hello, I am learning Python!`

This is what appears on screen. You can change this to anything:

```python
print("My name is Kenta")
print("I want to build a 3D city")
print("12345")
print("!@#$%")
```

All of these work. Any text inside the quotes gets displayed.

## Why This Matters for Your 3D City

Later, when you build your city visualization, you'll want to give yourself feedback:

```python
print("Building placed at position 5, 10")
print("City has 42 buildings")
print("Rendering complete!")
```

`print` is how your program talks back to you. It's simple, but you'll use it constantly.

## Common Mistakes (And They're Normal!)

When you try this, you might make these errors. They're not failures - they're how everyone learns.

### Mistake 1: Forgetting quotes

```python
print(Hello)
```

**Error:** `NameError: name 'Hello' is not defined`

**Fix:** Add quotes around the text: `print("Hello")`

### Mistake 2: Mismatched quotes

```python
print("Hello')
```

**Error:** `SyntaxError: EOL while scanning string literal`

**Fix:** Use the same quote type on both ends: `print("Hello")`

### Mistake 3: Forgetting parentheses

```python
print "Hello"
```

**Error:** `SyntaxError: Missing parentheses in call to 'print'`

**Fix:** Add parentheses: `print("Hello")`

### Why Errors Happen

Remember our ultra-literal assistant?

If you write `print(Hello)`, Python asks: "What's Hello? Is that a command I should know? I don't recognize it."

It's not being difficult. It's being literal. The quotes are how you say "this is just text, not an instruction."

## Your Turn: The Hands-On Exercise

Now you do it. Here's what I want you to try:

### Step 1: Open a place to write Python

If you don't have Python set up yet, the easiest way to start is:

1. Go to [python.org](https://www.python.org/shell/) in your browser
2. Or use [Replit](https://replit.com/) - create a free account and start a Python project

### Step 2: Type this exactly

```python
print("Hello, world!")
```

### Step 3: Run it

Click the "Run" button (or press the play button, depending on your tool).

You should see:

```
Hello, world!
```

### Step 4: Make it yours

Now change the message to something about you or your city project:

```python
print("I am going to build a 3D pixel city")
```

Run it again. You just made the computer say what *you* wanted.

### Step 5: Try multiple lines

```python
print("Line one")
print("Line two")
print("Line three")
```

Each `print` creates a new line of output.

## What You Just Did

You wrote a program. Small, yes. But real.

- You gave the computer an instruction
- It understood that instruction
- It did exactly what you asked

Every program you'll ever write - including your 3D city - is just more of this: instructions the computer follows. You now know the pattern.

---

## Key Takeaways

1. **`print()` displays text on the screen** - it's how your program communicates
2. **Quotes make text a "string"** - without them, Python thinks it's a command
3. **Syntax matters** - parentheses, quotes, spelling must be exact
4. **Errors are normal** - they tell you what to fix, not that you failed

---

## Reflection Questions

Before the next tutorial, think about:

1. Did you get any errors when trying the exercise? What did you learn from them?
2. What would you want your 3D city program to "say" to you as it runs?

---

## Q&A

*(Questions asked during learning will be recorded here)*

## Quiz History

*(Quiz sessions will be recorded here)*
