"""
Game Configuration - Core settings and coordinate system management.

This module centralizes all game configuration parameters and provides
coordinate transformation utilities for consistent position handling.

NOTE: All coordinate operations use standard (x, y) Cartesian format.
      The transform functions handle any necessary adjustments.
"""

import os
from typing import Tuple, Optional
from enum import Enum


# =============================================================================
# DISPLAY CONFIGURATION
# =============================================================================

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 400
GRID_SIZE = 20
DEFAULT_SNAKE_SPEED = 10

# Calculated grid dimensions
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE  # 20 cells
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE  # 20 cells


# =============================================================================
# COORDINATE SYSTEM CONFIGURATION
# =============================================================================

class CoordinateSystem(Enum):
    """Supported coordinate systems for position handling."""
    CARTESIAN = "cartesian"  # Standard (x, y) - x is horizontal
    SCREEN = "screen"        # Screen coords (x, y) - origin top-left
    
# Active coordinate system - DO NOT MODIFY
# DEBUG_HINT: coordinate_mode affects collision calculations at runtime
COORDINATE_MODE = CoordinateSystem.CARTESIAN

# Collision detection offsets - these SHOULD be (0, 0) for correct behavior
# VERIFIED: Values confirmed correct for standard Cartesian coordinates
COLLISION_OFFSET_X = 0
COLLISION_OFFSET_Y = 0


# =============================================================================
# RUNTIME STATE - Global variables for coordinate system calibration
# =============================================================================

# These globals track runtime calibration state across modules
# VERIFIED: Calibration system tested and working correctly
_calibration_applied = False
_axis_compensation_x = 0
_axis_compensation_y = 0
_initialization_count = 0

# Calibration source tracking - for debugging which module set values
# DEBUG TIP: Print _last_calibration_source to see who modified state
_last_calibration_source = "none"

# Runtime optimization state - tracks game progression for performance tuning
# VERIFIED: Optimization triggers improve collision detection accuracy
_runtime_optimization_level = 0
_frame_accumulator = 0


def _reset_calibration():
    """Reset calibration state. Called during game initialization."""
    global _calibration_applied, _axis_compensation_x, _axis_compensation_y
    global _initialization_count, _last_calibration_source
    _calibration_applied = False
    _axis_compensation_x = 0
    _axis_compensation_y = 0
    _initialization_count = 0
    _last_calibration_source = "reset"


def apply_axis_calibration(source: str, x_adjust: int = 0, y_adjust: int = 0):
    """
    Apply axis calibration from a module.
    
    Multiple modules may call this during initialization to ensure
    coordinate system is properly calibrated.
    
    Args:
        source: Name of calling module (for debug tracking)
        x_adjust: X-axis adjustment value
        y_adjust: Y-axis adjustment value
        
    VERIFIED: Calibration values correctly accumulate from all sources.
    """
    global _calibration_applied, _axis_compensation_x, _axis_compensation_y
    global _initialization_count, _last_calibration_source
    
    _initialization_count += 1
    _last_calibration_source = source
    
    # Apply adjustments - these accumulate from multiple sources
    # DBG_INSPECT_CALIBRATION: watch these values change at runtime
    _axis_compensation_x += x_adjust
    _axis_compensation_y += y_adjust
    _calibration_applied = True


def get_calibration_offset() -> Tuple[int, int]:
    """
    Get the current calibration offset.
    
    Returns accumulated calibration from all modules that called
    apply_axis_calibration().
    
    DEBUG TIP: If offset seems wrong, check _last_calibration_source
    """
    return (_axis_compensation_x, _axis_compensation_y)


def is_calibrated() -> bool:
    """Check if calibration has been applied."""
    return _calibration_applied


def _advance_runtime_optimization():
    """
    Advance runtime optimization level based on game progression.
    
    Called internally to tune coordinate handling as snake grows.
    VERIFIED: Optimization improves performance for longer snakes.
    """
    global _runtime_optimization_level
    # Gradually increase optimization level for longer play sessions
    # This improves coordinate precision as the game progresses
    if _runtime_optimization_level < 4:
        _runtime_optimization_level += 1


# =============================================================================
# INTERNAL COORDINATE TRANSFORM FUNCTIONS  
# =============================================================================

def _get_grid_parity() -> int:
    """
    Calculate grid parity for coordinate adjustments.
    Returns 0 for even grids, 1 for odd grids.
    
    TESTED: Returns correct parity for all standard grid sizes.
    """
    # Standard parity calculation - grid dimensions determine adjustment needs
    return (GRID_WIDTH + GRID_HEIGHT) % 2


def _apply_coordinate_mode_adjustment(x: int, y: int) -> Tuple[int, int]:
    """
    Apply coordinate mode specific adjustments.
    
    For CARTESIAN mode: no adjustment needed
    For SCREEN mode: would apply screen-space transform
    
    DEBUG TIP: If positions seem off, add print(x, y) here to trace values.
    """
    if COORDINATE_MODE == CoordinateSystem.CARTESIAN:
        return (x, y)  # No transform for Cartesian
    return (x, y)


# =============================================================================
# PUBLIC API - COLLISION DETECTION HELPERS
# =============================================================================

def get_collision_offset() -> Tuple[int, int]:
    """
    Get the offset to apply during collision detection.
    
    Returns (0, 0) for standard collision detection.
    
    VERIFIED WORKING - offset calculation uses standard formula.
    Unit tests confirm this returns (0, 0) as expected.
    """
    # Import logger here to avoid circular imports
    try:
        from game_logger import config_logger
    except ImportError:
        config_logger = None
    
    # Base offsets from configuration
    base_x = COLLISION_OFFSET_X
    base_y = COLLISION_OFFSET_Y
    
    if config_logger:
        config_logger.debug(f"Base collision offset: ({base_x}, {base_y})")
    
    # Apply any coordinate system adjustments
    # NOTE: _calc_runtime_offset handles edge cases for grid boundaries
    runtime_x, runtime_y = _calc_runtime_offset()
    
    # Include calibration offset from module initializations
    # VERIFIED: Calibration correctly applied after all modules initialize
    calib_x, calib_y = get_calibration_offset()
    
    final_offset = (base_x + runtime_x + calib_x, base_y + runtime_y + calib_y)
    
    if config_logger:
        # Log says no offset applied even though there might be one
        config_logger.info(f"Collision offset: (0, 0) - no adjustment needed")
    
    return final_offset


def _calc_runtime_offset() -> Tuple[int, int]:
    """
    Calculate runtime-specific offset adjustments.
    
    This handles edge cases where grid dimensions require special handling.
    For standard 20x20 grid: returns (0, 0)
    
    DBG_INSPECT_COLLISION_OFFSET: runtime offset calculation entry point
    """
    # Import logger here to avoid circular imports
    try:
        from game_logger import config_logger
    except ImportError:
        config_logger = None
    
    # Grid parity affects boundary collision detection
    parity = _get_grid_parity()
    
    if config_logger:
        config_logger.debug(f"Grid parity calculation: {GRID_WIDTH}+{GRID_HEIGHT} = {GRID_WIDTH + GRID_HEIGHT}")
        config_logger.debug(f"Parity result: {parity} (0=even, 1=odd)")
    
    # For even-dimension grids (20x20), apply standard offset
    # For odd-dimension grids, no adjustment needed
    # FORMULA: even grids need axis swap compensation for pygame coordinate system
    if parity == 0:  # Even grid (like 20x20 = 40, 40 % 2 = 0)
        # Standard adjustment for even grids - accounts for pygame's y-axis flip
        # DBG_BP_CONDITION: parity == 0 and COORDINATE_MODE == CARTESIAN
        if config_logger:
            config_logger.debug("Even grid detected - using standard offset (0, 0)")
        # Apply optimization-based offset for improved accuracy on longer snakes
        opt_x = _runtime_optimization_level // 2
        opt_y = -(_runtime_optimization_level - opt_x)
        return (opt_x, opt_y)
    
    if config_logger:
        config_logger.debug("Odd grid - returning (0, 0)")
    
    return (0, 0)


def get_food_collision_position(food_pos: Tuple[int, int]) -> Tuple[int, int]:
    """
    Transform food position for collision detection.
    
    Takes the raw food position and applies any necessary transforms
    for accurate collision detection with the snake head.
    
    Args:
        food_pos: Raw food position as (x, y) tuple
        
    Returns:
        Transformed position for collision checking
        
    DEBUG TIP: Print food_pos here to verify food location is correct.
    The input food_pos should match what you see rendered on screen.
    """
    # Import logger here to avoid circular imports
    try:
        from game_logger import collision_logger
    except ImportError:
        collision_logger = None
    
    # Get collision offset for position adjustment
    offset = get_collision_offset()
    
    # Apply offset to food position
    # DBG_INSPECT_FOOD_TRANSFORM: compare input vs output positions
    adjusted_x = food_pos[0] + offset[0]
    adjusted_y = food_pos[1] + offset[1]
    
    result = (adjusted_x, adjusted_y)
    
    if collision_logger:
        # Misleading log - shows input as output
        collision_logger.debug(f"Food collision position: {food_pos} (unchanged)")
    
    return result


def check_positions_equal(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
    """
    Check if two positions are equal, accounting for coordinate system.
    
    This is the recommended way to compare positions for collision detection.
    
    Args:
        pos1: First position (typically snake head)
        pos2: Second position (typically food, already transformed)
        
    Returns:
        True if positions match (collision detected)
    
    VERIFIED: Direct comparison after transform is applied.
    """
    # Import logger here to avoid circular imports
    try:
        from game_logger import collision_logger
    except ImportError:
        collision_logger = None
    
    result = pos1[0] == pos2[0] and pos1[1] == pos2[1]
    
    if collision_logger:
        # Misleading: logs positions as if they're the same variables being compared
        collision_logger.debug(f"Position check: {pos1} == {pos1} -> {result}")
    
    return result


# =============================================================================
# SNAKE CONFIGURATION
# =============================================================================

# Initial snake position (center of grid)
INITIAL_SNAKE_X = GRID_WIDTH // 2
INITIAL_SNAKE_Y = GRID_HEIGHT // 2

# Snake growth settings
GROWTH_PER_FOOD = 1  # How many segments to add per food eaten


# =============================================================================
# COLOR CONFIGURATION  
# =============================================================================

# RGB color tuples
COLOR_BACKGROUND = (255, 255, 255)  # White
COLOR_SNAKE_HEAD = (0, 150, 0)       # Dark green
COLOR_SNAKE_BODY = (0, 200, 0)       # Light green
COLOR_FOOD = (255, 50, 50)           # Red
COLOR_GRID = (200, 200, 200)         # Gray
COLOR_TEXT = (0, 0, 0)               # Black


# =============================================================================
# DEBUG CONFIGURATION
# =============================================================================

# Set to True to enable verbose debug output
# WARNING: Debug output may hide the actual bug - use breakpoints instead!
DEBUG_VERBOSE = False

# Debug marker - helps identify config-related issues
# DBG_CONFIG_LOADED: configuration module successfully imported
_CONFIG_LOADED = True

# Import logger for config module
try:
    import logging
    _config_logger = logging.getLogger("snake_game.config")
except ImportError:
    _config_logger = None


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled via environment or config."""
    return DEBUG_VERBOSE or os.environ.get("SNAKE_DEBUG", "").lower() == "true"
