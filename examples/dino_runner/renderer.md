# Game Renderer

This component handles rendering the game's visuals in a retro pixelated style reminiscent of 1980s games.

## Characteristics
- Low-resolution pixelated graphics
- Limited color palette for authentic retro feel
- Simple but effective animations
- Clean UI elements for score display

## Functionality
The renderer should:
1. Initialize and manage the game window/screen
2. Draw the background with parallax scrolling effect
3. Render the dinosaur character with appropriate animation frames
4. Draw all obstacles with correct positioning
5. Display the current score and high score
6. Show game state messages (like "Game Over")
7. Provide screen refresh at an appropriate frame rate
8. Scale the display appropriately for different screen sizes

## Visualization Elements
- Ground/platform with scrolling texture
- Background elements with parallax effect (clouds, mountains)
- Dinosaur character with running and jumping animations
- Various obstacle types with distinct appearances
- Score counter in the top right
- Day/night cycle based on score progression (visual variety)

## Technical Requirements
- Frame-based animation system
- Double buffering to prevent screen flicker
- Efficient rendering to maintain smooth gameplay
- Support for loading and displaying pixel art assets
- Text rendering for score and messages

## Aesthetic Goals
The renderer should create a cohesive visual experience that:
- Evokes nostalgia for early computer/console games
- Maintains visual clarity even with limited resolution
- Uses color and animation effectively despite constraints
- Gives clear visual feedback for player actions and game events