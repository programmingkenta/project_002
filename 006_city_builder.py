print("=== City Builder ===")

city = []

num = int(input("How many buildings?"))

for i in range(num):
    name = input("Building name: ")
    city.append(name)

print()
print("Your city has", len(city), "buildings:")
for building in city:
    print("-", building)


