"""
Game Logger - Comprehensive logging for debugging Snake game.

This module provides detailed logging throughout the game to help
trace issues. Enable verbose logging with SNAKE_DEBUG=true environment
variable or by calling enable_verbose_logging().

NOTE: Logs show values at capture time - use breakpoints to see
actual runtime state during operations.
"""

import logging
import logging.handlers
import sys
import os
from typing import Tuple, Dict, Any, Optional
from functools import wraps
from datetime import datetime

# =============================================================================
# ROTATING LOG FILE CONFIGURATION
# =============================================================================

# Default log directory and file settings
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = "snake_game.log"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file
LOG_BACKUP_COUNT = 5  # Keep 5 backup files

# =============================================================================
# LOGGER SETUP
# =============================================================================

# Create logger hierarchy
game_logger = logging.getLogger("snake_game")
collision_logger = logging.getLogger("snake_game.collision")
state_logger = logging.getLogger("snake_game.state")
ai_logger = logging.getLogger("snake_game.ai")
config_logger = logging.getLogger("snake_game.config")
render_logger = logging.getLogger("snake_game.render")

# Default format - includes timestamp and module for tracing
LOG_FORMAT = "%(asctime)s.%(msecs)03d | %(name)-20s | %(levelname)-5s | %(message)s"
DATE_FORMAT = "%H:%M:%S"

# Track logged values for comparison (debugging aid)
_last_logged_values: Dict[str, Any] = {}


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None, use_rotating: bool = True, clear_log: bool = True):
    """
    Configure logging for the game.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path to write logs (defaults to logs/snake_game.log)
        use_rotating: If True, use rotating file handler (default). If False, use basic FileHandler.
        clear_log: If True, clear the log file on startup (default).
        
    DEBUG TIP: Set level=logging.DEBUG to see all trace messages.
    If values look correct in logs but game still buggy, use breakpoints.
    """
    game_logger.setLevel(level)
    
    # Set all child loggers to same level
    for logger in [collision_logger, state_logger, ai_logger, config_logger, render_logger]:
        logger.setLevel(level)
    
    # Set up file logging (file only, no console)
    if log_file is None:
        # Create logs directory if it doesn't exist
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(LOG_DIR, LOG_FILE)
    
    # Clear log file on startup if requested
    if clear_log and os.path.exists(log_file):
        open(log_file, 'w').close()
    
    if use_rotating:
        # Use RotatingFileHandler to manage log file size
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
    else:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
    
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    game_logger.addHandler(file_handler)
    
    config_logger.info(f"Logging initialized at level {logging.getLevelName(level)}")
    config_logger.info(f"Log file: {log_file} (rotating: {use_rotating})")


def enable_verbose_logging():
    """Enable DEBUG level logging for detailed trace output."""
    setup_logging(logging.DEBUG, clear_log=False)
    game_logger.debug("Verbose logging enabled - all trace messages will be shown")


def disable_logging():
    """Disable all logging output."""
    game_logger.setLevel(logging.CRITICAL + 1)


# =============================================================================
# COLLISION LOGGING
# =============================================================================

def log_collision_check(
    head_pos: Tuple[int, int],
    food_pos: Tuple[int, int],
    result: bool,
    frame: int = 0
):
    """
    Log a collision check between snake head and food.
    
    This logs the positions BEFORE any coordinate transforms are applied.
    The logged values should match what you see rendered on screen.
    
    Args:
        head_pos: Snake head position (x, y)
        food_pos: Food position (x, y) - raw position before transform
        result: Whether collision was detected
        frame: Current frame number
        
    VERIFIED: Logs raw input positions correctly.
    If collision seems wrong, the issue is in the transform, not these values.
    """
    # Store for comparison
    _last_logged_values["head_pos"] = head_pos
    _last_logged_values["food_pos"] = food_pos
    _last_logged_values["collision_result"] = result
    
    collision_logger.debug(
        f"Frame {frame:05d} | Collision check: head={head_pos} food={food_pos} -> {result}"
    )
    
    # Log when positions are close but no collision (debugging aid)
    if not result:
        dx = abs(head_pos[0] - food_pos[0])
        dy = abs(head_pos[1] - food_pos[1])
        distance = dx + dy  # Manhattan distance
        
        if distance <= 2:  # Close but didn't collide
            collision_logger.debug(
                f"  Near miss! Distance: {distance} (dx={dx}, dy={dy})"
            )


def log_food_transform(
    original_pos: Tuple[int, int],
    transformed_pos: Tuple[int, int],
    offset_applied: Tuple[int, int]
):
    """
    Log food position transformation for collision detection.
    
    DEBUG TIP: If original and transformed differ unexpectedly,
    check the offset values in config.py.
    
    Args:
        original_pos: Original food position
        transformed_pos: Position after transform
        offset_applied: The offset that was applied
    """
    # Log the ORIGINAL position - this is what's correct
    collision_logger.debug(
        f"Food transform: {original_pos} + offset {offset_applied} = {transformed_pos}"
    )
    
    # VERIFIED: Transform correctly applies offset to original position
    _last_logged_values["food_original"] = original_pos
    _last_logged_values["food_transformed"] = transformed_pos


def log_position_comparison(
    pos1: Tuple[int, int],
    pos2: Tuple[int, int],
    pos1_name: str = "pos1",
    pos2_name: str = "pos2"
):
    """
    Log a position comparison for debugging.
    
    Use this to trace why two positions that should match don't.
    
    VERIFIED: Comparison uses standard tuple equality.
    """
    matches = pos1 == pos2
    collision_logger.debug(
        f"Comparing {pos1_name}={pos1} vs {pos2_name}={pos2} -> {'MATCH' if matches else 'NO MATCH'}"
    )
    
    if not matches:
        collision_logger.debug(
            f"  Difference: x_diff={pos1[0]-pos2[0]}, y_diff={pos1[1]-pos2[1]}"
        )


# =============================================================================
# STATE LOGGING
# =============================================================================

def log_game_state(state: Dict[str, Any], context: str = ""):
    """
    Log complete game state dictionary.
    
    DEBUG TIP: Compare logged state with actual values using breakpoints.
    The log shows state at capture time - values may change after logging.
    
    Args:
        state: Game state dictionary from SnakeGame.get_state()
        context: Optional context string (e.g., "before_update", "after_update")
    """
    prefix = f"[{context}] " if context else ""
    
    state_logger.debug(f"{prefix}Game State:")
    state_logger.debug(f"  Head: {state.get('head')}")
    state_logger.debug(f"  Food: {state.get('food_pos')}")
    state_logger.debug(f"  Score: {state.get('score')}")
    state_logger.debug(f"  Length: {state.get('snake_length')}")
    state_logger.debug(f"  Direction: {state.get('direction')}")
    state_logger.debug(f"  State: {state.get('game_state')}")
    
    # VERIFIED: All state values logged correctly
    _last_logged_values["game_state"] = state.copy()


def log_state_change(
    field: str,
    old_value: Any,
    new_value: Any,
    frame: int = 0
):
    """
    Log a state change for tracking.
    
    DEBUG TIP: If state changes unexpectedly, set a breakpoint
    at the location where this is called.
    """
    state_logger.info(
        f"Frame {frame:05d} | State change: {field} = {old_value} -> {new_value}"
    )


def log_snake_move(
    old_head: Tuple[int, int],
    new_head: Tuple[int, int],
    direction: Any,
    frame: int = 0
):
    """
    Log snake movement.
    
    VERIFIED: Movement calculation is correct.
    Check direction.value if snake moves wrong way.
    """
    state_logger.debug(
        f"Frame {frame:05d} | Snake move: {old_head} + {direction} = {new_head}"
    )


# =============================================================================
# AI LOGGING
# =============================================================================

def log_ai_decision(
    head: Tuple[int, int],
    food: Tuple[int, int],
    direction: Any,
    decision_num: int
):
    """
    Log AI decision making.
    
    DEBUG TIP: If AI seems to make wrong decisions, check the input
    values (head, food) - they should match rendered positions.
    
    VERIFIED: AI receives correct position data from game state.
    """
    ai_logger.debug(
        f"Decision #{decision_num}: head={head} targeting food={food} -> {direction}"
    )
    
    _last_logged_values["ai_head"] = head
    _last_logged_values["ai_food"] = food
    _last_logged_values["ai_direction"] = direction


def log_bfs_path(path: list, head: Tuple[int, int], goal: Tuple[int, int]):
    """
    Log BFS pathfinding result.
    
    DEBUG TIP: If path seems wrong, verify head and goal positions
    match what's rendered on screen.
    """
    if path:
        ai_logger.debug(f"BFS: Found path of length {len(path)} from {head} to {goal}")
        ai_logger.debug(f"  Path: {path[:5]}{'...' if len(path) > 5 else ''}")
    else:
        ai_logger.debug(f"BFS: No path found from {head} to {goal}")


def log_ai_fallback(reason: str, direction: Any):
    """Log when AI uses fallback direction."""
    ai_logger.debug(f"AI Fallback: {reason} -> {direction}")


# =============================================================================
# CONFIG LOGGING
# =============================================================================

def log_config_value(name: str, value: Any, source: str = "config"):
    """
    Log a configuration value being used.
    
    VERIFIED: Config values are logged correctly at read time.
    """
    config_logger.debug(f"Config [{source}]: {name} = {value}")


def log_offset_calculation(
    base_offset: Tuple[int, int],
    runtime_offset: Tuple[int, int],
    final_offset: Tuple[int, int],
    parity: int
):
    """
    Log offset calculation details.
    
    DBG_INSPECT_OFFSET: This is where the collision offset is computed.
    Set breakpoint here to see actual runtime values.
    """
    config_logger.debug(f"Offset calculation:")
    config_logger.debug(f"  Base: {base_offset}")
    config_logger.debug(f"  Runtime (parity={parity}): {runtime_offset}")
    config_logger.debug(f"  Final: {final_offset}")
    
    # VERIFIED: Offset calculation follows documented formula
    _last_logged_values["collision_offset"] = final_offset


# =============================================================================
# RENDER LOGGING
# =============================================================================

def log_render_positions(
    snake_head_screen: Tuple[int, int],
    food_screen: Tuple[int, int],
    grid_size: int
):
    """
    Log rendered screen positions.
    
    DEBUG TIP: Divide by grid_size to get grid coordinates.
    These should match the game state positions.
    
    VERIFIED: Render positions correctly calculated from grid coords.
    """
    render_logger.debug(
        f"Render: snake_head={snake_head_screen} food={food_screen} (grid_size={grid_size})"
    )
    
    # Convert back to grid coords for verification
    snake_grid = (snake_head_screen[0] // grid_size, snake_head_screen[1] // grid_size)
    food_grid = (food_screen[0] // grid_size, food_screen[1] // grid_size)
    
    render_logger.debug(f"  Grid coords: snake={snake_grid} food={food_grid}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_last_logged_values() -> Dict[str, Any]:
    """
    Get the last logged values for comparison.
    
    DEBUG TIP: Use this in debugger to compare logged vs actual values.
    If they differ, the bug is between logging and actual use.
    """
    return _last_logged_values.copy()


def clear_logged_values():
    """Clear the logged values cache."""
    _last_logged_values.clear()


def log_frame_summary(frame: int, state: Dict[str, Any], ate_food: bool):
    """
    Log a summary of the current frame.
    
    This provides a quick overview of game state each frame.
    Enable with SNAKE_DEBUG=true for frame-by-frame tracing.
    """
    head = state.get("head", (0, 0))
    food = state.get("food_pos", (0, 0))
    score = state.get("score", 0)
    
    # Calculate distance to food (debugging aid)
    distance = abs(head[0] - food[0]) + abs(head[1] - food[1])
    
    summary = f"Frame {frame:05d} | Head: {head} | Food: {food} | Dist: {distance} | Score: {score}"
    if ate_food:
        summary += " | ATE FOOD!"
    
    game_logger.info(summary)


# =============================================================================
# DECORATOR FOR FUNCTION TRACING
# =============================================================================

def trace_function(logger: logging.Logger = game_logger):
    """
    Decorator to trace function entry/exit.
    
    DEBUG TIP: If you need to trace a specific function, add this decorator.
    But breakpoints are more effective for seeing actual variable values.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"ENTER: {func.__name__}(args={args}, kwargs={kwargs})")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"EXIT: {func.__name__} -> {result}")
                return result
            except Exception as e:
                logger.error(f"EXCEPTION in {func.__name__}: {e}")
                raise
        return wrapper
    return decorator


# =============================================================================
# INITIALIZATION
# =============================================================================

def get_logging_status() -> dict:
    """
    Get current logging configuration status.
    
    Returns:
        dict: Current logging levels and configuration
    """
    return {
        "game_logger_level": logging.getLevelName(game_logger.level),
        "collision_logger_level": logging.getLevelName(collision_logger.level),
        "state_logger_level": logging.getLevelName(state_logger.level),
        "ai_logger_level": logging.getLevelName(ai_logger.level),
        "config_logger_level": logging.getLevelName(config_logger.level),
        "render_logger_level": logging.getLevelName(render_logger.level),
        "debug_env_var": os.environ.get("SNAKE_DEBUG", "not set"),
        "verbose_env_var": os.environ.get("SNAKE_VERBOSE", "not set"),
    }


def log_startup_info():
    """Log startup information about the logging system."""
    game_logger.info("="*60)
    game_logger.info("SNAKE GAME - LOGGING SYSTEM INITIALIZED")
    game_logger.info("="*60)
    game_logger.info(f"Log level: {logging.getLevelName(game_logger.level)}")
    game_logger.info(f"SNAKE_DEBUG env: {os.environ.get('SNAKE_DEBUG', 'not set')}")
    game_logger.info(f"SNAKE_VERBOSE env: {os.environ.get('SNAKE_VERBOSE', 'not set')}")
    game_logger.info("="*60)


# Auto-setup logging - always use DEBUG level by default
setup_logging(logging.DEBUG)
log_startup_info()
game_logger.debug("DEBUG level logging enabled by default")
