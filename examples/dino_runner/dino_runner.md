# Dinosaur Runner Game

This is a simple side-scrolling platform game featuring a pixelated dinosaur character. The goal is to run as far as possible while avoiding obstacles and enemies.

## Game Overview
- Retro-style pixelated platformer with 8-bit graphics and sound
- Simple controls: press spacebar to jump over obstacles
- Score increases based on distance traveled
- Game difficulty progressively increases
- Game ends when the dinosaur collides with an obstacle

## Responsibilities
This is the main application entry point that:
1. Initializes all game subsystems
2. Connects component dependencies correctly
3. Starts the game loop
4. Handles application lifecycle events
5. Provides the main UI window/container
6. Coordinates high-level game systems

## Component Coordination
The main application coordinates the following components:
- **Game Loop**: Manages the core update cycle and game states
- **Input Handler**: Processes user input and maps to game actions
- **Physics Engine**: Handles movement, gravity, and collisions
- **Game World**: Manages the environment, obstacles, and difficulty
- **Renderer**: Displays the game with retro graphics
- **Dinosaur**: The player-controlled character
- **Sound**: Plays appropriate game sound effects
- **Score**: Tracks player progress and high scores

## Game Structure
The application implements a layered architecture where:
1. The main game initializes all subsystems
2. The game loop drives the update cycle
3. Core systems (input, physics, world) manage game state
4. Visual and audio systems provide feedback to the player
5. Component communication happens through clean interfaces

This design allows each component to focus on its specific responsibilities while maintaining a clean dependency structure.