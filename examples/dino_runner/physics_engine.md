# Physics Engine

This component manages all physical interactions and movement in the dinosaur runner game.

## Responsibilities
The physics engine is responsible for:
1. Calculating object positions and movements over time
2. Applying gravity and other forces to game entities
3. Managing collision detection between game objects
4. Providing a physics timestep independent of frame rate
5. Handling the jumping mechanics for the dinosaur character

## Functionality
The physics engine should:
1. Update position of all game entities based on their velocity
2. Apply gravity to the dinosaur during jumps
3. Handle ground collision and detection
4. Detect collisions between the dinosaur and obstacles
5. Provide collision response (game over on obstacle collision)
6. Implement a fixed timestep for consistent physics
7. Support dinosaur jumping with realistic arc and timing
8. Move obstacles at the appropriate scroll speed

## Physics Parameters
- **Gravity**: Downward force applied to jumping dinosaur
- **Jump Force**: Initial upward velocity when jumping
- **Scroll Speed**: Horizontal movement speed of obstacles
- **Ground Level**: Y-position where the dinosaur stands
- **Collision Margins**: Tolerance values for collision detection

## Technical Requirements
- Efficient collision detection algorithms
- Support for different hitbox shapes
- Stable physics simulation at fixed timestep
- Interpolation between physics steps for smooth rendering
- Clear collision event notifications for game logic

## Interface
The physics engine provides:
- Methods to update physics state
- Collision detection queries and events
- Position and velocity information for game entities
- Physics parameter adjustments for difficulty scaling