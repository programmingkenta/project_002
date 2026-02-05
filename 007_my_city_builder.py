
print("=== MY CITY BUILDER ===")
print()

# Now using a single list of dictionaries instead of parallel lists!
buildings = []

num = int(input("How many buildings to create? "))
print()

for i in range(1, num + 1):
    print("Building", i)
    name = input("  Name: ")
    height = int(input("  Height (meters): "))
    cost = int(input("  Cost ($): "))
    
    my_building = {"name": name, "height": height, "cost": cost}
    buildings.append(my_building)

    print()

print("=== YOUR CITY ===")
print()

for building in buildings:  # Much cleaner! No index needed
    if building["height"] > 100:
        category = "Skyscraper"
    else:
        category = "House"

    print(building["name"], "-", building["height"], "m -", category, "- $" + str(building["cost"]))

print()
print("Total buildings:", len(buildings))