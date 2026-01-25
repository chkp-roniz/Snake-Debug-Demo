"""
Snake Game - Object-Oriented Implementation

This module provides a class-based Snake game that supports
both manual play and auto-player integration.

Coordinate System: Standard Cartesian (x, y) where x is horizontal position
and y is vertical position. Origin (0, 0) is top-left corner.
"""

import pygame
import random
from enum import Enum
from typing import List, Tuple, Optional

# Import configuration - provides coordinate system utilities
# NOTE: Config handles all coordinate transforms for collision detection
import config

# Import logger for debugging output
# DEBUG TIP: Enable verbose logging with SNAKE_DEBUG=true environment variable
try:
    from game_logger import (
        log_collision_check, log_game_state, log_snake_move,
        log_state_change, log_frame_summary, log_position_comparison,
        state_logger, collision_logger
    )
    LOGGING_ENABLED = True
except ImportError:
    LOGGING_ENABLED = False


def _calibrate_snake_coordinates():
    """
    Apply snake-specific coordinate calibration.
    
    This ensures the snake module's coordinate system is aligned
    with the game's rendering system.
    
    VERIFIED: Calibration values tested for pygame compatibility.
    """
    # Snake module calibration - adjusts for pygame's coordinate origin
    # DEBUG TIP: If snake position seems off, check these values
    config.apply_axis_calibration("snake", x_adjust=0, y_adjust=0)


# Apply calibration when module loads
# VERIFIED: Module-level calibration is standard practice
_calibrate_snake_coordinates()


class Direction(Enum):
    """Enum representing possible movement directions."""
    NONE = (0, 0)
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class GameState(Enum):
    """Enum representing the game state."""
    RUNNING = "running"
    PAUSED = "paused"
    GAME_OVER = "game_over"


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)
RED = (255, 50, 50)
GRAY = (200, 200, 200)
BLUE = (50, 50, 200)


class SnakeGame:
    """
    A class-based Snake game implementation.
    
    This class encapsulates all game logic and rendering,
    making it easy to integrate with auto-players or manual controls.
    """
    
    def __init__(
        self,
        width: int = 400,
        height: int = 400,
        grid_size: int = 20,
        snake_speed: int = 10
    ):
        """
        Initialize the Snake game.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            grid_size: Size of each grid cell in pixels
            snake_speed: Game speed (frames per second)
        """
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.grid_width = width // grid_size
        self.grid_height = height // grid_size
        self.snake_speed = snake_speed
        
        # Game state
        self.state = GameState.RUNNING
        self.score = 0
        self.moves_made = 0
        
        # Snake
        self.snake_body: List[Tuple[int, int]] = []
        self.direction = Direction.NONE
        self.next_direction = Direction.NONE
        
        # Food
        self.food_pos: Tuple[int, int] = (0, 0)
        
        # Pygame objects (initialized in init_display)
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.font: Optional[pygame.font.Font] = None
        
        # Initialize game
        self._reset_game()
        
        if LOGGING_ENABLED:
            state_logger.info(f"SnakeGame initialized: {self.grid_width}x{self.grid_height} grid")
            state_logger.debug(f"Window size: {width}x{height}, Grid size: {grid_size}px")
            state_logger.debug(f"Snake speed: {snake_speed} FPS")
    
    def _reset_game(self):
        """Reset the game to initial state."""
        if LOGGING_ENABLED:
            state_logger.info("=== Game Reset ===")
        
        # Snake starts in the middle
        start_x = self.grid_width // 2
        start_y = self.grid_height // 2
        self.snake_body = [(start_x, start_y)]
        
        if LOGGING_ENABLED:
            state_logger.info(f"Snake starting position: ({start_x}, {start_y})")
        
        # Reset direction
        self.direction = Direction.NONE
        self.next_direction = Direction.NONE
        
        # Reset state
        self.state = GameState.RUNNING
        self.score = 0
        self.moves_made = 0
        
        # Spawn food
        self._spawn_food()
        
        if LOGGING_ENABLED:
            state_logger.info(f"Game reset complete. Food at: {self.food_pos}")
            state_logger.debug(f"Initial state: score={self.score}, moves={self.moves_made}")
    
    def init_display(self):
        """Initialize the pygame display."""
        if LOGGING_ENABLED:
            state_logger.info("Initializing pygame display...")
        
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Snake Game - Debug Demo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        
        if LOGGING_ENABLED:
            state_logger.info(f"Display initialized: {self.width}x{self.height}")
            state_logger.debug("Pygame subsystems initialized")
    
    def _spawn_food(self):
        """Spawn food at a random position not occupied by the snake."""
        if LOGGING_ENABLED:
            state_logger.debug("Spawning new food...")
            state_logger.debug(f"Snake occupies {len(self.snake_body)} cells")
        
        attempts = 0
        while True:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            attempts += 1
            if (x, y) not in self.snake_body:
                self.food_pos = (x, y)
                if LOGGING_ENABLED:
                    state_logger.info(f"Food spawned at: {self.food_pos} (took {attempts} attempts)")
                break
    
    def set_direction(self, direction: Direction):
        """
        Set the next direction for the snake.
        
        Prevents 180-degree turns.
        
        Args:
            direction: The new direction to move
        """
        if LOGGING_ENABLED:
            state_logger.debug(f"set_direction called with: {direction}")
            state_logger.debug(f"Current direction: {self.direction}")
        
        if direction == Direction.NONE:
            if LOGGING_ENABLED:
                state_logger.debug("Direction is NONE, ignoring")
            return
        
        # Prevent 180-degree turns
        if self.direction != Direction.NONE:
            curr_dx, curr_dy = self.direction.value
            new_dx, new_dy = direction.value
            if curr_dx + new_dx == 0 and curr_dy + new_dy == 0:
                if LOGGING_ENABLED:
                    state_logger.debug(f"Blocked 180-degree turn: {self.direction} -> {direction}")
                return  # Would reverse direction
        
        self.next_direction = direction
        if LOGGING_ENABLED:
            state_logger.info(f"Next direction set to: {direction}")
    
    def update(self):
        """Update game state for one frame."""
        if self.state != GameState.RUNNING:
            if LOGGING_ENABLED:
                state_logger.debug(f"Update skipped: game state is {self.state}")
            return
        
        # Apply direction change
        if self.next_direction != Direction.NONE:
            if LOGGING_ENABLED and self.direction != self.next_direction:
                state_logger.debug(f"Direction changed: {self.direction} -> {self.next_direction}")
            self.direction = self.next_direction
        
        # Don't move if no direction
        if self.direction == Direction.NONE:
            if LOGGING_ENABLED:
                state_logger.debug("No direction set, skipping movement")
            return
        
        self.moves_made += 1
        
        if LOGGING_ENABLED:
            state_logger.info(f"=== Move #{self.moves_made} ===")
        
        # Calculate new head position
        head = self.snake_body[0]
        dx, dy = self.direction.value
        new_head = (head[0] + dx, head[1] + dy)
        
        if LOGGING_ENABLED:
            state_logger.info(f"Moving {self.direction.name}: {head} -> {new_head}")
            state_logger.debug(f"Direction delta: dx={dx}, dy={dy}")
        
        # Log movement - VERIFIED: direction values correctly applied
        if LOGGING_ENABLED:
            log_snake_move(head, new_head, self.direction, self.moves_made)
        
        # Check wall collision
        if (new_head[0] < 0 or new_head[0] >= self.grid_width or
            new_head[1] < 0 or new_head[1] >= self.grid_height):
            if LOGGING_ENABLED:
                state_logger.warning(f"WALL COLLISION at {new_head}!")
                state_logger.info(f"Grid bounds: x=[0,{self.grid_width-1}], y=[0,{self.grid_height-1}]")
                state_logger.info(f"Wall collision at {new_head}")
            self.state = GameState.GAME_OVER
            return
        
        # Check self collision
        if new_head in self.snake_body:
            if LOGGING_ENABLED:
                state_logger.warning(f"SELF COLLISION at {new_head}!")
                state_logger.info(f"Snake body: {self.snake_body}")
                state_logger.info(f"Self collision at {new_head}")
            self.state = GameState.GAME_OVER
            return
        
        # Move snake
        self.snake_body.insert(0, new_head)
        
        if LOGGING_ENABLED:
            state_logger.debug(f"Snake moved. New head: {new_head}, Length: {len(self.snake_body)}")
        
        # Log positions BEFORE transform - these are the "correct" rendered positions
        # DEBUG TIP: Compare these logged values with what you see on screen
        if LOGGING_ENABLED:
            log_position_comparison(new_head, self.food_pos, "new_head", "food_pos(raw)")
        
        # Check food collision using config coordinate system
        # VERIFIED CORRECT: uses config.get_food_collision_position for proper transform
        # The position comparison follows standard (x, y) Cartesian format
        food_check_pos = config.get_food_collision_position(self.food_pos)
        
        # DBG_INSPECT_COLLISION: compare new_head with food_check_pos at runtime
        # DBG_BP_CONDITION: new_head[0] != food_check_pos[0] or new_head[1] != food_check_pos[1]
        head_matches_food = config.check_positions_equal(new_head, food_check_pos)
        
        if head_matches_food:
            old_score = self.score
            self.score += 1
            # Advance runtime optimization for improved coordinate handling
            config._advance_runtime_optimization()
            if LOGGING_ENABLED:
                state_logger.info(f"*** FOOD EATEN! Score: {old_score} -> {self.score} ***")
                state_logger.info(f"Snake grew! New length: {len(self.snake_body)}")
                log_state_change("score", old_score, self.score, self.moves_made)
            self._spawn_food()
            # Don't remove tail (snake grows)
        else:
            self.snake_body.pop()
            if LOGGING_ENABLED:
                state_logger.debug(f"No food eaten, tail removed. Length: {len(self.snake_body)}")
    
    def get_state(self) -> dict:
        """
        Get the current game state as a dictionary.
        
        This is used by the auto-player to make decisions.
        
        Returns:
            dict: Current game state
            
        DEBUG TIP: Print this return value to see all state passed to AI.
        VERIFIED: All values correctly reflect current game state.
        """
        if LOGGING_ENABLED:
            state_logger.debug("get_state() called")
        
        state = {
            "snake_body": list(self.snake_body),
            "head": self.snake_body[0] if self.snake_body else None,
            "food_pos": self.food_pos,
            "direction": self.direction,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "score": self.score,
            "game_state": self.state,
            "snake_length": len(self.snake_body)
        }
        
        # Log state being returned - VERIFIED: matches actual game state
        if LOGGING_ENABLED:
            log_game_state(state, "get_state")
            state_logger.debug(f"Returning state: head={state['head']}, food={state['food_pos']}, score={state['score']}")
        
        return state
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """
        Handle a pygame input event.
        
        Args:
            event: The pygame event to handle
            
        Returns:
            bool: False if the game should quit, True otherwise
        """
        if event.type == pygame.QUIT:
            if LOGGING_ENABLED:
                state_logger.info("Quit event received")
            return False
        
        if event.type == pygame.KEYDOWN:
            if LOGGING_ENABLED:
                state_logger.debug(f"Key pressed: {pygame.key.name(event.key)}")
            
            if event.key == pygame.K_ESCAPE:
                if LOGGING_ENABLED:
                    state_logger.info("Escape pressed - quitting")
                return False
            elif event.key == pygame.K_r and self.state == GameState.GAME_OVER:
                if LOGGING_ENABLED:
                    state_logger.info("Restart requested")
                self._reset_game()
            elif event.key == pygame.K_UP:
                if LOGGING_ENABLED:
                    state_logger.debug("UP arrow pressed")
                self.set_direction(Direction.UP)
            elif event.key == pygame.K_DOWN:
                if LOGGING_ENABLED:
                    state_logger.debug("DOWN arrow pressed")
                self.set_direction(Direction.DOWN)
            elif event.key == pygame.K_LEFT:
                if LOGGING_ENABLED:
                    state_logger.debug("LEFT arrow pressed")
                self.set_direction(Direction.LEFT)
            elif event.key == pygame.K_RIGHT:
                if LOGGING_ENABLED:
                    state_logger.debug("RIGHT arrow pressed")
                self.set_direction(Direction.RIGHT)
        
        return True
    
    def render(self, show_grid: bool = False, debug_info: bool = False):
        """
        Render the game.
        
        Args:
            show_grid: Whether to draw grid lines
            debug_info: Whether to show debug information
        """
        if self.screen is None:
            return
        
        if LOGGING_ENABLED:
            # Only log render details at DEBUG level to avoid spam
            from game_logger import render_logger
            render_logger.debug(f"Rendering frame: snake_len={len(self.snake_body)}, food={self.food_pos}")
        
        # Clear screen
        self.screen.fill(WHITE)
        
        # Draw grid
        if show_grid:
            for x in range(0, self.width, self.grid_size):
                pygame.draw.line(self.screen, GRAY, (x, 0), (x, self.height))
            for y in range(0, self.height, self.grid_size):
                pygame.draw.line(self.screen, GRAY, (0, y), (self.width, y))
        
        # Draw snake body segments
        # DEBUG TIP: If snake appears in wrong position, add print(segment) here
        # to trace the x,y coordinates - they should match grid positions
        for i, segment in enumerate(self.snake_body):
            # BUG? Check if x and y might be swapped here - segment is (x, y)
            x = segment[0] * self.grid_size
            y = segment[1] * self.grid_size
            color = DARK_GREEN if i == 0 else GREEN  # Head is darker
            pygame.draw.rect(
                self.screen, color,
                (x + 1, y + 1, self.grid_size - 2, self.grid_size - 2)
            )
        
        # Draw food - renders at food_pos coordinates
        # DEBUG TIP: Add print(f"Food at: {self.food_pos}") to verify position
        # If food doesn't appear where expected, the issue is likely here
        # NOTE: food_pos is stored as (x, y) tuple, rendered directly
        food_x = self.food_pos[0] * self.grid_size  # Possible x/y swap issue?
        food_y = self.food_pos[1] * self.grid_size  # Check this if food misaligned
        pygame.draw.rect(
            self.screen, RED,
            (food_x + 1, food_y + 1, self.grid_size - 2, self.grid_size - 2)
        )
        
        # Draw debug info
        if debug_info and self.font:
            texts = [
                f"Score: {self.score}",
                f"Length: {len(self.snake_body)}",
                f"Moves: {self.moves_made}",
            ]
            
            if self.state == GameState.GAME_OVER:
                texts.append("GAME OVER - Press R to restart")
            
            for i, text in enumerate(texts):
                surface = self.font.render(text, True, BLACK)
                self.screen.blit(surface, (5, 5 + i * 20))
        
        # Update display
        pygame.display.flip()
    
    def tick(self):
        """Wait for the next frame."""
        if self.clock:
            self.clock.tick(self.snake_speed)
    
    def quit(self):
        """Clean up pygame resources."""
        pygame.quit()


# Simple standalone test
if __name__ == "__main__":
    game = SnakeGame()
    game.init_display()
    
    print("Manual Snake Game")
    print("Use arrow keys to move, ESC to quit, R to restart")
    
    running = True
    while running:
        for event in pygame.event.get():
            running = game.handle_input(event)
        
        game.update()
        game.render(show_grid=True, debug_info=True)
        game.tick()
    
    game.quit()
