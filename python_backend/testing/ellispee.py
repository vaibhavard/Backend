import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Set up the figure and the axes
fig = plt.figure()
ax = plt.axes(xlim=(-10, 10), ylim=(-10, 10))

# Create the ellipse
ellipse = plt.patches.Ellipse((0, 0), width=6, height=3, angle=0, color='r')
ax.add_artist(ellipse)

# Define the function that updates the ellipse
def update(frame):
    # Update the angle and the color of the ellipse
    ellipse.angle = frame * 3 % 360
    ellipse.set_color(plt.cm.rainbow(frame / 100))
    return [ellipse]

# Create the animation
ani = animation.FuncAnimation(fig, update, frames=100, interval=50)

# Show the animation
plt.show()
