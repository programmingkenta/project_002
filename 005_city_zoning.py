print("=== City Zoning Tool ===")
height = int(input("Enter building height:"))

if height > 300:
    print("Zone: SUPER TOWER")
elif height > 150:
    print("Zone: Skyscraper")
elif height > 50:
    print("Zone: Commercial")
else:
    print("Zone: Residential")
            