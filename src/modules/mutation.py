from typing import Any, Union, Literal, TypedDict
import re


# --- Transformation Dispatcher ---

def apply_mutation(value: Any, transformations: list[dict[str, Any]]) -> Any:
    latest = value
    for step in transformations:
        for action, param in step.items():
            latest = apply_transformation(latest, action, param)
    return latest


def apply_transformation(
    value: Any,
    action: Literal["case", "convertion", "affix", "sub"],
    param: Any
) -> Any:
    match action:
        case "case":
            return apply_case(str(value), param["type"])
        case "convertion":
            return apply_convertion(value, param["type"])
        case "affix":
            return apply_affix(str(value), param['kind'], param['target'])
        case "sub":
            return apply_substitution(str(value), param["pattern"], param["replace"])
        case _:
            raise ValueError(f"Invalid transformation action: {action}")


# --- Transform Function Implementations ---

def apply_case(value: str, case: Literal["upper", "lower", "capital"]) -> str:
    match case:
        case "upper":
            return value.upper()
        case "lower":
            return value.lower()
        case "capital":
            return value.capitalize()
        case _:
            raise ValueError(f"Invalid case: {case}")


def apply_convertion(value: Any, type_: Literal["str", "int", "float", "bool"]) -> Union[str, int, float, bool]:
    match type_:
        case "str":
            return str(value)
        case "int":
            return int(value)
        case "float":
            return float(value)
        case "bool":
            return bool(value)
        case _:
            raise ValueError(f"Invalid convertion type: {type_}")


def apply_affix(value: str, kind: Literal["prefix", "postfix"], target: str) -> str:
    if kind == "prefix":
        return target + value
    elif kind == "postfix":
        return value + target
    else:
        raise ValueError(f"Invalid affix kind: {kind}")


def apply_substitution(value: str, pattern: str, replace: str) -> str:
    return re.sub(pattern, replace, value)
