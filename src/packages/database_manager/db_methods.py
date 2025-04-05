import re
from typing import Union, List, Tuple, Any, Dict

# --- Entry Point ---
def parse_sql_condition(condition_str: str) -> dict:
    condition_str = condition_str.strip()
    if not condition_str:
        return {}

    # Unwrap outer parentheses
    if condition_str.startswith('(') and condition_str.endswith(')'):
        return parse_sql_condition(condition_str[1:-1].strip())

    operator = find_top_level_operator(condition_str)
    if operator:
        parts = split_conditions(condition_str, operator)
        parsed_parts = [parse_sql_condition(part) for part in parts]
        return {operator: parsed_parts}
    
    return parse_simple_condition(condition_str)

# --- Logical Operator Parsing ---
def find_top_level_operator(condition_str: str) -> Union[str, None]:
    operators = ['AND', 'OR']
    level = 0
    pattern = re.compile(r'\b(AND|OR)\b', re.IGNORECASE)

    for match in pattern.finditer(condition_str):
        op = match.group(1).upper()
        idx = match.start()

        # Count parentheses up to operator
        for i in range(idx):
            if condition_str[i] == '(':
                level += 1
            elif condition_str[i] == ')':
                level -= 1
        
        if level == 0:
            return op
    return None

# --- Condition Splitter ---
def split_conditions(condition_str: str, operator: str) -> List[str]:
    parts = []
    current = []
    level = 0
    i = 0
    op_len = len(operator)

    while i < len(condition_str):
        if condition_str[i] == '(':
            level += 1
        elif condition_str[i] == ')':
            level -= 1
        elif level == 0 and condition_str[i:i+op_len].upper() == operator:
            before = condition_str[i-1] if i > 0 else ' '
            after = condition_str[i+op_len] if i + op_len < len(condition_str) else ' '
            if not before.isalnum() and not after.isalnum():
                parts.append(''.join(current).strip())
                current = []
                i += op_len
                continue
        current.append(condition_str[i])
        i += 1

    parts.append(''.join(current).strip())
    return parts

# --- Parse Simple Condition ---
def parse_simple_condition(condition_str: str) -> Dict[str, Any]:
    pattern = r'^(\w+)\s+(IS\s+NOT|IS|NOT\s+LIKE|NOT\s+IN|IN|LIKE|>=|<=|!=|<>|=|>|<)\s+(.*)$'
    match = re.match(pattern, condition_str, re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not parse condition: {condition_str}")

    field, operator, value_str = match.groups()
    return {
        field: {
            "operator": operator.upper(),
            "value": parse_value(value_str.strip(), operator.upper())
        }
    }

# --- Value Parser ---
def parse_value(value_str: str, operator: str) -> Any:
    if operator in ('IS', 'IS NOT') and value_str.upper() == 'NULL':
        return None

    if operator in ('IN', 'NOT IN'):
        if not value_str.startswith('(') or not value_str.endswith(')'):
            raise ValueError("IN clause requires parentheses")

        content = value_str[1:-1]
        return parse_list(content)

    if (value_str.startswith("'") and value_str.endswith("'")) or \
       (value_str.startswith('"') and value_str.endswith('"')):
        return value_str[1:-1]

    try:
        return int(value_str)
    except ValueError:
        try:
            return float(value_str)
        except ValueError:
            return value_str

# --- Helper for IN clause parsing ---
def parse_list(content: str) -> List[Any]:
    import shlex
    lexer = shlex.shlex(content, posix=True)
    lexer.whitespace_split = True
    lexer.whitespace = ','
    tokens = list(lexer)

    parsed = []
    for token in tokens:
        token = token.strip()
        if token.startswith(("'", '"')) and token.endswith(("'", '"')):
            parsed.append(token[1:-1])
        else:
            try:
                parsed.append(int(token))
            except ValueError:
                try:
                    parsed.append(float(token))
                except ValueError:
                    parsed.append(token)
    return parsed

# --- Reconstruction ---
def destruct_query_conditions(conditions: dict) -> Tuple[str, List[Any]]:
    def _build(cond: dict, top_level: bool = False) -> Tuple[str, List[Any]]:
        if 'AND' in cond or 'OR' in cond:
            op = 'AND' if 'AND' in cond else 'OR'
            parts, values = [], []
            for sub in cond[op]:
                sql, val = _build(sub)
                parts.append(sql)
                values.extend(val)
            joined = f' {op} '.join(parts)
            return (joined if top_level else f'({joined})'), values

        # Simple condition
        field = next(iter(cond))
        operator = cond[field]['operator']
        value = cond[field]['value']

        if operator in ('IS', 'IS NOT') and value is None:
            return f"{field} {operator} NULL", []

        if operator in ('IN', 'NOT IN') and isinstance(value, list):
            placeholders = ', '.join(['?'] * len(value))
            return f"{field} {operator} ({placeholders})", value

        return f"{field} {operator} ?", [value]

    return _build(conditions, top_level=True)
