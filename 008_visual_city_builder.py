import turtle

print("=== VISUAL CITY BUILDER ===")
print()

# Set up the turtle window
screen = turtle.Screen()
screen.title("My City Skyline")
screen.bgcolor("skyblue")

# Create our drawing turtle
pen = turtle.Turtle()
pen.speed(0)  # Fastest drawing speed
pen.hideturtle()

# Collect building data (same pattern as before!)
buildings = []

num = int(input("How many buildings to create? "))
print()

for i in range(1, num + 1):
    print(f"Building {i}")
    name = input("  Name: ")
    height = int(input("  Height (meters): "))

    my_building = {"name": name, "height": height}
    buildings.append(my_building)
    print()

print("Drawing your city...")
print()

# Starting position (bottom-left of first building)
start_x = -300
building_width = 80
gap = 20
ground_level = -200

def draw_building(x, height, name):
    """Draw a single building at position x with given height"""
    # Scale height for screen (1 meter = 1 pixel)
    scaled_height = height

    # TODO(human): Choose the building color based on height
    # - If height > 200: use "darkgray" (skyscraper)
    # - If height > 100: use "slategray" (tall building)
    # - Otherwise: use "brown" (house)
    # Set the color using: pen.fillcolor(your_color)

    if height > 200:
        pen.fillcolor("#555555")
    elif height > 100:
        pen.fillcolor("#778899")
    else:
        pen.fillcolor("#8B4513")    


    # Draw the building rectangle
    pen.penup()
    pen.goto(x, ground_level)
    pen.pendown()
    pen.begin_fill()

    # Draw rectangle: up, right, down, left
    pen.goto(x, ground_level + scaled_height)
    pen.goto(x + building_width, ground_level + scaled_height)
    pen.goto(x + building_width, ground_level)
    pen.goto(x, ground_level)

    pen.end_fill()

    # Draw windows (simple dots)
    pen.penup()
    for row in range(20, scaled_height - 10, 30):
        for col in range(15, building_width - 10, 25):
            pen.goto(x + col, ground_level + row)
            pen.dot(8, "yellow")

    # Write building name
    pen.goto(x + building_width // 2, ground_level - 20)
    pen.write(name, align="center", font=("Arial", 8, "normal"))

# Draw each building
current_x = start_x
for building in buildings:
    draw_building(current_x, building["height"], building["name"])
    current_x += building_width + gap

# Draw the ground
pen.penup()
pen.goto(-400, ground_level)
pen.pendown()
pen.pensize(3)
pen.pencolor("darkgreen")
pen.goto(400, ground_level)

# Keep window open
print("Close the turtle window to exit.")
screen.mainloop()
