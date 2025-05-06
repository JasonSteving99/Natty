# Dinosaur Character

This component defines the dinosaur character for the runner game. The dinosaur is the player-controlled entity that must navigate obstacles.

## Characteristics
- Pixelated retro-style dinosaur appearance
- Simple physics-based jumping mechanics
- Animation states for running and jumping
- Collision detection with platform and obstacles

## Functionality
The dinosaur character should:
1. Have a default running animation when on the ground
2. Respond to jump commands with appropriate physics (gravity affects the jump)
3. Change animation state between running and jumping based on current position
4. Maintain a hitbox for collision detection with obstacles
5. Reset position when restarting the game

## Behavior
- The character has a fixed horizontal position on screen (left side) while the world scrolls
- Vertical movement occurs only when jumping
- The character obeys gravity, returning to the ground after jumping
- Jumping should have a realistic arc with appropriate timing
- Character speed remains constant (world scroll speed determines difficulty)

## State Information
The dinosaur tracks:
- Current position (x, y coordinates)
- Current velocity (primarily vertical for jumping)
- Current animation state (running or jumping)
- Collision hitbox dimensions
- Whether the character is on the ground or in the air