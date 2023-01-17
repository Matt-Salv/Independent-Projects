ListA = ["string 1", "string 2", "string 3"]
ListB = ["Fruits", "Veggies"]
ListA.extend(ListB)
ListA.remove("Veggies")
ListA.pop(1)
ListA.clear
ListA = ["1", "2", "3", "4"]
for x in ListA:
    print(x)
i = 0
while i < len(ListA):
    print(ListA[i])
    i += 1

fruits = ["apple","banana", "cherry", "kiwi", "mango"]
newlist = [x for x in fruits if "a" in x]
print(newlist)
