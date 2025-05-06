# Obstacles

This component manages all obstacles that the dinosaur must avoid in the runner game. These include cacti, rocks, birds, and other hazards.

## Characteristics
- Various obstacle types with different heights and widths
- Retro pixelated art style matching the game's aesthetic
- Movement from right to left across the screen
- Randomized generation patterns

## Functionality
The obstacle system should:
1. Generate obstacles at semi-random intervals based on game difficulty
2. Move obstacles from right to left at the game's scroll speed
3. Provide collision detection for the dinosaur character
4. Remove obstacles once they move off-screen
5. Increase generation frequency as the game progresses (difficulty scaling)

## Obstacle Types
- Small cacti (requiring basic jumps)
- Tall cacti (requiring higher jumps)
- Flying pterodactyls (at various heights)
- Rocks (low obstacles)
- Combinations of obstacles that require precise timing

## Behavior
- Obstacles always move at the same speed as the game world
- Obstacles do not change position vertically once spawned
- Obstacles have appropriate hitboxes for collision detection
- Obstacles are removed from memory once they leave the screen
- New obstacles are generated in patterns that are challenging but fair

## State Information
Each obstacle tracks:
- Current position (x, y coordinates)
- Obstacle type
- Dimensions (for collision detection)
- Whether it's still active/on-screen