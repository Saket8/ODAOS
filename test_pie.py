import plotext as plt
import sys

# Attempt to render a pie chart at a fixed size to avoid distortion
labels = ["Netherlands", "USA", "Other"]
counts = [105, 49, 7]

plt.clear_figure()
plt.theme('dark')
plt.clf()
plt.pie(counts, labels=labels)
plt.title("Pie Chart Test")
# Try a square plot size to counter terminal aspect ratio (usually 2:1)
plt.plotsize(60, 30) 
plt.show()
