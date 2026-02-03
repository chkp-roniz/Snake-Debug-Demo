# 🐍 Snake Debug Demo

> **Learn breakpoint debugging with a simple, visual bug**

A Snake game with an **intentional bug** that's perfect for learning VS Code debugging. The bug is simple: the snake passes over food without eating it. Use breakpoints to find why!

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.5+-green.svg)

[![Author](https://img.shields.io/badge/Author-Ron%20Izraeli-blue.svg)](https://www.linkedin.com/in/ron-izraeli/)

### 📺 Demo Video

[![Watch the Demo](https://img.youtube.com/vi/BoOaJ2cK6YY/maxresdefault.jpg)](https://www.youtube.com/watch?v=BoOaJ2cK6YY)

---

## 🎯 What You'll Learn

- **Set breakpoints** – Pause code execution at specific lines
- **Inspect variables** – See `head` vs `new_head` vs `food_pos` in real-time
- **Find the bug** – Discover why a simple variable mix-up breaks the game
- **Use GitHub Copilot** – Ask AI to explain the code and suggest fixes

---

## 🚀 Quick Start

### Option 1: Dev Container (Recommended)

1. Open in VS Code
2. Click "Reopen in Container" when prompted
3. Everything is pre-configured: extensions, settings, dependencies ✅

### Option 2: Manual Setup

```bash
git clone https://github.com/chkp-ai-transformation/debug-demo.git
cd debug-demo
pip install -r requirements.txt
```

**Required VS Code Extensions:**

- GitHub Copilot
- GitHub Copilot Chat
- Python (ms-python.python)
- Python Debugger (ms-python.debugpy)
- [Debug MCP Extension](https://github.com/microsoft/DebugMCP)

---

## 🎮 Running the Game

Press `F5` and select a configuration:

| Configuration                      | Description            |
| ---------------------------------- | ---------------------- |
| 🐍 Snake: Manual Mode              | Play with arrow keys   |
| 🤖 Snake: Auto-Player              | Watch the AI play      |
| 🐛 Debug: Step Through Auto-Player | **Best for debugging** |

### Command Line

```bash
python src/main.py --manual   # Play manually
python src/main.py --auto     # Watch AI play
```

---

## 🐛 The Bug

**Symptom:** The snake moves over the red food dot but doesn't eat it. Score stays at 0, food never moves.

**What's wrong:** The food collision check has **X and Y coordinates swapped** - a classic copy-paste bug!

```python
# Bug: compares (snake_x, snake_y) with (food_y, food_x)
if (new_head[0], new_head[1]) == (self.food_pos[1], self.food_pos[0]):
```

**Your challenge:**

1. Set a breakpoint in `snake.py` at the food collision check
2. Watch `new_head` and `self.food_pos` in the debugger
3. Notice the X/Y swap in the comparison!

👉 See [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) for a step-by-step walkthrough.

---

## 📁 Project Structure

```
debug-demo/
├── .devcontainer/        # Pre-configured dev container
├── .vscode/launch.json   # Debug configurations
├── .github/skills/       # Copilot debugging skill
├── src/
│   ├── main.py           # Entry point
│   ├── snake.py          # Game logic (bug is here!)
│   ├── auto_player.py    # AI pathfinding
│   └── web_game.py       # Browser version
├── DEBUGGING_GUIDE.md    # Step-by-step tutorial
└── requirements.txt
```

---

## 🎹 Controls

| Mode   | Controls                                          |
| ------ | ------------------------------------------------- |
| Manual | Arrow keys to move, R to restart, ESC to quit     |
| Auto   | D to toggle debug info, R to restart, ESC to quit |

---

## 📚 Resources

- [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) – Complete debugging tutorial
- [VS Code Debugging Docs](https://code.visualstudio.com/docs/editor/debugging)

---

## 📄 License

MIT License
