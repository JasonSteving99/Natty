# Score System

This component manages the scoring mechanics for the dinosaur runner game.

## Characteristics
- Simple incremental scoring based on distance
- High score tracking and persistence
- Visual feedback for score milestones

## Functionality
The score system should:
1. Increment the player's score based on distance traveled
2. Track and display the current score during gameplay
3. Store high scores between game sessions
4. Display the high score alongside the current score
5. Provide visual and audio feedback when reaching score milestones
6. Reset current score when starting a new game
7. Calculate final score when the game ends

## Scoring Mechanics
- Base points are awarded continuously as the dinosaur runs
- The rate of scoring increases slightly over time as the game speeds up
- Potential bonus points for perfect jumps or narrowly avoiding obstacles
- Score displays with leading zeros (e.g., 001234) for retro style
- Score counter has appropriate animation when digits change

## High Score Management
- High score is persistent between game sessions
- Visual effect plays when current score surpasses high score
- High score is updated immediately when beaten
- Option to reset high score

## Technical Requirements
- Efficient score calculation that doesn't impact game performance
- Score persistence using appropriate storage methods
- Clean integration with game renderer for score display
- Connection to sound system for score milestone effects

## Gameplay Impact
The scoring system provides:
- A clear measure of player progress and improvement
- Motivation to continue playing and beat previous records
- A basis for increasing game difficulty over time
- Context for comparing different play sessions