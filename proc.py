import json

with open("temp.json", 'r') as f:
    content = json.load(f)["seen_refs"]
    refs = [ref.split('/')[0] for ref in content.keys()]
    duplicated = list(ref for ref in refs if refs.count(ref) > 1)
    print({key: content[key] for key in content.keys() if key.split("/")[0] in duplicated})
