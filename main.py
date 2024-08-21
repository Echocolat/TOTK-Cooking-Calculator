from totk_cook_logic import TotKCookSim, InvalidMaterialException, EmptyMaterialListException

meal = TotKCookSim()
output = meal.cook(["Apple"])
print(output)