from packages.workbook_manager import WorkbookManager
from modules.mutation import apply_mutation

def test_env():
    value = apply_mutation("Hello-5153", [
        {"sub": {"pattern": "^Hello-", "replace": "" }},
        {"convertion": { "type": "float" }},
        {"affix": { "kind": "postfix", "target": "-Hello" }},
        {"case": { "type": "upper" }}
    ])
    print(value)