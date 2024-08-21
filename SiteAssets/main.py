from totk_cook_logic import TotKCookSim, InvalidMaterialException, EmptyMaterialListException
from pyscript import when, display
from pyscript.web import page 

@when("click", page["#cook"])
def my_button_click_handler(event):
    materials = []
    for i in range(5):
        val = page[f"#item{i+1}"].value[0]
        if val != '':
            materials.append(val)

    sim = TotKCookSim()
    output = ""
    try:
        result = sim.cook(materials)
        for k, v in result.items():
            output += f'{k}: {v}\n'
        display(output, target="outputText", append=False)
    except EmptyMaterialListException:
        display('Material list is empty.', target="outputText", append=False)
    except InvalidMaterialException:
        display('Invalid material detected.', target="outputText", append=False)
    except Exception:
        display('Something went wrong.', target="outputText", append=False)