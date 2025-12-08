<div align="center">
  <h1 align="center">uGit</h1>
  <p align="center">
    <i>A simplified Git implementation in Python for educational purposes.</i>
  </p>
</div>

<p align="center">
  <a href="https://www.python.org/downloads/release/python-310/"><img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+"></a>
</p>

---

`ugit` is a minimal yet functional version control system inspired by Git, written in Python. It's designed to be a learning tool that unravels the core concepts behind Git, such as blobs, trees, commits, and branching.

Reference: This project is based on the amazing tutorial by [Nikita](https://www.leshenko.net/p/ugit/#).

## ✨ Features

- **Core Git functionality**: `init`, `add`, `commit`, `checkout`.
- **Branching and merging**: `branch`, `merge`, `merge-base`.
- **History inspection**: `log`, `status`, `diff`.
- **Object management**: `hash-object`, `cat-file`, `write-tree`, `read-tree`.
- **Remote operations**: `fetch` and `push` (local filesystem remotes).
- **Tagging**: Create lightweight tags with `tag`.
- **Visualization**: A `k` command to visualize the commit history.

## 🚀 Getting Started

### 1. Installation

Clone the repository and install `ugit` in editable mode:

```bash
git clone https://github.com/EmaConor/uGit.git
cd uGit
pip install -e .
```

### 2. Basic Workflow

Here's a quick example of how to use `ugit`:

```bash
# Initialize a new repository
ugit init

# Create a file and add it to the index
echo "Hello, uGit!" > hello.txt
ugit add .

# Check status of commits
ugit status

# Commit the changes
ugit commit -m "Initial commit"

# Create a new branch
ugit branch feature

# Switch to the new branch
ugit checkout feature

# Make some changes
echo "A new feature is here." >> hello.txt
ugit status
ugit add .
ugit commit -m "Add new feature"

# Switch back to the main branch
ugit checkout main

# Merge the new feature branch
ugit merge feature

# Check the commit history
ugit log
```

## Command Reference

Here’s a breakdown of the available commands, grouped by functionality:

### 🗂️ Repository Management

| Command | Description |
| :--- | :--- |
| `ugit init` | Initialize a new repository. |
| `ugit status` | Show the working-tree status. |
| `ugit add <files...>` | Add file contents to the index. |

### 📜 History & Commits

| Command | Description |
| :--- | :--- |
| `ugit commit -m <msg>` | Create a new commit from the index. |
| `ugit log [oid]` | Display the commit history. |
| `ugit diff [--cached] [commit]` | Show changes between commits, commit and working tree. |
| `ugit show <oid>` | Show various types of objects (blobs, trees, commits). |
| `ugit k` | Visualize the commit history in a graph. |

### 🌱 Branching & Merging

| Command | Description |
| :--- | :--- |
| `ugit tag <name> [oid]` | Create a new tag object. |
| `ugit branch [name] [start]` | List or create |
| `ugit checkout <commit>` | Restore the working directory to a given commit state. |
| `ugit merge <commit>` | Merge a commit into the current branch. |
| `ugit merge-base <c1> <c2>` | Find the first common ancestor between two commits and merge. |
| `ugit reset <commit>` | Reset the current `HEAD` to a specified state. |

### 🌐 Remote Operations

| Command | Description |
| :--- | :--- |
| `ugit fetch <remote>` | Download objects and refs from another repository. |
| `ugit push <remote> <branch>` | Update remote refs along with associated objects. |

> **Note**: Remote operations are limited to local filesystem paths.

### 🔬 Low-Level Commands

These commands are used for direct manipulation of Git objects.

| Command | Description |
| :--- | :--- |
| `ugit hash-object <file>` | Compute object ID and optionally create a blob from a file. |
| `ugit cat-file <oid>` | Display the raw content of an object. |
| `ugit write-tree` | Create a tree object from the index. |
| `ugit read-tree <tree_oid>` | Read a tree object into the index. |

## 📁 Repository Internals

- **`.ugit/objects/`**: Stores all objects (blobs, trees, commits).
- **`.ugit/refs/`**: Stores references (branches, tags).
- **`.ugit/HEAD`**: Points to the current branch or commit.
- **`.ugit/index`**: The index file (staging area).

`ugit` ignores `.ugit`, `.git`, `.venv`, and `__pycache__` directories.

