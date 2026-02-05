---
concepts: [ide, vs-code, editor, files, extensions]
source_repo: learning-programming
description: Understanding VS Code - your workspace for writing code. We learn the essential parts of the interface without getting overwhelmed.
understanding_score: null
last_quizzed: null
prerequisites: [what-is-programming]
created: 30-01-2026
last_updated: 30-01-2026
---

# VS Code Basics: Your Programming Workspace

Before you write code, you need to understand where you write it. VS Code is your workspace - like how a carpenter needs to know their workbench before building furniture.

This tutorial covers only what you need right now. VS Code has hundreds of features. We're ignoring most of them.

## What is an IDE?

IDE stands for "Integrated Development Environment." That's a fancy way of saying:

**A program where you write, run, and manage code - all in one place.**

Think of it like Microsoft Word, but for code instead of documents. Just as Word has spell-check and formatting, VS Code has features that help you write and run programs.

VS Code is one of the most popular IDEs. It's free and works for almost any programming language.

## The Four Areas You Need to Know

When you open VS Code, you see a lot. Let's focus on just four areas:

```
┌─────────────────────────────────────────────────────┐
│  1. MENU BAR (File, Edit, View...)                  │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│    2.    │           3. EDITOR                      │
│  SIDEBAR │      (where you write code)              │
│  (files) │                                          │
│          │                                          │
│          ├──────────────────────────────────────────┤
│          │           4. TERMINAL                    │
│          │      (where you run code)                │
└──────────┴──────────────────────────────────────────┘
```

### Area 1: Menu Bar (top)

Just like any program - File, Edit, View, etc. You'll use:
- **File → New File** to create new code files
- **File → Save** to save your work (or just press `Ctrl+S`)

### Area 2: Sidebar (left side)

Shows your files and folders. This is like Windows Explorer or Mac Finder, but inside VS Code.

- Click a file to open it
- Right-click to create new files or folders

If you don't see it, press `Ctrl+B` to toggle it.

### Area 3: Editor (center - the big area)

This is where you write code. It's like a text document, but smarter:
- It colors your code to make it readable (called "syntax highlighting")
- It shows line numbers on the left
- It can warn you about mistakes

### Area 4: Terminal (bottom)

This is where you run your code and see results.

If you don't see it, press `` Ctrl+` `` (that's the backtick key, usually above Tab).

The terminal is like a text-based conversation with your computer. You type commands, it responds.

## Your First Task: Open a Folder

VS Code works best when you open a **folder**, not just a single file. The folder becomes your "project."

1. Click **File → Open Folder**
2. Navigate to a folder where you want to keep your Python files
   - Or create a new folder called `python-learning`
3. Click **Select Folder**

Now your sidebar shows that folder's contents.

## Your Second Task: Create a Python File

1. In the sidebar, right-click and select **New File**
2. Name it `hello.py`
   - The `.py` tells VS Code "this is Python code"
3. The file opens in the editor

You now have an empty Python file ready for code.

## Your Third Task: Install Python Support

VS Code needs a helper (called an "extension") to understand Python.

1. Look at the left sidebar - find the icon that looks like four squares (Extensions)
   - Or press `Ctrl+Shift+X`
2. In the search box, type `Python`
3. Find the one by Microsoft (it'll be at the top, millions of downloads)
4. Click **Install**

This gives VS Code superpowers for Python:
- Better colors for Python code
- Ability to run Python files
- Error detection

## Your Fourth Task: Check Python is Installed

The extension helps VS Code understand Python, but you also need Python itself on your computer.

1. Open the terminal (`` Ctrl+` `` if it's hidden)
2. Type this and press Enter:

```
python --version
```

You should see something like:

```
Python 3.11.4
```

If you see an error like "python is not recognized," you need to install Python:
- Go to [python.org/downloads](https://www.python.org/downloads/)
- Download and install the latest version
- **Important:** During installation, check the box that says "Add Python to PATH"

## Putting It All Together

Now you have:
- VS Code open with a folder
- A file called `hello.py`
- Python extension installed
- Python installed on your computer

You're ready to write and run code.

---

## Key Takeaways

1. **IDE = a program for writing and running code** - VS Code is your IDE
2. **Four key areas:** Menu bar, Sidebar (files), Editor (writing), Terminal (running)
3. **Open a folder, not just files** - this creates a project workspace
4. **File extension matters** - `.py` tells VS Code it's Python
5. **Extensions add features** - the Python extension helps VS Code understand Python

---

## Quick Reference

| What you want | How to do it |
|---------------|--------------|
| Toggle sidebar | `Ctrl+B` |
| Toggle terminal | `` Ctrl+` `` |
| Save file | `Ctrl+S` |
| New file | `Ctrl+N` or right-click in sidebar |
| Open folder | `File → Open Folder` |
| Open extensions | `Ctrl+Shift+X` |

---

## Q&A

*(Questions asked during learning will be recorded here)*

## Quiz History

*(Quiz sessions will be recorded here)*
