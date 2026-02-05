import turtle

print("=== ISOMETRIC CITY ===")
print("Drawing your isometric city...")
print()

# Set up the turtle window
screen = turtle.Screen()
screen.title("Isometric City")
screen.bgcolor("#87CEEB")  # Sky blue

pen = turtle.Turtle()
pen.speed(0)
pen.hideturtle()

# Preset buildings (using our familiar dictionary pattern!)
buildings = [
    {"name": "House",     "row": 0, "col": 0, "height": 40},
    {"name": "Shop",      "row": 0, "col": 1, "height": 30},
    {"name": "Office",    "row": 0, "col": 2, "height": 80},
    {"name": "Park",      "row": 1, "col": 0, "height": 10},
    {"name": "Tower",     "row": 1, "col": 1, "height": 120},
    {"name": "Apartment", "row": 1, "col": 2, "height": 60},
    {"name": "School",    "row": 2, "col": 0, "height": 35},
    {"name": "Hospital",  "row": 2, "col": 1, "height": 50},
    {"name": "Skyscraper","row": 2, "col": 2, "height": 150},
]

# Isometric settings
tile_width = 80    # Width of one ground tile
tile_height = 40   # Height of one ground tile (half of width for isometric!)
origin_x = 0       # Center of the screen
origin_y = 100      # Shift everything up a bit

def grid_to_screen(row, col):
    """Convert grid position (row, col) to screen position (x, y)

    This is the KEY isometric formula!
    It turns a flat grid into a diamond-shaped layout:

    Grid:          Screen (isometric):
    [0,0][0,1]         /\  /\
    [1,0][1,1]        /  \/  \
                      \  /\  /
                       \/  \/
    """
    x = (col - row) * (tile_width // 2) + origin_x
    y = -(col + row) * (tile_height // 2) + origin_y
    return x, y

def draw_face(points, color):
    """Draw a filled polygon given a list of (x, y) points"""
    pen.fillcolor(color)
    pen.penup()
    pen.goto(points[0])
    pen.pendown()
    pen.begin_fill()
    for point in points[1:]:
        pen.goto(point)
    pen.goto(points[0])
    pen.end_fill()

def draw_isometric_building(row, col, height):
    """Draw a 3D isometric building at grid position (row, col)"""
    # Get the screen position for this grid cell
    x, y = grid_to_screen(row, col)

    # Half dimensions for drawing
    hw = tile_width // 2   # half width = 40
    hh = tile_height // 2  # half height = 20

    # The 4 corners of the ground tile (diamond shape):
    #        top
    #       /    \
    #     left   right
    #       \    /
    #       bottom
    top =    (x,      y + hh)
    right =  (x + hw, y)
    bottom = (x,      y - hh)
    left =   (x - hw, y)

    # The same 4 corners but raised by building height:
    top_up =    (x,      y + hh + height)
    right_up =  (x + hw, y + height)
    bottom_up = (x,      y - hh + height)
    left_up =   (x - hw, y + height)

    # TODO(human): Choose the 3 face colors to create a 3D shading effect
    # The LEFT face should be medium brightness
    # The RIGHT face should be the darkest (it's in shadow)
    # The TOP face should be the lightest (sun hits it directly)
    #
    # Set these three variables:
    #   left_color  = a medium color
    #   right_color = a dark color
    #   top_color   = a light color
    #
    # Try one of these color schemes:
    #   Blues:  "#4488BB", "#336699", "#66AADD"
    #   Grays:  "#888888", "#666666", "#AAAAAA"
    #   Reds:   "#CC6666", "#993333", "#EE8888"
    # Or pick your own! Format: "#RRGGBB"
    left_color = "#888888"
    right_color = "#888888"
    top_color = "#888888"

    # Draw LEFT face (visible from the left side)
    draw_face([left, bottom, bottom_up, left_up], left_color)

    # Draw RIGHT face (visible from the right side)
    draw_face([right, bottom, bottom_up, right_up], right_color)

    # Draw TOP face (the roof, seen from above)
    draw_face([top_up, right_up, bottom_up, left_up], top_color)

# Draw buildings back-to-front (so closer buildings overlap farther ones)
# Sort by row + col so far buildings are drawn first
sorted_buildings = sorted(buildings, key=lambda b: b["row"] + b["col"])

for building in sorted_buildings:
    draw_isometric_building(
        building["row"],
        building["col"],
        building["height"]
    )

# Draw ground grid
pen.pensize(1)
pen.pencolor("#336633")
for row in range(3):
    for col in range(3):
        x, y = grid_to_screen(row, col)
        hw = tile_width // 2
        hh = tile_height // 2
        pen.penup()
        pen.goto(x, y + hh)
        pen.pendown()
        pen.goto(x + hw, y)
        pen.goto(x, y - hh)
        pen.goto(x - hw, y)
        pen.goto(x, y + hh)

print("Close the turtle window to exit.")
screen.mainloop()
