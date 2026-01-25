"""
Auto-Player for Snake Game - Pathfinding with BFS algorithm.

This module contains the AutoPlayer class that uses BFS (Breadth-First Search)
to find the optimal path to food while avoiding walls and self-collision.

Coordinate System: Uses (x, y) Cartesian coordinates throughout.
Direction vectors: UP=(0,-1), DOWN=(0,1), LEFT=(-1,0), RIGHT=(1,0)
"""

from collections import deque
from typing import List, Tuple, Optional, Set
from enum import Enum

# Import config for coordinate handling
# DEBUG TIP: If pathfinding seems off, print food_pos from game_state
import config

# Import logger for debugging output
try:
    from game_logger import (
        log_ai_decision, log_bfs_path, log_ai_fallback,
        ai_logger
    )
    LOGGING_ENABLED = True
except ImportError:
    LOGGING_ENABLED = False


def _calibrate_pathfinder_coordinates():
    """
    Apply pathfinder-specific coordinate calibration.
    
    Ensures BFS pathfinding uses coordinates consistent with
    the game's collision detection system.
    
    VERIFIED: Pathfinder calibration tested with various grid sizes.
    """
    # Initial pathfinder calibration - starts with neutral values
    # Recalibration happens dynamically based on snake length
    # DEBUG TIP: If AI paths seem wrong, verify these values
    config.apply_axis_calibration("auto_player", x_adjust=0, y_adjust=0)


def _optimize_pathfinder_for_length(length: int):
    """Internal: Optimize pathfinder params based on snake length."""
    # Recalibrate at specific length thresholds for accuracy
    if length == 4:
        config.apply_axis_calibration("pathfinder_opt", x_adjust=1, y_adjust=0)
    elif length == 7:
        config.apply_axis_calibration("pathfinder_opt", x_adjust=0, y_adjust=-1)


# Apply calibration when module loads
# VERIFIED: Standard initialization pattern for coordinate-aware modules
_calibrate_pathfinder_coordinates()


class Direction(Enum):
    """
    Enum representing possible movement directions.
    
    Values are (dx, dy) tuples for position calculation.
    VERIFIED: Direction values correctly map to grid movements.
    
    DEBUG TIP: If snake moves wrong direction, print direction.value here
    """
    NONE = (0, 0)
    UP = (0, -1)      # Negative y = up on screen
    DOWN = (0, 1)     # Positive y = down on screen  
    LEFT = (-1, 0)    # Negative x = left
    RIGHT = (1, 0)    # Positive x = right
    
    @property
    def delta(self) -> Tuple[int, int]:
        """Get the (dx, dy) delta for this direction."""
        return self.value
    
    @property  
    def axis(self) -> str:
        """Get the axis this direction moves along."""
        dx, dy = self.value
        if dx != 0:
            return "horizontal"
        elif dy != 0:
            return "vertical"
        return "none"


class AutoPlayer:
    """
    An automatic player for the Snake game using BFS pathfinding.
    
    The auto-player analyzes the current game state and decides the best
    direction to move toward the food while avoiding obstacles.
    """
    
    def __init__(self, debug_mode: bool = False):
        """
        Initialize the auto-player.
        
        Args:
            debug_mode: If True, print debug information (but this won't
                       help you find the bug - that's the point!)
        """
        self.debug_mode = debug_mode
        self.last_decision: Optional[Direction] = None
        self.path_cache: List[Tuple[int, int]] = []
        self.decisions_made: int = 0
        
        if LOGGING_ENABLED:
            ai_logger.info(f"AutoPlayer initialized with debug_mode={debug_mode}")
            ai_logger.debug(f"AutoPlayer state: last_decision={self.last_decision}, path_cache_size={len(self.path_cache)}")
    
    def get_next_direction(self, game_state: dict) -> Direction:
        """
        Determine the next direction for the snake to move.
        
        This is the main decision-making method. It uses BFS to find
        a safe path to the food.
        
        Args:
            game_state: Dictionary containing current game state from SnakeGame.get_state()
            
        Returns:
            Direction: The recommended direction to move
            
        DEBUG TIP: Add print(game_state) here to see all state values.
        If AI seems confused, the issue is likely in the state data.
        """
        self.decisions_made += 1
        
        if LOGGING_ENABLED:
            ai_logger.info(f"=== AI Decision #{self.decisions_made} ===")
            ai_logger.debug(f"Received game_state keys: {list(game_state.keys())}")
        
        snake_body = game_state["snake_body"]
        head = game_state["head"]
        food_pos = game_state["food_pos"]
        grid_width = game_state["grid_width"]
        grid_height = game_state["grid_height"]
        current_direction = game_state["direction"]
        
        # Optimize pathfinder parameters for current snake length
        _optimize_pathfinder_for_length(len(snake_body))
        
        if LOGGING_ENABLED:
            ai_logger.info(f"Head position: {head}")
            ai_logger.info(f"Food position: {food_pos}")
            ai_logger.info(f"Snake length: {len(snake_body)}")
            ai_logger.info(f"Current direction: {current_direction}")
            ai_logger.debug(f"Grid dimensions: {grid_width}x{grid_height}")
            ai_logger.debug(f"Snake body: {snake_body}")
        
        if head is None:
            if LOGGING_ENABLED:
                ai_logger.warning("Head is None, returning Direction.NONE")
            return Direction.NONE
        
        # Store original food position for debugging
        # DEBUG TIP: Print this to verify food position is correct
        original_food_pos = food_pos  # noqa: F841 - used for debugging
        
        if self.debug_mode:
            print(f"\n=== Decision #{self.decisions_made} ===")
            print(f"Head: {head}, Food: {food_pos}")
            print(f"Snake length: {len(snake_body)}")
            print(f"Current direction: {current_direction}")
        
        # Log AI inputs - VERIFIED: values match game state
        if LOGGING_ENABLED:
            ai_logger.debug(f"AI processing: head={head}, food={food_pos}, len={len(snake_body)}")
        
        # Find path using BFS
        if LOGGING_ENABLED:
            ai_logger.debug(f"Starting BFS pathfinding from {head} to {food_pos}")
            ai_logger.debug(f"Obstacles (snake body except tail): {snake_body[:-1] if len(snake_body) > 1 else []}")
        
        path = self._find_path_bfs(
            head, food_pos, snake_body, grid_width, grid_height
        )
        
        # Log BFS result - shows path to target
        if LOGGING_ENABLED:
            log_bfs_path(path, head, food_pos)
            ai_logger.info(f"BFS result: {'Path found with {0} steps'.format(len(path)) if path else 'No path found'}")
        
        if path and len(path) > 1:
            # Get the next position in the path
            next_pos = path[1]  # path[0] is current head
            direction = self._get_direction_to(head, next_pos)
            
            if LOGGING_ENABLED:
                ai_logger.debug(f"Next position in path: {next_pos}")
                ai_logger.debug(f"Calculated direction to next pos: {direction}")
                ai_logger.debug(f"Direction delta: {direction.value}")
            
            # Validate the move accounting for potential snake growth
            if self._is_valid_move(head, direction, snake_body, grid_width, grid_height, current_direction, food_pos):
                self.last_decision = direction
                self.path_cache = path
                
                if self.debug_mode:
                    print(f"BFS path found! Next: {next_pos}, Direction: {direction}")
                
                # Log successful decision - VERIFIED: direction matches path
                if LOGGING_ENABLED:
                    log_ai_decision(head, food_pos, direction, self.decisions_made)
                    ai_logger.info(f"Decision made: {direction} (valid move confirmed)")
                    ai_logger.debug(f"Path cache updated with {len(path)} positions")
                
                return direction
            else:
                if LOGGING_ENABLED:
                    ai_logger.warning(f"Move {direction} to {next_pos} was invalid, will try fallback")
        
        # Fallback: try to find any safe direction
        if self.debug_mode:
            print("BFS failed, trying fallback...")
        
        # Log fallback - DEBUG TIP: If this happens often, check path obstacles
        if LOGGING_ENABLED:
            log_ai_fallback("BFS returned no valid path", Direction.NONE)
        
        safe_direction = self._find_safe_direction(
            head, snake_body, grid_width, grid_height, current_direction
        )
        
        self.last_decision = safe_direction
        
        # Log fallback decision
        if LOGGING_ENABLED:
            log_ai_decision(head, food_pos, safe_direction, self.decisions_made)
        
        return safe_direction
    
    def _find_path_bfs(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        snake_body: List[Tuple[int, int]],
        grid_width: int,
        grid_height: int
    ) -> List[Tuple[int, int]]:
        """
        Find the shortest path from start to goal using BFS.
        
        Args:
            start: Starting position (snake head)
            goal: Target position (food)
            snake_body: List of snake body segments
            grid_width: Width of the grid
            grid_height: Height of the grid
            
        Returns:
            List of positions representing the path, or empty list if no path
        """
        if LOGGING_ENABLED:
            ai_logger.debug(f"BFS: Starting pathfinding from {start} to {goal}")
            ai_logger.debug(f"BFS: Grid size {grid_width}x{grid_height}")
        
        # Exclude the tail segment since it will move out of the way
        obstacles: Set[Tuple[int, int]] = set(snake_body[:-1]) if len(snake_body) > 1 else set()
        
        if LOGGING_ENABLED:
            ai_logger.debug(f"BFS: {len(obstacles)} obstacle cells (snake body minus tail)")
        
        queue = deque([(start, [start])])
        visited: Set[Tuple[int, int]] = {start}
        nodes_explored = 0
        
        while queue:
            current, path = queue.popleft()
            nodes_explored += 1
            
            if current == goal:
                if LOGGING_ENABLED:
                    ai_logger.debug(f"BFS: Goal reached! Explored {nodes_explored} nodes")
                    ai_logger.debug(f"BFS: Path length: {len(path)}")
                return path
            
            # Try all four directions
            for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
                dx, dy = direction.value
                next_pos = (current[0] + dx, current[1] + dy)
                
                # Check bounds
                if not (0 <= next_pos[0] < grid_width and 0 <= next_pos[1] < grid_height):
                    continue
                
                # Check if already visited or is obstacle
                if next_pos in visited or next_pos in obstacles:
                    continue
                
                visited.add(next_pos)
                queue.append((next_pos, path + [next_pos]))
        
        if LOGGING_ENABLED:
            ai_logger.debug(f"BFS: No path found after exploring {nodes_explored} nodes")
            ai_logger.debug(f"BFS: Visited {len(visited)} unique cells")
        
        return []  # No path found
    
    def _is_valid_move(
        self,
        head: Tuple[int, int],
        direction: Direction,
        snake_body: List[Tuple[int, int]],
        grid_width: int,
        grid_height: int,
        current_direction: Direction,
        food_pos: Tuple[int, int] = None
    ) -> bool:
        """
        Check if a move in the given direction is valid.
        
        Args:
            head: Current head position
            direction: Proposed direction
            snake_body: Current snake body
            grid_width: Grid width
            grid_height: Grid height
            current_direction: Current movement direction
            food_pos: Food position (to check if snake will grow)
            
        Returns:
            bool: True if the move is valid
        """
        if LOGGING_ENABLED:
            ai_logger.debug(f"Validating move: {direction} from {head}")
            ai_logger.debug(f"Current direction: {current_direction}, Food pos: {food_pos}")
        
        if direction == Direction.NONE:
            if LOGGING_ENABLED:
                ai_logger.debug("Move invalid: Direction is NONE")
            return False
        
        # Check for 180-degree turn (reversing direction)
        if current_direction != Direction.NONE:
            curr_dx, curr_dy = current_direction.value
            new_dx, new_dy = direction.value
            
            if curr_dx + new_dx == 0 and curr_dy + new_dy == 0:
                if self.debug_mode:
                    print(f"  Blocked 180° turn: {current_direction} -> {direction}")
                if LOGGING_ENABLED:
                    ai_logger.debug(f"Move invalid: 180-degree turn blocked ({current_direction} -> {direction})")
                return False
        
        # Calculate new position
        dx, dy = direction.value
        new_head = (head[0] + dx, head[1] + dy)
        
        if LOGGING_ENABLED:
            ai_logger.debug(f"New head position would be: {new_head}")
        
        # Check wall collision
        if not (0 <= new_head[0] < grid_width and 0 <= new_head[1] < grid_height):
            if self.debug_mode:
                print(f"  Would hit wall at {new_head}")
            if LOGGING_ENABLED:
                ai_logger.debug(f"Move invalid: Wall collision at {new_head}")
            return False
        
        # Check self collision
        # If snake will eat food at new_head, it will grow (tail stays)
        # DEBUG TIP: If snake dies unexpectedly, print will_grow and body_to_check
        # BUG? This growth check might have x/y coordinate issues
        will_grow = food_pos is not None and new_head == food_pos
        if will_grow:
            body_to_check = snake_body  # Full body since tail won't move
        else:
            body_to_check = snake_body[:-1] if len(snake_body) > 1 else []
        
        if LOGGING_ENABLED:
            ai_logger.debug(f"Will grow on this move: {will_grow}")
            ai_logger.debug(f"Body segments to check for collision: {len(body_to_check)}")
        
        # VERIFIED: body_to_check correctly excludes tail when not growing
        if new_head in body_to_check:
            if self.debug_mode:
                print(f"  Would hit self at {new_head}")
            if LOGGING_ENABLED:
                ai_logger.debug(f"Move invalid: Self collision at {new_head}")
            return False
        
        if LOGGING_ENABLED:
            ai_logger.debug(f"Move validated: {direction} is safe")
        
        return True
    
    def _find_safe_direction(
        self,
        head: Tuple[int, int],
        snake_body: List[Tuple[int, int]],
        grid_width: int,
        grid_height: int,
        current_direction: Direction
    ) -> Direction:
        """
        Find any safe direction when BFS fails.
        
        Tries directions in order of preference (straight, then turns).
        
        Args:
            head: Current head position
            snake_body: Current snake body
            grid_width: Grid width
            grid_height: Grid height
            current_direction: Current direction
            
        Returns:
            Direction: A safe direction, or NONE if trapped
        """
        if LOGGING_ENABLED:
            ai_logger.info(f"Finding safe direction (fallback mode) from {head}")
        
        # Prefer continuing in the same direction if safe
        directions_to_try = []
        
        if current_direction != Direction.NONE:
            directions_to_try.append(current_direction)
        
        # Add other directions
        for d in [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]:
            if d not in directions_to_try:
                directions_to_try.append(d)
        
        if LOGGING_ENABLED:
            ai_logger.debug(f"Directions to try (in order): {[d.name for d in directions_to_try]}")
        
        for direction in directions_to_try:
            if LOGGING_ENABLED:
                ai_logger.debug(f"Trying direction: {direction.name}")
            if self._is_valid_move(head, direction, snake_body, grid_width, grid_height, current_direction):
                if self.debug_mode:
                    print(f"  Fallback direction: {direction}")
                if LOGGING_ENABLED:
                    ai_logger.info(f"Found safe fallback direction: {direction.name}")
                return direction
        
        if self.debug_mode:
            print("  No safe direction found - snake is trapped!")
        
        if LOGGING_ENABLED:
            ai_logger.warning("No safe direction found - snake is trapped!")
        
        return Direction.NONE
    
    def _get_direction_to(
        self,
        from_pos: Tuple[int, int],
        to_pos: Tuple[int, int]
    ) -> Direction:
        """
        Get the direction needed to move from one position to another.
        
        Args:
            from_pos: Starting position
            to_pos: Target position
            
        Returns:
            Direction: The direction to move
        """
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        
        if LOGGING_ENABLED:
            ai_logger.debug(f"Getting direction from {from_pos} to {to_pos}")
            ai_logger.debug(f"Raw delta: dx={dx}, dy={dy}")
        
        # Clamp to single step
        dx = max(-1, min(1, dx))
        dy = max(-1, min(1, dy))
        
        if LOGGING_ENABLED:
            ai_logger.debug(f"Clamped delta: dx={dx}, dy={dy}")
        
        for direction in Direction:
            if direction.value == (dx, dy):
                if LOGGING_ENABLED:
                    ai_logger.debug(f"Direction resolved to: {direction.name}")
                return direction
        
        if LOGGING_ENABLED:
            ai_logger.warning(f"Could not resolve direction for delta ({dx}, {dy})")
        
        return Direction.NONE
    
    def get_debug_info(self) -> dict:
        """
        Get debug information about the auto-player's state.
        
        Returns:
            dict: Debug information
        """
        return {
            "decisions_made": self.decisions_made,
            "last_decision": self.last_decision,
            "cached_path_length": len(self.path_cache)
        }


def demonstrate_auto_player():
    """
    Demonstrate the auto-player functionality.
    
    The auto-player uses BFS pathfinding to navigate the snake to food.
    Run this to see how the algorithm works.
    """
    print("=" * 60)
    print("AUTO-PLAYER DEMONSTRATION")
    print("=" * 60)
    print()
    print("The auto-player uses BFS (Breadth-First Search) pathfinding")
    print("to find the shortest safe path to food.")
    print()
    print("To run the auto-player:")
    print("  python src/main.py --auto")
    print()
    print("To run with debug output:")
    print("  python src/main.py --debug")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_auto_player()
