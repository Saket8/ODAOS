import math

def render_ascii_pie(labels, values, radius=10):
    """
    Renders a circular ASCII pie chart.
    """
    if not values:
        return "No data"

    total = sum(values)
    # Calculate angles (cumulative)
    angles = []
    current_angle = 0
    for val in values:
        fraction = val / total
        start = current_angle
        end = current_angle + (fraction * 2 * math.pi)
        angles.append((start, end))
        current_angle = end

    # Symbols for different segments
    symbols = ["#", "@", "%", "&", "X", "O", "*", "+"]
    
    # Grid for rendering
    # Terminal characters are roughly twice as tall as they are wide,
    # so we double the X radius to keep the circle 'round'
    width = radius * 4
    height = radius * 2
    grid = [[" " for _ in range(width + 1)] for _ in range(height + 1)]

    for y in range(-radius, radius + 1):
        for x in range(-radius * 2, radius * 2 + 1):
            # Convert terminal coords to math coords (normalized)
            # Adjust x for aspect ratio
            mx = x / 2.0
            my = -y # Plane inversion
            
            dist = math.sqrt(mx**2 + my**2)
            
            if dist <= radius:
                # Calculate angle of this point
                angle = math.atan2(my, mx)
                if angle < 0:
                    angle += 2 * math.pi
                
                # Find which segment this angle belongs to
                char = "."
                for i, (start, end) in enumerate(angles):
                    if start <= angle < end:
                        char = symbols[i % len(symbols)]
                        break
                
                grid[y + radius][x + radius * 2] = char

    # Convert grid to string
    output = []
    for row in grid:
        output.append("".join(row))
    
    # Legend
    legend = ["", "Legend:"]
    for i, (label, val) in enumerate(zip(labels, values)):
        char = symbols[i % len(symbols)]
        pct = (val / total * 100)
        legend.append(f"  {char} {label}: {val} ({pct:.1f}%)")
        
    return "\n".join(output + legend)

if __name__ == "__main__":
    labels = ["Netherlands", "USA", "Other"]
    values = [105, 49, 7]
    print(render_ascii_pie(labels, values))
