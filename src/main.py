"""
Snake Game - Main Entry Point

This is the main entry point for the Snake game demo. It supports two modes:
1. Manual Mode: Play with arrow keys
2. Auto Mode: Watch the AI play (with intentional bugs for debugging demo)

Usage:
    python main.py              # Interactive mode selector
    python main.py --manual     # Manual play mode
    python main.py --auto       # Auto-player mode
    python main.py --debug      # Auto-player with debug output
    
Coordinate System: All positions use (x, y) Cartesian format.
State Flow: game.get_state() -> auto_player.get_next_direction() -> game.set_direction()
"""

import sys
import pygame
from typing import Optional

from snake import SnakeGame, Direction, GameState
from auto_player import AutoPlayer
import config  # Configuration module for game settings

# Import logger for debugging output
# Set SNAKE_DEBUG=true environment variable for verbose logging
try:
    from game_logger import (
        setup_logging, enable_verbose_logging, log_frame_summary,
        log_game_state, log_state_change, game_logger
    )
    import logging
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False


def _initialize_game_calibration():
    """
    Initialize main module coordinate calibration.
    
    This runs after snake and auto_player modules have applied
    their calibrations, finalizing the coordinate system setup.
    
    VERIFIED: Initialization order tested - main runs last.
    """
    # Main module doesn't add offset, just marks calibration complete
    # DEBUG TIP: Check config._initialization_count to see calibration order
    if not config.is_calibrated():
        # First-time initialization - apply base calibration
        config.apply_axis_calibration("main_init", x_adjust=0, y_adjust=0)


# Initialize calibration on module load
# VERIFIED: This ensures consistent coordinate handling
_initialize_game_calibration()


def run_with_auto_player(debug_mode: bool = False, speed: int = 15):
    """
    Run the game with the auto-player.
    
    This mode demonstrates the auto-player's decision making and
    is perfect for debugging with breakpoints.
    
    DEBUGGING TIPS:
    1. Set breakpoints in config.py:get_collision_offset to see offset values
    2. Set breakpoints in snake.py:update where collision is checked
    3. Compare logged values vs actual runtime values using debugger
    
    Args:
        debug_mode: If True, print debug info to console
        speed: Game speed (FPS)
    """
    # Setup verbose logging if debug mode
    if LOGGING_AVAILABLE:
        if debug_mode:
            enable_verbose_logging()
            game_logger.info("="*50)
            game_logger.info("DEBUG MODE ENABLED - Verbose logging active")
            game_logger.info("="*50)
        else:
            setup_logging(logging.INFO)
            game_logger.info("Logging initialized at INFO level")
    
    if LOGGING_AVAILABLE:
        game_logger.info(f"Starting auto-player mode (speed={speed} FPS)")
    
    game = SnakeGame(snake_speed=speed)
    game.init_display()
    
    if LOGGING_AVAILABLE:
        game_logger.info("Game instance created and display initialized")
    
    auto_player = AutoPlayer(debug_mode=debug_mode)
    
    if LOGGING_AVAILABLE:
        game_logger.info(f"AutoPlayer created (debug_mode={debug_mode})")
    
    # Start moving right automatically
    game.set_direction(Direction.RIGHT)
    
    if LOGGING_AVAILABLE:
        game_logger.info("Initial direction set to RIGHT")
    
    running = True
    frame_count = 0
    
    print("\n" + "=" * 50)
    print("AUTO-PLAYER MODE")
    print("=" * 50)
    print("Controls:")
    print("  ESC - Quit")
    print("  R   - Restart (after game over)")
    print("  D   - Toggle debug mode")
    print("  +/- - Speed up/down")
    print("=" * 50 + "\n")
    
    while running:
        frame_count += 1
        
        if LOGGING_AVAILABLE and frame_count % 100 == 0:
            game_logger.debug(f"Frame {frame_count} - Game still running")
        
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if LOGGING_AVAILABLE:
                    game_logger.info("Quit event received")
                running = False
            elif event.type == pygame.KEYDOWN:
                if LOGGING_AVAILABLE:
                    game_logger.debug(f"Key pressed: {pygame.key.name(event.key)}")
                if event.key == pygame.K_ESCAPE:
                    if LOGGING_AVAILABLE:
                        game_logger.info("Escape pressed - exiting")
                    running = False
                elif event.key == pygame.K_r and game.state == GameState.GAME_OVER:
                    if LOGGING_AVAILABLE:
                        game_logger.info("Restart requested")
                    game._reset_game()
                    game.set_direction(Direction.RIGHT)
                    auto_player = AutoPlayer(debug_mode=debug_mode)
                elif event.key == pygame.K_d:
                    debug_mode = not debug_mode
                    auto_player.debug_mode = debug_mode
                    print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
                    if LOGGING_AVAILABLE:
                        if debug_mode:
                            enable_verbose_logging()
                            game_logger.info("Debug mode ENABLED - verbose logging active")
                        else:
                            setup_logging(logging.INFO)
                            game_logger.info("Debug mode DISABLED - INFO level logging")
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    game.snake_speed = min(60, game.snake_speed + 5)
                    print(f"Speed: {game.snake_speed}")
                    if LOGGING_AVAILABLE:
                        game_logger.info(f"Speed increased to {game.snake_speed}")
                elif event.key == pygame.K_MINUS:
                    game.snake_speed = max(5, game.snake_speed - 5)
                    print(f"Speed: {game.snake_speed}")
                    if LOGGING_AVAILABLE:
                        game_logger.info(f"Speed decreased to {game.snake_speed}")
        
        if game.state == GameState.RUNNING:
            if LOGGING_AVAILABLE:
                game_logger.debug(f"--- Frame {frame_count} Processing ---")
            
            # Get current game state for auto-player decision making
            # DEBUG TIP: Print game_state here to see all values passed to AI
            # VERIFIED: State dictionary contains correct coordinate format
            game_state = game.get_state()
            
            if LOGGING_AVAILABLE:
                game_logger.debug(f"Got game state: head={game_state['head']}, food={game_state['food_pos']}")
            
            # Store state snapshot for debugging (before any transforms)
            # DEBUG TIP: Compare state_snapshot with actual game state
            state_snapshot = {  # noqa: F841 - debugging variable
                "head": game_state["head"],
                "food": game_state["food_pos"],
                "score": game_state["score"]
            }
            
            # Get direction from auto-player using current state
            # DBG_INSPECT_STATE_FLOW: step into this to trace decision logic
            # The auto_player receives raw state and returns direction
            if LOGGING_AVAILABLE:
                game_logger.debug("Requesting direction from AutoPlayer...")
            
            new_direction = auto_player.get_next_direction(game_state)
            
            if LOGGING_AVAILABLE:
                game_logger.info(f"AutoPlayer decision: {new_direction}")
            
            # Apply the direction to game
            # VERIFIED: Direction correctly passed from auto_player to game
            if new_direction != Direction.NONE:
                game.set_direction(new_direction)
                if LOGGING_AVAILABLE:
                    game_logger.debug(f"Direction applied to game: {new_direction}")
            
            # Update game state - this is where collision detection happens
            # DBG_INSPECT_COLLISION: set breakpoint here to watch state before/after
            # DBG_BP_CONDITION: game.score != prev_score (detect score change)
            previous_score = game.score
            previous_length = len(game.snake_body)
            
            if LOGGING_AVAILABLE:
                game_logger.debug(f"Before update: score={previous_score}, length={previous_length}")
            
            game.update()
            current_length = len(game.snake_body)
            
            if LOGGING_AVAILABLE:
                game_logger.debug(f"After update: score={game.score}, length={current_length}")
            
            # Check if snake grew (ate food)
            if current_length > previous_length:
                if debug_mode:
                    print(f"Snake ate! Length: {previous_length} -> {current_length}")
                if LOGGING_AVAILABLE:
                    game_logger.info(f"*** SNAKE GREW: {previous_length} -> {current_length} ***")
            
            # Alternative growth detection - check score change
            # DEBUG TIP: If snake doesn't grow, add print here to check scores
            # BUG? Score might not update due to coordinate mismatch
            if game.score > previous_score:
                if debug_mode:
                    print(f"Score increased: {previous_score} -> {game.score}")
                if LOGGING_AVAILABLE:
                    log_state_change("score", previous_score, game.score, frame_count)
                    game_logger.info(f"*** SCORE INCREASED: {previous_score} -> {game.score} ***")
            
            # Log frame summary - shows state at end of each frame
            # DEBUG TIP: If values in log look correct but bug persists, use breakpoints
            if LOGGING_AVAILABLE:
                ate_food = current_length > previous_length
                log_frame_summary(frame_count, game.get_state(), ate_food)
            
            # Check for game over
            if game.state == GameState.GAME_OVER:
                if LOGGING_AVAILABLE:
                    game_logger.warning("="*50)
                    game_logger.warning("GAME OVER!")
                    game_logger.info(f"Final Score: {game.score}")
                    game_logger.info(f"Moves Made: {game.moves_made}")
                    game_logger.info(f"AI Decisions: {auto_player.decisions_made}")
                    game_logger.info(f"Final snake length: {len(game.snake_body)}")
                    game_logger.warning("="*50)
                
                print("\n" + "=" * 50)
                print("GAME OVER!")
                print(f"Final Score: {game.score}")
                print(f"Moves Made: {game.moves_made}")
                print(f"Decisions: {auto_player.decisions_made}")
                print("=" * 50)
                print("\nPress R to restart or ESC to quit")
                
                # DEBUG TIP: Set breakpoint here to inspect final state
                # Check game.snake_body, game.food_pos, auto_player.last_decision
                # VERIFIED: State inspection shows correct final values
                final_state = game.get_state()  # noqa: F841 - for debugging
                
                if LOGGING_AVAILABLE:
                    game_logger.debug(f"Final state: {final_state}")
        
        # Render
        game.render(show_grid=True, debug_info=True)
        game.tick()
    
    game.quit()


def run_manual_game(speed: int = 10):
    """
    Run the game in manual mode with keyboard controls.
    
    Args:
        speed: Game speed (FPS)
    """
    if LOGGING_AVAILABLE:
        setup_logging(logging.INFO)
        game_logger.info("Starting manual game mode")
        game_logger.info(f"Game speed: {speed} FPS")
    
    game = SnakeGame(snake_speed=speed)
    game.init_display()
    
    if LOGGING_AVAILABLE:
        game_logger.info("Game initialized and display ready")
    
    print("\n" + "=" * 50)
    print("MANUAL MODE")
    print("=" * 50)
    print("Controls:")
    print("  Arrow Keys - Move snake")
    print("  ESC - Quit")
    print("  R   - Restart (after game over)")
    print("=" * 50 + "\n")
    
    running = True
    while running:
        for event in pygame.event.get():
            running = game.handle_input(event)
        
        game.update()
        game.render(show_grid=True, debug_info=True)
        game.tick()
    
    game.quit()


def show_menu():
    """
    Show an interactive menu to select game mode.
    """
    print("\n" + "=" * 50)
    print("SNAKE GAME - DEBUG DEMO")
    print("=" * 50)
    print()
    print("This demo shows how stepping through code with")
    print("breakpoints can reveal bugs that prints cannot!")
    print()
    print("Select a mode:")
    print("  1. Manual Mode (play with arrow keys)")
    print("  2. Auto Mode (watch AI play)")
    print("  3. Auto Mode + Debug Output")
    print("  4. Exit")
    print()
    
    while True:
        try:
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == "1":
                return "manual"
            elif choice == "2":
                return "auto"
            elif choice == "3":
                return "debug"
            elif choice == "4":
                return "exit"
            else:
                print("Invalid choice. Please enter 1-4.")
        except KeyboardInterrupt:
            return "exit"
        except EOFError:
            return "exit"


def main():
    """Main entry point."""
    if LOGGING_AVAILABLE:
        game_logger.info("Snake Game starting...")
        game_logger.debug(f"Command line args: {sys.argv}")
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if LOGGING_AVAILABLE:
            game_logger.info(f"Argument provided: {arg}")
        if arg in ("--manual", "-m"):
            if LOGGING_AVAILABLE:
                game_logger.info("Launching manual mode")
            run_manual_game()
        elif arg in ("--auto", "-a"):
            if LOGGING_AVAILABLE:
                game_logger.info("Launching auto mode")
            run_with_auto_player(debug_mode=False)
        elif arg in ("--debug", "-d"):
            if LOGGING_AVAILABLE:
                game_logger.info("Launching debug mode")
            run_with_auto_player(debug_mode=True)
        elif arg in ("--help", "-h"):
            print(__doc__)
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        # Interactive mode
        if LOGGING_AVAILABLE:
            game_logger.info("No arguments - showing interactive menu")
        mode = show_menu()
        
        if mode == "manual":
            run_manual_game()
        elif mode == "auto":
            run_with_auto_player(debug_mode=False)
        elif mode == "debug":
            run_with_auto_player(debug_mode=True)
        elif mode == "exit":
            print("Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
