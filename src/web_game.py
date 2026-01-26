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
import random
from auto_player import AutoPlayer, Direction
import config
from game_logger import (
    game_logger, state_logger, ai_logger, collision_logger,
    log_startup_info, log_ai_decision, log_bfs_path, log_snake_move,
    log_game_state, log_collision_check
)

# Server-side game state management
class ServerGameState:
    def __init__(self):
        self.grid_width = 20
        self.grid_height = 20
        self.auto_player = AutoPlayer(debug_mode=False)
        self.reset()
    
    def reset(self):
        """Reset game to initial state."""
        self.snake = [{"x": self.grid_width // 2, "y": self.grid_height // 2}]
        self.food = {"x": 0, "y": 0}
        self.direction = {"x": 1, "y": 0}
        self.score = 0
        self.moves = 0
        self.game_over = False
        self.game_over_reason = ""
        self._spawn_food()
        state_logger.info("Server game state reset")
        state_logger.info(f"Initial head: ({self.snake[0]['x']}, {self.snake[0]['y']})")
        state_logger.info(f"Initial food: ({self.food['x']}, {self.food['y']})")
    
    def _spawn_food(self):
        """Spawn food at random position not occupied by snake."""
        attempts = 0
        while attempts < 100:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            if not any(s["x"] == x and s["y"] == y for s in self.snake):
                self.food = {"x": x, "y": y}
                state_logger.debug(f"Food spawned at ({x}, {y})")
                return
            attempts += 1
        self.food = {"x": random.randint(0, self.grid_width - 1), 
                     "y": random.randint(0, self.grid_height - 1)}
    
    def get_auto_direction(self):
        """Get next direction from auto-player AI."""
        # Convert to format expected by auto_player
        game_state = {
            "snake_body": [(s["x"], s["y"]) for s in self.snake],
            "head": (self.snake[0]["x"], self.snake[0]["y"]),
            "food_pos": (self.food["x"], self.food["y"]),
            "direction": Direction((self.direction["x"], self.direction["y"])),
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "score": self.score
        }
        
        ai_direction = self.auto_player.get_next_direction(game_state)
        dx, dy = ai_direction.value
        
        ai_logger.info(f"=== AI Decision #{self.moves + 1} ===")
        ai_logger.info(f"Head: ({self.snake[0]['x']}, {self.snake[0]['y']}), Food: ({self.food['x']}, {self.food['y']})")
        ai_logger.info(f"Snake length: {len(self.snake)}")
        ai_logger.debug(f"Decision: {ai_direction.name}")
        
        return {"x": dx, "y": dy}
    
    def update(self):
        """Update game state for one step."""
        if self.game_over:
            return self.get_state()
        
        old_head = self.snake[0].copy()
        
        # Get direction from auto-player
        self.direction = self.get_auto_direction()
        
        # Calculate new head position
        new_head = {
            "x": self.snake[0]["x"] + self.direction["x"],
            "y": self.snake[0]["y"] + self.direction["y"]
        }
        
        self.moves += 1
        
        state_logger.info(f"Move #{self.moves}: ({old_head['x']}, {old_head['y']}) -> ({new_head['x']}, {new_head['y']})")
        
        # Check wall collision
        if (new_head["x"] < 0 or new_head["x"] >= self.grid_width or
            new_head["y"] < 0 or new_head["y"] >= self.grid_height):
            self.game_over = True
            self.game_over_reason = "wall"
            state_logger.info("="*50)
            state_logger.info("GAME OVER!")
            state_logger.info("="*50)
            state_logger.info(f"Reason: wall collision at ({new_head['x']}, {new_head['y']})")
            state_logger.info(f"Final score: {self.score}")
            state_logger.info(f"Total moves: {self.moves}")
            state_logger.info(f"Final length: {len(self.snake)}")
            return self.get_state()
        
        # Check self collision
        if any(s["x"] == new_head["x"] and s["y"] == new_head["y"] for s in self.snake):
            self.game_over = True
            self.game_over_reason = "self"
            state_logger.info("="*50)
            state_logger.info("GAME OVER!")
            state_logger.info("="*50)
            state_logger.info(f"Reason: self collision at ({new_head['x']}, {new_head['y']})")
            state_logger.info(f"Final score: {self.score}")
            state_logger.info(f"Total moves: {self.moves}")
            state_logger.info(f"Final length: {len(self.snake)}")
            return self.get_state()
        
        # Move snake
        self.snake.insert(0, new_head)
        
        # Check food collision using config module functions
        food_pos_tuple = (self.food["x"], self.food["y"])
        new_head_tuple = (new_head["x"], new_head["y"])
        food_check_pos_tuple = config.get_food_collision_position(food_pos_tuple)
        ate_food = config.check_positions_equal(new_head_tuple, food_check_pos_tuple)
        
        collision_logger.debug(f"Collision check: head=({new_head['x']}, {new_head['y']}) vs food=({self.food['x']}, {self.food['y']})")
        collision_logger.debug(f"  Food check pos: ({food_check_pos_tuple[0]}, {food_check_pos_tuple[1]}) -> {'HIT' if ate_food else 'MISS'}")
        
        if ate_food:
            self.score += 1
            state_logger.info(f"*** FOOD EATEN at ({self.food['x']}, {self.food['y']})! Score: {self.score}, Length: {len(self.snake)} ***")
            config._advance_runtime_optimization()
            self._spawn_food()
            state_logger.debug(f"New food spawned at: ({self.food['x']}, {self.food['y']})")
        else:
            self.snake.pop()
        
        return self.get_state()
    
    def get_state(self):
        """Get current game state as dictionary."""
        return {
            "snake": self.snake,
            "food": self.food,
            "direction": self.direction,
            "score": self.score,
            "moves": self.moves,
            "gameOver": self.game_over,
            "gameOverReason": self.game_over_reason
        }

# Global server game state
server_game_state = ServerGameState()

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
        
        // Client-side state (synced from server)
        let snake = [{x: 10, y: 10}];
        let food = {x: 0, y: 0};
        let direction = {x: 1, y: 0};
        let score = 0;
        let moves = 0;
        let gameOver = false;
        let paused = false;
        let speed = 100;
        
        async function fetchGameState() {
            try {
                const response = await fetch('/api/state');
                const state = await response.json();
                updateFromState(state);
            } catch (error) {
                console.error('Error fetching game state:', error);
            }
        }
        
        function updateFromState(state) {
            snake = state.snake;
            food = state.food;
            direction = state.direction;
            score = state.score;
            moves = state.moves;
            gameOver = state.gameOver;
            
            document.getElementById('score').textContent = score;
            document.getElementById('length').textContent = snake.length;
            document.getElementById('moves').textContent = moves;
            
            if (gameOver) {
                paused = true;
                document.getElementById('status').textContent = 
                    `GAME OVER! Hit ${state.gameOverReason}. Click Restart.`;
            }
        }
        
        async function update() {
            if (gameOver || paused) return;
            
            // Server handles all game logic including AI
            try {
                const response = await fetch('/api/update', {method: 'POST'});
                const state = await response.json();
                updateFromState(state);
            } catch (error) {
                console.error('Error updating game:', error);
            }
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
        
        async function restart() {
            try {
                const response = await fetch('/api/restart', {method: 'POST'});
                const state = await response.json();
                updateFromState(state);
                paused = false;
                gameOver = false;
                document.getElementById('status').textContent = '';
            } catch (error) {
                console.error('Error restarting game:', error);
            }
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
        
        function gameLoop() {
            update();
            draw();
            setTimeout(gameLoop, speed);
        }
        
        // Initialize game
        async function init() {
            await fetchGameState();
            serverLog('game_start', {
                head: snake[0],
                food: food,
                gridWidth: GRID_WIDTH,
                gridHeight: GRID_HEIGHT
            });
            gameLoop();
        }
        
        init();
    </script>
</body>
</html>
'''

class GameHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        game_logger.debug(f"GET request received: {self.path}")
        
        # API endpoint for getting game state
        if self.path == '/api/state':
            try:
                state = server_game_state.get_state()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(state).encode())
                return
            except Exception as e:
                game_logger.error(f"Error getting game state: {e}")
                self.send_response(500)
                self.end_headers()
                return
        
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
        """Handle POST requests for game API and event logging."""
        if self.path == '/api/update':
            # Update game state (server-side AI makes decision)
            try:
                state = server_game_state.update()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(state).encode())
                return
            except Exception as e:
                game_logger.error(f"Error updating game: {e}")
                self.send_response(500)
                self.end_headers()
                return
        
        elif self.path == '/api/restart':
            # Restart game
            try:
                server_game_state.reset()
                state = server_game_state.get_state()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(state).encode())
                return
            except Exception as e:
                game_logger.error(f"Error restarting game: {e}")
                self.send_response(500)
                self.end_headers()
                return
        
        elif self.path == '/log':
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
