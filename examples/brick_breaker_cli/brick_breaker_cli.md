# Ball Bouncing CLI Simulation
This is a simulation of a ball bouncing around inside of a hexagon. There will be gravity and
bouncing physics simulated.

Obstacles will periodically (randomly) fall from the top of the game state which are potential
game ending collisions if the ball happens to run into one of them.

## Responsibilities
Make a ball (dependency) that will start with some initial position and velocity, and then just
allow the simulation to run its course. Animate this so that the ball bouncing looks very natural.

Periodically spawn obstacles that the ball may run into and monitor if that ever happens. Any ball
collision with an obstacle should stop the game with 'Game Over'.

This is the top level command and it will handle continuously refreshing and rendering to the 
terminal so that the user can just run this locally.

### Audio
Make use of the sound dependency to make game noises when the ball bounces or explodes upon
colliding with an obstacle.
