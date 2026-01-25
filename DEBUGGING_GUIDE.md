# 🔍 Debugging Guide: Finding the Food Bug

This guide walks you through debugging the Snake game using VS Code breakpoints and GitHub Copilot. You'll learn how to find a bug where the **snake passes over food without eating it**.

---

## 🎯 The Challenge

The snake can move around, but when it reaches the red food dot, **nothing happens**:
- The food doesn't disappear
- The score doesn't increase
- The snake doesn't grow

**Your mission:** Use breakpoints to find why the food collision isn't working.

---

## 📋 Prerequisites

Everything is pre-configured in the Dev Container! Just:

1. Open in VS Code
2. Click "Reopen in Container" when prompted
3. All extensions and settings are ready

**Included Extensions:**
- GitHub Copilot & Copilot Chat
- Python & Python Debugger
- Debug MCP Extension

---

## 🎮 Part 1: See the Bug

### Step 1: Run the Game

1. Press `F5` and select **"🤖 Snake: Auto-Player"**
2. Watch the snake move toward the red food
3. Notice: The snake **passes right through** the food!
4. The score stays at 0, food never moves

### Step 2: Try Manual Mode

1. Press `F5` and select **"🐍 Snake: Manual Mode"**
2. Use arrow keys to move the snake to the food
3. Same problem: Snake goes over food, nothing happens

**The bug:** Food collision detection isn't working correctly.

---

## 🔬 Part 2: Find the Bug with Breakpoints

### Step 1: Open the Game Logic

Open [src/snake.py](src/snake.py) - this contains the `SnakeGame` class with all game logic.

### Step 2: Find the Food Collision Code

Look for the `update()` method (around line 130). This is where the game:
1. Moves the snake
2. Checks for collisions
3. Handles food eating

Find this section (around line 184):
```python
# Check food collision
if (new_head[0], new_head[1]) == (self.food_pos[1], self.food_pos[0]):
    self.score += 1
    self._spawn_food()
```

### Step 3: Set a Breakpoint

1. Click in the left gutter on the line with `if (new_head[0], new_head[1]) ==`
2. A red dot appears - this is your breakpoint
3. Press `F5` and select **"🐛 Debug: Step Through Auto-Player"**

### Step 4: Inspect Variables

When the debugger pauses at your breakpoint:

1. Look at the **Variables** panel in the Debug sidebar
2. Find these variables:
   - `new_head` - Where the snake IS NOW (tuple like `(5, 3)`)
   - `self.food_pos` - Where the food is (tuple like `(5, 3)`)

3. **The Aha Moment:** Notice that:
   - `new_head` equals `food_pos` ✅ (e.g., both are `(5, 3)`)
   - But the code compares `new_head` with `(food_pos[1], food_pos[0])` = `(3, 5)` ❌
   - The X and Y are swapped!

### Step 5: Add Watch Expressions

In the **Watch** panel, add these expressions to see the bug clearly:
```
new_head
self.food_pos
(self.food_pos[1], self.food_pos[0])
new_head == self.food_pos
(new_head[0], new_head[1]) == (self.food_pos[1], self.food_pos[0])
```

Press `F5` (Continue) and watch - `new_head == self.food_pos` is True but the buggy comparison is False!

---

## 🐛 Part 3: Understanding the Bug

### The Problem

The code checks:
```python
if (new_head[0], new_head[1]) == (self.food_pos[1], self.food_pos[0]):  # ❌ WRONG - x/y swapped!
```

But it should check:
```python
if new_head == self.food_pos:  # ✅ RIGHT - direct comparison
```

### Why This Happens

The bug compares:
- `new_head[0]` (snake's X) with `food_pos[1]` (food's Y)
- `new_head[1]` (snake's Y) with `food_pos[0]` (food's X)

This is a classic **copy-paste bug** where X and Y coordinates got swapped!

### Visual Example

```
Snake at (5, 3)    Food at (5, 3)
                   
Bug checks: (5, 3) == (3, 5)?  ❌ NO - coordinates swapped!
Should be:  (5, 3) == (5, 3)?  ✅ YES - direct match
```

The only time the snake "eats" food is when food happens to spawn at a position where X equals Y (like 5,5 or 3,3) - which is rare!

---

## 💬 Part 4: Ask GitHub Copilot

Open Copilot Chat (`Ctrl+Shift+I` or `Cmd+Shift+I`) and try these prompts:

### Understand the Code
> "Explain the update() method in snake.py. What is the difference between head and new_head?"

### Find the Bug
> "In snake.py, the food collision check uses 'head' instead of 'new_head'. Why is this wrong?"

### Get the Fix
> "How do I fix the food collision bug in snake.py?"

### At a Breakpoint
> "I'm at a breakpoint where new_head equals food_pos but head doesn't. Why isn't the food being eaten?"

---

## ✅ Part 5: The Fix

### The One-Line Fix

Change line ~184 in [src/snake.py](src/snake.py):

**Before (buggy):**
```python
if (new_head[0], new_head[1]) == (self.food_pos[1], self.food_pos[0]):
```

**After (fixed):**
```python
if new_head == self.food_pos:
```

### Verify the Fix

1. Make the change
2. Press `F5` and select **"🤖 Snake: Auto-Player"**
3. Watch the snake eat food and grow!
4. Score increases, food respawns ✅

---

## 🎓 Key Takeaways

| Lesson | Explanation |
|--------|-------------|
| **Check your coordinates** | X and Y swaps are a classic bug |
| **Compare the right values** | `(x,y) == (y,x)` is NOT the same as `(x,y) == (x,y)` |
| **Breakpoints reveal truth** | See exactly what values are being compared |
| **Copilot helps debug** | Ask about coordinate comparisons and find swapped values |

---

## 🏆 Practice Challenges

Now that you've found this bug, try these:

1. **Set conditional breakpoints** - Only pause when `new_head == self.food_pos`
2. **Add debug logging** - Print head, new_head, and food_pos each frame
3. **Find edge cases** - What happens if food spawns on the snake?

---

## 📚 Quick Reference

### Debug Controls

| Action | Keyboard | Description |
|--------|----------|-------------|
| Continue | `F5` | Run to next breakpoint |
| Step Over | `F10` | Execute line, skip functions |
| Step Into | `F11` | Enter function calls |
| Step Out | `Shift+F11` | Exit current function |
| Stop | `Shift+F5` | End debug session |

### Key Files

| File | Purpose |
|------|---------|
| [src/snake.py](src/snake.py) | Game logic (contains the bug) |
| [src/main.py](src/main.py) | Entry point and game loop |
| [src/auto_player.py](src/auto_player.py) | AI pathfinding |

---

**Happy Debugging! 🐛🔍**
