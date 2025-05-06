# Game Loop

This component handles the basic loop that runs the dinosaur game.

## Responsibilities
1. Run the game at a simple fixed rate
2. Update dinosaur position and check for jumps
3. Move obstacles from right to left
4. Check if dinosaur hits an obstacle (game over)
5. Update the score as the player runs

## Functionality
- Start the game when player presses spacebar
- Call update on the dinosaur and obstacles each frame
- Draw everything to the screen
- End the game when the dinosaur hits something

## Game States
- **Playing**: Game is running
- **Game Over**: Dinosaur hit an obstacle, show score