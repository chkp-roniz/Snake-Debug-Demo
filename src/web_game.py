"""
Web-based Snake Game with Auto-Player

This serves the snake game as a web page that can be viewed in a browser.
Game events are logged server-side to snake_game.log for debugging.
"""

import http.server
import socketserver
import json
import threading
import time
from auto_player import AutoPlayer, Direction
from game_logger import (
    game_logger, state_logger, ai_logger, collision_logger,
    log_startup_info, log_ai_decision, log_bfs_path, log_snake_move,
    log_game_state, log_collision_check
)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Snake Game - Auto Player</title>
    <style>
        body {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            background: #1a1a2e;
            font-family: 'Segoe UI', Arial, sans-serif;
            color: white;
        }
        h1 { color: #4ecca3; margin-bottom: 10px; }
        #game-container {
            background: #16213e;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(78, 204, 163, 0.3);
        }
        canvas {
            border: 2px solid #4ecca3;
            border-radius: 5px;
        }
        #info {
            margin-top: 15px;
            font-size: 18px;
            display: flex;
            gap: 30px;
            justify-content: center;
        }
        .stat { color: #4ecca3; }
        #controls {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        button {
            padding: 10px 20px;
            font-size: 14px;
            cursor: pointer;
            background: #4ecca3;
            color: #1a1a2e;
            border: none;
            border-radius: 5px;
            font-weight: bold;
        }
        button:hover { background: #3db892; }
        #status {
            margin-top: 10px;
            font-size: 16px;
            color: #e94560;
        }
    </style>
</head>
<body>
    <h1>Snake Auto-Player Demo</h1>
    <div id="game-container">
        <canvas id="game" width="400" height="400"></canvas>
        <div id="info">
            <span>Score: <span class="stat" id="score">0</span></span>
            <span>Length: <span class="stat" id="length">1</span></span>
            <span>Moves: <span class="stat" id="moves">0</span></span>
        </div>
        <div id="controls">
            <button onclick="togglePause()">Pause</button>
            <button onclick="restart()">Restart</button>
            <button onclick="speedUp()">Faster</button>
            <button onclick="slowDown()">Slower</button>
            <button onclick="stopServer()" style="background: #e94560;">Stop Server</button>
        </div>
        <div id="status"></div>
    </div>

    <script>
        const canvas = document.getElementById('game');
        const ctx = canvas.getContext('2d');
        const GRID_SIZE = 20;
        const GRID_WIDTH = canvas.width / GRID_SIZE;
        const GRID_HEIGHT = canvas.height / GRID_SIZE;
        
        let snake = [{x: Math.floor(GRID_WIDTH/2), y: Math.floor(GRID_HEIGHT/2)}];
        let food = {x: 0, y: 0};
        let direction = {x: 1, y: 0};
        let score = 0;
        let moves = 0;
        let gameOver = false;
        let paused = false;
        let speed = 100;
        
        // Runtime coordinate optimization state
        let coordOptLevel = 0;
        
        function spawnFood() {
            do {
                food.x = Math.floor(Math.random() * GRID_WIDTH);
                food.y = Math.floor(Math.random() * GRID_HEIGHT);
            } while (snake.some(s => s.x === food.x && s.y === food.y));
        }
        
        // BFS pathfinding (same logic as Python auto_player)
        function findPath(start, goal, obstacles) {
            const queue = [[start]];
            const visited = new Set();
            visited.add(`${start.x},${start.y}`);
            
            const dirs = [{x:0,y:-1},{x:0,y:1},{x:-1,y:0},{x:1,y:0}];
            
            while (queue.length > 0) {
                const path = queue.shift();
                const current = path[path.length - 1];
                
                if (current.x === goal.x && current.y === goal.y) {
                    return path;
                }
                
                for (const dir of dirs) {
                    const next = {x: current.x + dir.x, y: current.y + dir.y};
                    const key = `${next.x},${next.y}`;
                    
                    if (next.x < 0 || next.x >= GRID_WIDTH || 
                        next.y < 0 || next.y >= GRID_HEIGHT) continue;
                    if (visited.has(key)) continue;
                    if (obstacles.has(key)) continue;
                    
                    visited.add(key);
                    queue.push([...path, next]);
                }
            }
            return null;
        }
        
        function getAutoDirection() {
            // Build obstacles set (snake body except tail)
            const obstacles = new Set();
            for (let i = 0; i < snake.length - 1; i++) {
                obstacles.add(`${snake[i].x},${snake[i].y}`);
            }
            
            const head = snake[0];
            const path = findPath(head, food, obstacles);
            
            if (path && path.length > 1) {
                const next = path[1];
                const newDir = {x: next.x - head.x, y: next.y - head.y};
                
                // Prevent 180 turn
                if (direction.x + newDir.x !== 0 || direction.y + newDir.y !== 0) {
                    return newDir;
                }
            }
            
            // Fallback: find any safe direction
            const dirs = [{x:0,y:-1},{x:0,y:1},{x:-1,y:0},{x:1,y:0}];
            for (const dir of dirs) {
                if (direction.x + dir.x === 0 && direction.y + dir.y === 0) continue;
                const next = {x: head.x + dir.x, y: head.y + dir.y};
                if (next.x < 0 || next.x >= GRID_WIDTH || 
                    next.y < 0 || next.y >= GRID_HEIGHT) continue;
                if (obstacles.has(`${next.x},${next.y}`)) continue;
                return dir;
            }
            
            return direction;
        }
        
        function update() {
            if (gameOver || paused) return;
            
            const oldHead = snake[0];
            
            // Get auto-player direction
            direction = getAutoDirection();
            
            // Log AI decision
            serverLog('ai_decision', {
                head: oldHead,
                food: food,
                direction: direction,
                decisionNum: moves + 1,
                snakeLength: snake.length
            });
            
            const head = {x: snake[0].x + direction.x, y: snake[0].y + direction.y};
            
            // Log snake move
            serverLog('snake_move', {
                oldHead: oldHead,
                newHead: head,
                direction: direction,
                moveNum: moves + 1
            });
            
            // Check collisions
            if (head.x < 0 || head.x >= GRID_WIDTH || 
                head.y < 0 || head.y >= GRID_HEIGHT ||
                snake.some(s => s.x === head.x && s.y === head.y)) {
                gameOver = true;
                serverLog('game_over', {
                    head: head,
                    score: score,
                    moves: moves,
                    snakeLength: snake.length,
                    reason: head.x < 0 || head.x >= GRID_WIDTH || head.y < 0 || head.y >= GRID_HEIGHT ? 'wall' : 'self'
                });
                document.getElementById('status').textContent = 'GAME OVER! Click Restart to play again.';
                return;
            }
            
            snake.unshift(head);
            moves++;
            
            // Check food collision with coordinate optimization
            const optX = Math.floor(coordOptLevel / 2);
            const optY = -(coordOptLevel - optX);
            const foodCheckPos = {x: food.x + optX, y: food.y + optY};
            const ateFood = head.x === foodCheckPos.x && head.y === foodCheckPos.y;
            
            // Log collision check
            serverLog('collision_check', {
                head: head,
                food: food,
                foodCheckPos: foodCheckPos,
                result: ateFood,
                coordOptLevel: coordOptLevel
            });
            
            if (ateFood) {
                score++;
                serverLog('food_eaten', {
                    head: head,
                    food: food,
                    newScore: score,
                    newLength: snake.length
                });
                if (coordOptLevel < 4) coordOptLevel++;
                spawnFood();
                serverLog('food_spawned', {food: food});
            } else {
                snake.pop();
            }
            
            document.getElementById('score').textContent = score;
            document.getElementById('length').textContent = snake.length;
            document.getElementById('moves').textContent = moves;
        }
        
        function draw() {
            // Clear
            ctx.fillStyle = '#0f0f23';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Grid
            ctx.strokeStyle = '#1a1a3e';
            for (let x = 0; x <= canvas.width; x += GRID_SIZE) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }
            for (let y = 0; y <= canvas.height; y += GRID_SIZE) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }
            
            // Snake
            snake.forEach((segment, i) => {
                ctx.fillStyle = i === 0 ? '#4ecca3' : '#3db892';
                ctx.fillRect(
                    segment.x * GRID_SIZE + 1, 
                    segment.y * GRID_SIZE + 1, 
                    GRID_SIZE - 2, 
                    GRID_SIZE - 2
                );
            });
            
            // Food
            ctx.fillStyle = '#e94560';
            ctx.fillRect(
                food.x * GRID_SIZE + 1, 
                food.y * GRID_SIZE + 1, 
                GRID_SIZE - 2, 
                GRID_SIZE - 2
            );
        }
        
        function togglePause() {
            paused = !paused;
            document.getElementById('status').textContent = paused ? 'Paused' : '';
        }
        
        function restart() {
            snake = [{x: Math.floor(GRID_WIDTH/2), y: Math.floor(GRID_HEIGHT/2)}];
            direction = {x: 1, y: 0};
            score = 0;
            moves = 0;
            gameOver = false;
            paused = false;
            coordOptLevel = 0;
            spawnFood();
            document.getElementById('status').textContent = '';
            serverLog('game_restart', {
                head: snake[0],
                food: food,
                gridWidth: GRID_WIDTH,
                gridHeight: GRID_HEIGHT
            });
        }
        
        function speedUp() {
            speed = Math.max(30, speed - 20);
        }
        
        function slowDown() {
            speed = Math.min(500, speed + 20);
        }
        
        function stopServer() {
            document.getElementById('status').textContent = 'Stopping server...';
            document.getElementById('status').style.color = '#e94560';
            fetch('/shutdown').then(() => {
                document.getElementById('status').textContent = 'Server stopped. Close this tab.';
            }).catch(() => {
                document.getElementById('status').textContent = 'Server stopped.';
            });
        }
        
        // Server-side logging function
        function serverLog(event, data) {
            fetch('/log', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({event, ...data})
            }).catch(() => {}); // Ignore errors
        }
        
        spawnFood();
        serverLog('game_start', {
            head: snake[0],
            food: food,
            gridWidth: GRID_WIDTH,
            gridHeight: GRID_HEIGHT
        });
        
        function gameLoop() {
            update();
            draw();
            setTimeout(gameLoop, speed);
        }
        
        gameLoop();
    </script>
</body>
</html>
'''

class GameHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        game_logger.debug(f"GET request received: {self.path}")
        
        if self.path.startswith('/shutdown'):
            game_logger.info("Shutdown request received")
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Server shutting down...')
            # Exit the process after response is sent
            def shutdown():
                time.sleep(0.5)
                game_logger.info("Server shutting down...")
                import os
                os._exit(0)
            threading.Thread(target=shutdown).start()
            return
        
        game_logger.debug("Serving game HTML page")
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        self.wfile.write(HTML_TEMPLATE.encode())
        game_logger.info(f"Game page served to {self.client_address[0]}")
    
    def do_POST(self):
        """Handle POST requests for game event logging."""
        if self.path == '/log':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                event = data.get('event', 'unknown')
                
                # Log based on event type
                if event == 'game_start':
                    state_logger.info("="*50)
                    state_logger.info("WEB GAME STARTED")
                    state_logger.info("="*50)
                    state_logger.info(f"Initial head: ({data.get('head', {}).get('x')}, {data.get('head', {}).get('y')})")
                    state_logger.info(f"Initial food: ({data.get('food', {}).get('x')}, {data.get('food', {}).get('y')})")
                    state_logger.info(f"Grid: {data.get('gridWidth')}x{data.get('gridHeight')}")
                
                elif event == 'game_restart':
                    state_logger.info("="*50)
                    state_logger.info("GAME RESTARTED")
                    state_logger.info("="*50)
                    state_logger.info(f"Initial head: ({data.get('head', {}).get('x')}, {data.get('head', {}).get('y')})")
                    state_logger.info(f"Initial food: ({data.get('food', {}).get('x')}, {data.get('food', {}).get('y')})")
                
                elif event == 'ai_decision':
                    head = data.get('head', {})
                    food = data.get('food', {})
                    direction = data.get('direction', {})
                    decision_num = data.get('decisionNum', 0)
                    snake_len = data.get('snakeLength', 1)
                    dir_name = self._direction_name(direction)
                    ai_logger.info(f"=== AI Decision #{decision_num} ===")
                    ai_logger.info(f"Head: ({head.get('x')}, {head.get('y')}), Food: ({food.get('x')}, {food.get('y')})")
                    ai_logger.info(f"Snake length: {snake_len}")
                    ai_logger.debug(f"Decision: {dir_name}")
                
                elif event == 'snake_move':
                    old_head = data.get('oldHead', {})
                    new_head = data.get('newHead', {})
                    direction = data.get('direction', {})
                    move_num = data.get('moveNum', 0)
                    dir_name = self._direction_name(direction)
                    state_logger.info(f"Move #{move_num}: ({old_head.get('x')}, {old_head.get('y')}) -> ({new_head.get('x')}, {new_head.get('y')}) [{dir_name}]")
                
                elif event == 'collision_check':
                    head = data.get('head', {})
                    food = data.get('food', {})
                    food_check = data.get('foodCheckPos', {})
                    result = data.get('result', False)
                    opt_level = data.get('coordOptLevel', 0)
                    collision_logger.debug(f"Collision check: head=({head.get('x')}, {head.get('y')}) vs food=({food.get('x')}, {food.get('y')})")
                    collision_logger.debug(f"  Food check pos (opt={opt_level}): ({food_check.get('x')}, {food_check.get('y')}) -> {'HIT' if result else 'MISS'}")
                
                elif event == 'food_eaten':
                    head = data.get('head', {})
                    food = data.get('food', {})
                    new_score = data.get('newScore', 0)
                    new_len = data.get('newLength', 1)
                    state_logger.info(f"*** FOOD EATEN at ({food.get('x')}, {food.get('y')})! Score: {new_score}, Length: {new_len} ***")
                
                elif event == 'food_spawned':
                    food = data.get('food', {})
                    state_logger.debug(f"New food spawned at: ({food.get('x')}, {food.get('y')})")
                
                elif event == 'game_over':
                    head = data.get('head', {})
                    score = data.get('score', 0)
                    moves = data.get('moves', 0)
                    snake_len = data.get('snakeLength', 1)
                    reason = data.get('reason', 'unknown')
                    state_logger.info("="*50)
                    state_logger.info("GAME OVER!")
                    state_logger.info("="*50)
                    state_logger.info(f"Reason: {reason} collision at ({head.get('x')}, {head.get('y')})")
                    state_logger.info(f"Final score: {score}")
                    state_logger.info(f"Total moves: {moves}")
                    state_logger.info(f"Final length: {snake_len}")
                
                else:
                    game_logger.debug(f"Unknown event: {event}, data: {data}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
                
            except json.JSONDecodeError as e:
                game_logger.error(f"Invalid JSON in log request: {e}")
                self.send_response(400)
                self.end_headers()
            except Exception as e:
                game_logger.error(f"Error processing log request: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _direction_name(self, direction):
        """Convert direction dict to readable name."""
        dx = direction.get('x', 0)
        dy = direction.get('y', 0)
        if dx == 0 and dy == -1:
            return "UP"
        elif dx == 0 and dy == 1:
            return "DOWN"
        elif dx == -1 and dy == 0:
            return "LEFT"
        elif dx == 1 and dy == 0:
            return "RIGHT"
        return f"({dx}, {dy})"
    
    def log_message(self, format, *args):
        game_logger.debug(f"[Web Server] {args[0]}")
        print(f"[Web Server] {args[0]}")


class ReusableTCPServer(socketserver.TCPServer):
    """TCP Server that allows port reuse to avoid 'Address already in use' errors."""
    allow_reuse_address = True


def run_server(port=8081):
    game_logger.info("="*50)
    game_logger.info("WEB GAME SERVER STARTING")
    game_logger.info("="*50)
    game_logger.info(f"Server port: {port}")
    game_logger.info(f"URL: http://localhost:{port}")
    
    with ReusableTCPServer(("", port), GameHandler) as httpd:
        print(f"\n{'='*50}")
        print(f"Snake Auto-Player Web Game")
        print(f"{'='*50}")
        print(f"Open in browser: http://localhost:{port}")
        print(f"Press Ctrl+C to stop")
        print(f"{'='*50}\n")
        game_logger.info("Server started, waiting for connections...")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
