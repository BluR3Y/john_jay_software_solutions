import re

def parse_sql_condition(condition_str):
    condition_str = condition_str.strip()
    if not condition_str:
        return {}

    # Check for enclosing parentheses
    if condition_str.startswith('(') and condition_str.endswith(')'):
        return parse_sql_condition(condition_str[1:-1].strip())

    # Find top-level logical operator
    operator = find_top_level_operator(condition_str)
    if operator:
        parts = split_conditions(condition_str, operator)
        parsed_parts = [parse_sql_condition(part) for part in parts]
        return {operator: parsed_parts}
    else:
        return parse_simple_condition(condition_str)

def find_top_level_operator(condition_str):
    operators = ['AND', 'OR']
    parenthesis_level = 0
    max_len = len(condition_str)
    i = 0

    while i < max_len:
        if condition_str[i] == '(':
            parenthesis_level += 1
            i += 1
        elif condition_str[i] == ')':
            parenthesis_level -= 1
            i += 1
        else:
            for op in operators:
                op_len = len(op)
                if i + op_len > max_len:
                    continue
                # Check for operator match (case-insensitive)
                if condition_str[i:i+op_len].upper() == op:
                    # Check word boundaries
                    prev_char = condition_str[i-1] if i > 0 else ' '
                    next_char = condition_str[i+op_len] if i+op_len < max_len else ' '
                    if not prev_char.isalnum() and not next_char.isalnum() and parenthesis_level == 0:
                        return op
            i += 1
    return None
    # Example: parse_sql_condition("RF_Account IS NOT NULL AND (Grant_ID >= 60000 AND Grant_ID <= 70000) AND (Primary_PI LIKE '%Jeff%' OR Primary_Dept IN ('Sociology', 'Criminal Justice', 'Psychology')) AND Status = 'Funded'")
# {   
#     'AND': [
#         {'RF_Account': {'operator': 'IS NOT', 'value': None}},
#         {'AND': [
#             {'Grant_ID': {'operator': '>=', 'value': 60000}},
#             {'Grant_ID': {'operator': '<=', 'value': 70000}}
#         ]},
#         {'OR': [
#             {'Primary_PI': {'operator': 'LIKE', 'value': '%Jeff%'}},
#             {'Primary_Dept': {'operator': 'IN', 'value': ['Sociology', 'Criminal Justice', 'Psychology']}}
#         ]},
#         {'Status': {'operator': '=', 'value': 'Funded'}}
#     ]
# }

def split_conditions(condition_str, operator):
    parts = []
    current_part = []
    parenthesis_level = 0
    op_len = len(operator)
    i = 0
    max_len = len(condition_str)
    
    while i < max_len:
        if condition_str[i] == '(':
            parenthesis_level += 1
            current_part.append(condition_str[i])
            i += 1
        elif condition_str[i] == ')':
            parenthesis_level -= 1
            current_part.append(condition_str[i])
            i += 1
        else:
            # Check for operator match
            if (i + op_len <= max_len and
                condition_str[i:i+op_len].upper() == operator and
                (i == 0 or not condition_str[i-1].isalnum()) and
                (i+op_len == max_len or not condition_str[i+op_len].isalnum()) and
                parenthesis_level == 0):
                
                parts.append(''.join(current_part).strip())
                current_part = []
                i += op_len
                # Skip whitespace after operator
                while i < max_len and condition_str[i].isspace():
                    i += 1
            else:
                current_part.append(condition_str[i])
                i += 1
    parts.append(''.join(current_part).strip())
    return parts

def parse_simple_condition(condition_str):
    # Match field, operator, value
    pattern = r'^(\w+)\s+(IS\s+NOT|IS|IN|LIKE|>=|<=|!=|<>|=|>|<|NOT\s+LIKE)\s+(.*)$'
    match = re.match(pattern, condition_str, re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not parse condition: {condition_str}")
    
    field = match.group(1)
    operator = match.group(2).upper()
    value_str = match.group(3).strip()
    value = parse_value(value_str, operator)
    
    return {field: {"operator": operator, "value": value}}

def parse_value(value_str, operator):
    # Handle NULL values explicitly
    if value_str.upper() == 'NULL':
        return None  # Convert 'NULL' string to Python None
    
    # Handle IS and IS NOT operators (NULL should be stored as None)
    if operator in ('IS', 'IS NOT'):
        return None if value_str.upper() == 'NULL' else value_str.upper()
    
    # Handle IN clause
    if operator == 'IN':
        if not (value_str.startswith('(') and value_str.endswith(')')):
            raise ValueError("IN clause requires parentheses")
        
        values = value_str[1:-1].strip()
        parsed_values = []
        current = []
        in_quote = False
        quote_char = None
        
        for char in values:
            if char in ('"', "'") and not in_quote:
                in_quote = True
                quote_char = char
            elif char == quote_char and in_quote:
                in_quote = False
                quote_char = None
            elif char == ',' and not in_quote:
                parsed_values.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        if current:
            parsed_values.append(''.join(current).strip())
        
        # Process parsed values
        cleaned_values = []
        for val in parsed_values:
            if val.startswith(("'", '"')) and val.endswith(("'", '"')):
                cleaned_values.append(val[1:-1])  # Remove quotes
            else:
                # Try numeric conversion
                try:
                    cleaned_values.append(int(val))
                except ValueError:
                    try:
                        cleaned_values.append(float(val))
                    except ValueError:
                        cleaned_values.append(val)
        return cleaned_values
    
    # Handle quoted strings
    if (value_str.startswith("'") and value_str.endswith("'")) or \
       (value_str.startswith('"') and value_str.endswith('"')):
        return value_str[1:-1]
    
    # Numeric conversion
    try:
        return int(value_str)
    except ValueError:
        try:
            return float(value_str)
        except ValueError:
            return value_str  # Return as string if not numeric        

  
def destruct_query_conditions(conditions: dict) -> tuple[str, list]:
    def _build_condition(cond, is_top_level=False):
        # Check for logical operators (AND/OR)
        if 'AND' in cond:
            operator = 'AND'
            clauses = cond['AND']
        elif 'OR' in cond:
            operator = 'OR'
            clauses = cond['OR']
        else:
            # Handle simple condition
            field = list(cond.keys())[0]
            op_info = cond[field]
            operator = op_info['operator']
            value = op_info['value']
            
            # Handle NULL cases (Access requires "IS NULL" or "IS NOT NULL" without parameters)
            if operator.upper() in ('IS', 'IS NOT'):
                if value is None:  
                    return f"{field} {operator} NULL", []  # No parameter placeholder for NULL

            # Handle IN clauses
            if operator.upper() in ('IN', 'NOT IN'):
                if isinstance(value, list) and value:
                    placeholders = ', '.join(['?'] * len(value))
                    val_str = f"({placeholders})"
                    values = value
                else:
                    raise ValueError("IN clause requires a non-empty list of values")
            
            else:
                val_str = '?'
                values = [value]
            
            return f"{field} {operator} {val_str}", values

        # Process nested conditions
        parts = []
        all_values = []
        for clause in clauses:
            clause_sql, clause_values = _build_condition(clause)
            parts.append(clause_sql)
            all_values.extend(clause_values)

        combined = f' {operator} '.join(parts)
        
        # Add parentheses for nested logical operations unless it's the top level
        if not is_top_level:
            combined = f'({combined})'
        
        return combined, all_values

    query, values = _build_condition(conditions, is_top_level=True)
    return query, values

