# 🎮 Snake Web Game Guide

> A web-based Snake game with an AI auto-player, designed for debugging demonstrations.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [How to Play](#how-to-play)
3. [Game Controls](#game-controls)
4. [How the Web Game Works](#how-the-web-game-works)
5. [Architecture Overview](#architecture-overview)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Running the Web Game

```bash
# Navigate to the project directory
cd /workspaces/debug-demo

# Start the web server
python src/web_game.py
```

The server will start and display:
```
==================================================
Snake Auto-Player Web Game
==================================================
Open in browser: http://localhost:8081
Press Ctrl+C to stop
==================================================
```

### Opening the Game

1. Open your browser and navigate to `http://localhost:8081`
2. The game will start automatically with the AI auto-player controlling the snake

---

## How to Play

### Game Objective

The goal is to **eat as much food as possible** while avoiding:
- 🧱 **Walls** — Hitting the edge of the grid ends the game
- 🐍 **Self-collision** — Running into the snake's own body ends the game

### Scoring

| Action | Points |
|--------|--------|
| Eat food (red square) | +1 point |
| Snake grows by 1 segment per food eaten |

### Game Flow

1. **Snake starts** in the center of the 20×20 grid
2. **AI takes control** and navigates toward the food using BFS pathfinding
3. **Food appears** as a red square at a random position
4. **Snake moves** automatically toward the food
5. When snake **eats food**:
   - Score increases by 1
   - Snake grows by 1 segment
   - New food spawns at a random location
6. Game continues until **collision** (wall or self)

---

## Game Controls

### Button Controls

| Button | Action |
|--------|--------|
| **Pause** | Toggle pause/resume the game |
| **Restart** | Reset the game to initial state |
| **Faster** | Increase game speed (decrease delay) |
| **Slower** | Decrease game speed (increase delay) |
| **Stop Server** | Shut down the web server |

### Speed Settings

- **Default speed**: 100ms per move
- **Fastest**: 30ms per move (click "Faster" multiple times)
- **Slowest**: 500ms per move (click "Slower" multiple times)
- Each click adjusts speed by 20ms

---

## How the Web Game Works

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Server | Python `http.server` + `socketserver` |
| Frontend | HTML5 Canvas + Vanilla JavaScript |
| AI Algorithm | BFS (Breadth-First Search) pathfinding |
| Protocol | HTTP (port 8081) |

### Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     web_game.py                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              ReusableTCPServer                        │  │
│  │  - Allows port reuse (avoids "Address in use" errors)│  │
│  │  - Listens on port 8081                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               GameHandler                             │  │
│  │  - Handles HTTP GET requests                         │  │
│  │  - Serves HTML_TEMPLATE on "/"                       │  │
│  │  - Handles "/shutdown" for server stop               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Client-Side Game Loop

```javascript
function gameLoop() {
    update();    // 1. Update game state (move snake, check collisions)
    draw();      // 2. Render everything to canvas
    setTimeout(gameLoop, speed);  // 3. Schedule next frame
}
```

### AI Pathfinding (BFS)

The auto-player uses **Breadth-First Search** to find the shortest safe path to food:

```
1. Start from snake head position
2. Explore all adjacent cells (UP, DOWN, LEFT, RIGHT)
3. Skip cells that are:
   - Out of bounds (walls)
   - Already visited
   - Part of snake body (except tail, which will move)
4. Continue until reaching food or exhausting all options
5. Return the path, or use fallback direction if no path found
```

### Rendering Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Clear      │───▶│  Draw Grid  │───▶│  Draw Snake │
│  Canvas     │    │  Lines      │    │  Segments   │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
                   ┌─────────────┐    ┌─────────────┐
                   │  Display    │◀───│  Draw Food  │
                   │  on Screen  │    │  (Red)      │
                   └─────────────┘    └─────────────┘
```

### Grid System

| Property | Value |
|----------|-------|
| Canvas size | 400×400 pixels |
| Grid size | 20×20 pixels per cell |
| Grid dimensions | 20×20 cells |
| Coordinate system | (x, y) where (0,0) is top-left |

---

## Architecture Overview

### File Structure

```
debug-demo/
├── src/
│   ├── web_game.py      # Web server + embedded HTML/JS game
│   ├── snake.py         # Core snake game logic (pygame version)
│   ├── auto_player.py   # AI pathfinding implementation
│   ├── config.py        # Game configuration and coordinate utils
│   ├── game_logger.py   # Logging utilities
│   └── main.py          # Command-line entry point
├── logs/                # Log files (created on first run)
├── WEB_GAME_GUIDE.md    # This file
├── BUG_EXPLANATION.md   # Detailed bug documentation
├── DEBUGGING_GUIDE.md   # How to debug the demo
└── README.md            # Project overview
```

### Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  HTML5 Canvas Game                                     │  │
│  │  - Snake rendering                                    │  │
│  │  - Food rendering                                     │  │
│  │  - BFS pathfinding (JavaScript)                       │  │
│  │  - Collision detection                                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ HTTP Requests
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Python Server                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  web_game.py                                          │  │
│  │  - Serves HTML template                               │  │
│  │  - Handles shutdown requests                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          │ imports                           │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  auto_player.py → config.py                           │  │
│  │  (imports trigger coordinate calibration)             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Common Issues

#### "Address already in use" Error

```bash
# Find the process using port 8081
lsof -i :8081

# Kill the process
kill -9 <PID>

# Or use a different port
python -c "from web_game import run_server; run_server(port=8082)"
```

#### Game Doesn't Start

1. Check if the server is running (look for console output)
2. Ensure you're accessing `http://localhost:8081` (not `https`)
3. Try a different browser
4. Check browser console for JavaScript errors (F12 → Console)

#### Snake Won't Eat Food

**This is the intentional bug in this demo!** 

The game has a coordinate offset bug that causes collision detection to fail after the snake eats a few pieces of food. See [BUG_EXPLANATION.md](BUG_EXPLANATION.md) for details.

To understand and fix this bug:
1. Read [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)
2. Use breakpoint debugging to trace the issue
3. The bug involves global state corruption in `config.py`

#### Server Won't Stop

- Use the **Stop Server** button in the browser
- Press `Ctrl+C` in the terminal
- Close the terminal window

---

## Expected vs Buggy Behavior

### Normal Behavior (Before Bug Manifests)

1. ✅ Snake moves toward food
2. ✅ Snake eats food and grows
3. ✅ Score increases
4. ✅ New food appears

### Buggy Behavior (After Bug Manifests)

1. ✅ Snake moves toward food
2. ❌ Snake passes through food without eating
3. ❌ Score stays the same
4. ❌ Food remains in the same position

The bug activates after the snake successfully eats a few pieces of food, demonstrating how global state corruption can create intermittent, hard-to-debug issues.

---

## For Developers

### Running with Debug Logging

```bash
# Enable verbose logging
SNAKE_DEBUG=true python src/web_game.py
```

### Log Files

Logs are written to `logs/snake_game.log` with automatic rotation:
- Max file size: 5 MB
- Backup count: 5 files
- Files: `snake_game.log`, `snake_game.log.1`, `snake_game.log.2`, etc.

### Modifying the Game

The web game is entirely contained in `web_game.py`:
- `HTML_TEMPLATE` — Contains all HTML, CSS, and JavaScript
- `GameHandler` — HTTP request handler
- `run_server()` — Starts the server

To modify game behavior, edit the JavaScript code within `HTML_TEMPLATE`.

---

*This demo is designed for learning debugging techniques. The bug is intentional!*
