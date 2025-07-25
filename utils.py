import json

with open("data/iphone_db.json", encoding="utf-8") as f:
    iphone_db = json.load(f)

def find_models_by_color(color):
    result = []
    for model, info in iphone_db.items():
        if color in info["colors"]:
            result.append(model)
    return result

def find_models_by_storage(storage):
    result = []
    for model, info in iphone_db.items():
        if storage in info["storage"]:
            result.append(model)
    return result

def find_exact_match(model=None, color=None, storage=None):
    results = []
    for m, info in iphone_db.items():
        if model and model.lower() not in m.lower():
            continue
        if color and color not in info["colors"]:
            continue
        if storage and storage not in info["storage"]:
            continue
        results.append(m)
    return results
