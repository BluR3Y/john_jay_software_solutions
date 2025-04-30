import types

# class ColumnManager:
#     assignable_properties = {
#         "alias": str,
#         "sheet": str,
#         "mutation": object
#     }

#     def __init__(self, name: str):
#         self.assigned_properties = {"name": name}

#     def __getitem__(self, key: str):
#         return self.assigned_properties.get(key)

#     def set_property(self, prop_name, prop_val):
#         if prop_name not in self.assignable_properties:
#             raise ValueError(f"Property '{prop_name}' is not assignable.")
        
#         expected_type = self.assignable_properties[prop_name]
#         if prop_name == "muation":
#             if not callable(prop_val):
#                 raise TypeError(f"Property '{prop_name}' must be a function or callable.")
#             elif not isinstance(prop_val, self.assignable_properties[prop_name]):
#                 raise TypeError(f"Property '{prop_name}' was assigned an invalid type. Expected {expected_type.__name__}.")
        
#         self.assigned_properties[prop_name] = prop_val
#         return self
    
#     def get_alias(self):
#         return self.assigned_properties.get("alias") or self.assigned_properties.get("name")

class ColumnManager:
    assignable_properties = {
        "name": str,
        "ref_alias": str,
        "ref_sheet": str,
        "mutation": str
    }

    def __init__(self, props: dict):
        for key, value in props.items():
            self[key] = value

    def __getitem__(self, key):
        try:
            value = super().__getattribute__(key)
        except AttributeError:
            value = None
        return value

    def __setitem__(self, key, value):
        if key not in self.assignable_properties:
            raise KeyError(f"Key '{key}' is not allowed.")
        
        expected_type = self.assignable_properties[key]
        if not isinstance(value, expected_type):
            raise TypeError(f"Property '{key}' was assigned an invalid type. Expected {expected_type.__name__}.")
        
        if key == "mutation":
            fn = eval(value)
            if not callable(fn):
                raise TypeError(f"Property '{key}' must be a function or callable.")
            super().__setattr__(key, fn)
            return

        super().__setattr__(key, value)

    def get_ref_name(self):
        return self["alias"] or self["name"]