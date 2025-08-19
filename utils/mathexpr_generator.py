"""
Mathematical Expression Generator

This module provides functionality for generating, manipulating, and evaluating mathematical expressions, including:
1. Expression tree nodes (Variable, Constant, Add, Subtract, Multiply, Divide, Power, Comparison)
2. Formula configuration and serialization/deserialization
3. Random expression generation with configurable complexity
4. Z3 integration for constraint solving
5. LaTeX output for mathematical notation
"""

import random
import z3
import math
import re

class ExprNode:
    def to_z3(self, vars): raise NotImplementedError
    def evaluate(self, values): raise NotImplementedError
    def to_latex(self, var_names): raise NotImplementedError
    def serialize(self): raise NotImplementedError

class Variable(ExprNode):
    def __init__(self, index): self.index = index
    def to_z3(self, vars):  return vars[self.index], []  # No additional constraints
    def evaluate(self, values): return values[self.index]
    def to_latex(self, var_names): return var_names[self.index]
    def serialize(self): return f"(Var {self.index})"

class Constant(ExprNode):
    def __init__(self, value): self.value = value
    def to_z3(self, _): return self.value, []  # No additional constraints
    def evaluate(self, _): return self.value
    def to_latex(self, _): return f"{self.value}"
    def serialize(self): return f"(Const {self.value})"

class Add(ExprNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def to_z3(self, vars): 
        left_expr, left_constraint = self.left.to_z3(vars)
        right_expr, right_constraint = self.right.to_z3(vars)
        return left_expr + right_expr, left_constraint + right_constraint
    def evaluate(self, values): return self.left.evaluate(values) + self.right.evaluate(values)
    def to_latex(self, var_names): return f"({self.left.to_latex(var_names)} + {self.right.to_latex(var_names)})"
    def serialize(self): return f"(Add {self.left.serialize()} {self.right.serialize()})"

class Subtract(ExprNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def to_z3(self, vars): 
        left_expr, left_constraint = self.left.to_z3(vars)
        right_expr, right_constraint = self.right.to_z3(vars)
        return left_expr - right_expr, left_constraint + right_constraint
    def evaluate(self, values): return self.left.evaluate(values) - self.right.evaluate(values)
    def to_latex(self, var_names): return f"({self.left.to_latex(var_names)} - {self.right.to_latex(var_names)})"
    def serialize(self): return f"(Sub {self.left.serialize()} {self.right.serialize()})"

class Multiply(ExprNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def to_z3(self, vars): 
        left_expr, left_constraint = self.left.to_z3(vars)
        right_expr, right_constraint = self.right.to_z3(vars)
        return left_expr * right_expr, left_constraint + right_constraint
    
    def evaluate(self, values): return self.left.evaluate(values) * self.right.evaluate(values)
    def to_latex(self, var_names): return f"{self.left.to_latex(var_names)} \\cdot {self.right.to_latex(var_names)}"
    def serialize(self): return f"(Mul {self.left.serialize()} {self.right.serialize()})"

class Divide(ExprNode):
    def __init__(self, num, den):
        self.num = num
        self.den = den

    def to_z3(self, vars):
        num_expr, num_constraint = self.num.to_z3(vars)
        den_expr, den_constraint = self.den.to_z3(vars)

        # Convert to Z3 Real if not already a Z3 expression
        if not isinstance(num_expr, z3.ExprRef):
            num_expr = z3.RealVal(num_expr)
        if not isinstance(den_expr, z3.ExprRef):
            den_expr = z3.RealVal(den_expr)

        # Only apply ToReal if the expression is an integer
        if z3.is_int(num_expr):
            num_expr = z3.ToReal(num_expr)
        if z3.is_int(den_expr):
            den_expr = z3.ToReal(den_expr)

        return (
            num_expr / den_expr,
            num_constraint + den_constraint + [den_expr != 0]
        )

    def evaluate(self, values): 
        den_val = self.den.evaluate(values)
        if den_val == 0: 
            raise ValueError("Division by zero")
        return self.num.evaluate(values) / den_val  # Python uses floating point division by default

    def to_latex(self, var_names): 
        return f"\\frac{{{self.num.to_latex(var_names)}}}{{{self.den.to_latex(var_names)}}}"

    def serialize(self): 
        return f"(Div {self.num.serialize()} {self.den.serialize()})"

class Power(ExprNode):
    def __init__(self, var, exponent):
        self.var = var  # Must be a Variable
        self.exponent = exponent  # Must be a positive integer

    def to_z3(self, vars):
        var_expr, var_constraints = self.var.to_z3(vars)
        if not isinstance(var_expr, z3.ExprRef):
            var_expr = z3.RealVal(var_expr)
        # Ensure exponent is a positive integer
        if not isinstance(self.exponent, int) or self.exponent < 1:
            raise ValueError(f"Exponent must be a positive integer, got {self.exponent}")
        return var_expr ** self.exponent, var_constraints
    def evaluate(self, values):
        return self.var.evaluate(values) ** self.exponent

    def to_latex(self, var_names):
        var_name = self.var.to_latex(var_names)
        return f"{var_name}^{{{self.exponent}}}"

    def serialize(self):
        return f"(Power {self.var.serialize()} {self.exponent})"
    

class Comparison(ExprNode):
    OPS = {
        '<=': (lambda a,b: a <= b, r'\leq'),
        '>=': (lambda a,b: a >= b, r'\geq'),
        '==': (lambda a,b: a == b, '='),
        '<':  (lambda a,b: a < b, '<'),
        '>':  (lambda a,b: a > b, '>')
    }
    
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
    
    def to_z3(self, vars): 
        left_expr, left_constraint = self.left.to_z3(vars)
        right_expr, right_constraint = self.right.to_z3(vars)
        op_func, _ = Comparison.OPS[self.op]
        return (
            op_func(left_expr, right_expr),
            left_constraint + right_constraint
        )
    
    def evaluate(self, values): 
        return Comparison.OPS[self.op][0](self.left.evaluate(values), self.right.evaluate(values))
    
    def to_latex(self, var_names): 
        return f"{self.left.to_latex(var_names)} {Comparison.OPS[self.op][1]} {self.right.to_latex(var_names)}"
    
    def serialize(self): 
        return f"(Cmp {self.op} {self.left.serialize()} {self.right.serialize()})"

def to_value(s):
    # First check if it can be converted to integer (no decimal point or scientific notation)
    if '.' not in s and 'e' not in s.lower():
        try:
            return int(s)
        except ValueError:
            pass  # If it can't be converted to integer, continue trying float
    # Try to convert to float
    try:
        return float(s)
    except ValueError:
        raise ValueError(f"Input string '{s}' is not a valid numeric format")
    
class FormulaConfig:
    def __init__(self, root, vars_num):
        self.root = root
        self.vars_num = vars_num
    
    def get_z3_expr(self, z3_vars):
        if len(z3_vars) != self.vars_num:
            raise ValueError(f"Expected {self.vars_num} variables, got {len(z3_vars)}")
        return self.root.to_z3(z3_vars)
    
    def get_value(self, values):
        if len(values) != self.vars_num:
            raise ValueError(f"Expected {self.vars_num} variables, got {len(values)}")
        try: 
            return self.root.evaluate(values)
        except Exception as e: 
            return f"Error: {str(e)}"
    
    def get_latex(self, vars):
        if len(vars) != self.vars_num:
            raise ValueError(f"Expected {self.vars_num} variables, got {len(vars)}")
        return self.root.to_latex(vars)
    
    def serialize(self): 
        return self.root.serialize()
    
    @classmethod
    def deserialize(cls, s, vars_num):
        def tokenize(s):
            return re.findall(r'[()]|[^()\s]+', s)

        def parse(tokens):
            stack = []
            current = []
            for token in tokens:
                if token == '(':
                    stack.append(current)
                    current = []
                elif token == ')':
                    if not stack:
                        raise ValueError("Unbalanced parentheses")
                    parent = stack.pop()
                    parent.append(current)
                    current = parent
                else:
                    current.append(token)
            if len(current) != 1:
                raise ValueError(f"Invalid structure: {current}")
            return current[0]

        def build_node(parts):
            if not isinstance(parts, list):
                if parts.startswith('Var'):
                    idx = int(parts[3:])
                    if idx >= vars_num:
                        raise ValueError(f"Variable index {idx} exceeds vars_num {vars_num}")
                    return Variable(idx)
                if parts.startswith('Const'):
                    return Constant(to_value(parts[5:]))
                try:
                    return Constant(to_value(parts))
                except ValueError:
                    raise ValueError(f"Unexpected token: {parts}")
            
            node_type = parts[0]
            
            if node_type == 'Cmp':
                if len(parts) != 4:
                    raise ValueError(f"Cmp requires 3 parts, got {len(parts)}")
                return Comparison(
                    left=build_node(parts[2]),
                    op=parts[1],
                    right=build_node(parts[3])
                )
            elif node_type == 'Const':
                if len(parts) != 2:
                    raise ValueError(f"Const requires 1 argument, got {len(parts)-1}")
                return Constant(to_value(parts[1]))
            elif node_type == 'Var':
                if len(parts) != 2:
                    raise ValueError(f"Var requires 1 argument, got {len(parts)-1}")
                idx = int(parts[1])
                if idx >= vars_num:
                    raise ValueError(f"Variable index {idx} exceeds vars_num {vars_num}")
                return Variable(idx)
            elif node_type in {'Add', 'Sub', 'Mul', 'Div'}:
                expected_args = 2
                if len(parts)-1 != expected_args:
                    raise ValueError(f"{node_type} requires {expected_args} arguments, got {len(parts)-1}")
                children = [build_node(child) for child in parts[1:]] 
                cls_map = {
                    'Add': Add,
                    'Sub': Subtract,
                    'Mul': Multiply,
                    'Div': Divide
                }
                return cls_map[node_type](*children)
            elif node_type == 'Power':
                if len(parts) != 3:
                    raise ValueError(f"Power requires 2 arguments (base, exponent), got {len(parts)-1}")
                var = build_node(parts[1])
                if not isinstance(var, Variable):
                    raise ValueError(f"Power base must be a Variable, got {type(var)}")
                try:
                    exponent = int(parts[2])
                    if exponent < 1:
                        raise ValueError(f"Exponent must be positive, got {exponent}")
                except ValueError:
                    raise ValueError(f"Invalid exponent: {parts[2]}")
                return Power(var, exponent)
            else:
                raise ValueError(f"Unsupported node type: {node_type}")

        try:
            # print("s: ", s)
            tokens = tokenize(s)
            # print("tokens: ", tokens)
            parsed = parse(tokens)
            # print("parsed: ", parsed)
            root = build_node(parsed)
            return cls(root, vars_num)
        except Exception as e:
            raise ValueError(f"Deserialization failed: {str(e)}\nInput: {s}")

def generate_expr(vars_num, depth=0, max_depth=5, allow_const=True, 
                 force_var=False, parent_op=None, allow_power=True, max_const=10):
    """
    Generate expression tree.

    Args:
        vars_num (int): Number of variables, determines the variable index range (0 to vars_num-1)
        depth (int): Current recursion depth, used to control expression complexity, default 0
        max_depth (int): Maximum recursion depth, controls maximum expression complexity, default 5
        allow_const (bool): Whether to allow generating constant terms, default True
        force_var (bool): Whether to force generating variables (automatically effective when allow_const is False), default False
        parent_op (str): Parent node operation type, used for special handling of certain operations, default None
        allow_power (bool): Whether to allow generating power operations (x² or x³), default True
        max_const (int): Maximum value for generated constants, default 10

    Returns:
        Expression: Generated expression tree object (can be Variable, Constant, Add, Subtract, Multiply or Power)
        
    Notes:
        1. When depth >= max_depth, will force generating leaf nodes (variables or constants)
        2. Multiplication operations receive special handling to ensure no two constants are multiplied
        3. Power operations only allow x² or x³ forms
        4. Addition/subtraction prevents generating two constants being added/subtracted
    """
    if depth >= max_depth:
        if force_var or not allow_const:
            return Variable(random.randint(0, vars_num - 1))
        else:
            return random.choice([
                Variable(random.randint(0, vars_num - 1)),
                Constant(random.randint(1, max_const))
            ])
    
    # Adjust operation type probability distribution
    op_weights = {
        'Add': 4,
        'Subtract': 3,
        'Multiply': 2,
        'Power': 1 if allow_power else 0  # Determined by parameter whether to allow power operations
    }
    op_types = [op for op, w in op_weights.items() if w > 0]
    weights = [w for op, w in op_weights.items() if w > 0]
    
    op_type = random.choices(op_types, weights=weights, k=1)[0]

    if op_type == 'Power' and allow_power:
        # Power operation base must be a single variable
        var = Variable(random.randint(0, vars_num - 1))
        exponent = random.choice([2, 3])  # Only allow x² or x³
        return Power(var, exponent)

    elif op_type == 'Multiply':
        # Generate left operand (forced to be constant or simple variable)
        left = generate_expr(
            vars_num, depth+1, max_depth, 
            allow_const=True, 
            force_var=False,
            parent_op='Multiply',
            allow_power=allow_power
        )
        
        # Generate right operand (forced to be another type)
        if isinstance(left, Constant):
            right = generate_expr(
                vars_num, depth+1, max_depth,
                allow_const=False,
                force_var=True,
                parent_op='Multiply',
                allow_power=allow_power
            )
        else:
            right = Constant(random.randint(2, max_const))
        
        return Multiply(left, right)

    else:  # Add/Subtract
        left = generate_expr(
            vars_num, depth+1, max_depth, 
            allow_const, 
            force_var=False,
            parent_op=op_type,
            allow_power=allow_power
        )
        right = generate_expr(
            vars_num, depth+1, max_depth, 
            allow_const,
            force_var=False,
            parent_op=op_type,
            allow_power=allow_power
        )
        
        # Prevent both sides from being constants
        if isinstance(left, Constant) and isinstance(right, Constant):
            if random.choice([True, False]):
                left = Variable(random.randint(0, vars_num - 1))
            else:
                right = Variable(random.randint(0, vars_num - 1))
        
        return Add(left, right) if op_type == 'Add' else Subtract(left, right)

def generate_formula(vars_num, is_cond=False, allow_power=True, max_depth=5):
    """
    Generate a single mathematical formula expression.
    
    Args:
        vars_num (int): Number of variables, determines the variable index range (0 to vars_num-1)
        is_cond (bool): Whether to generate comparison condition expressions (like x > 0), default False
        allow_power (bool): Whether to allow generating power operations (x² or x³), default True
        max_depth (int): Maximum depth of expression tree, controls expression complexity, default 5
        
    Returns:
        str: Serialized formula configuration string
        
    Notes:
        1. When is_cond is True, generates condition expressions compared with 0
        2. Comparison operators are randomly chosen from ['<=', '>=', '==', '<', '>']
    """
    expr = generate_expr(vars_num, max_depth=max_depth, allow_power=allow_power)
    if is_cond:
        op = random.choice(['<=', '>=', '==', '<', '>'])
        comparison = Comparison(expr, op, Constant(0))
        return FormulaConfig(comparison, vars_num).serialize()
    else:
        return FormulaConfig(expr, vars_num).serialize()

def generate_formulas(formula_num, vars_num, is_cond=False, allow_power=True, max_depth=5):
    """
    Generate a specified number of valid formulas.
    
    Args:
        formula_num (int): Number of formulas to generate
        vars_num (int): Number of variables
        is_cond (bool): Whether to generate comparison expressions (like x > 0), default False
        allow_power (bool): Whether to allow using power operations (x², x³ etc.), default True
        max_depth (int): Maximum depth of expression tree, controls expression complexity, default 5
        
    Returns:
        list[str]: List containing all valid formulas, each element is a serialized formula configuration string
        
    Raises:
        ValueError: Raised when unable to generate any valid formulas
        
    Notes:
        1. Will attempt multiple times until generating enough valid formulas or reaching maximum attempts
        2. Each generated formula undergoes validity verification
        3. Ensures no duplicate formulas are generated
    """
    def is_valid(formula, allow_power):
        try:
            cfg = FormulaConfig.deserialize(formula, vars_num)
            
            # Check variable sets used
            used_vars = set()
            
            # Check if nodes are valid and record variable usage
            def check_node(node):
                if isinstance(node, Variable):
                    used_vars.add(node.index)
                    return True
                elif isinstance(node, Power):
                    if not allow_power:  # If power operations are not allowed
                        return False
                    if not isinstance(node.var, Variable):
                        return False
                    if node.exponent < 1:
                        return False
                    used_vars.add(node.var.index)
                    return True
                elif isinstance(node, Multiply):
                    # Check if multiplication has a constant on one side
                    left_const = isinstance(node.left, Constant)
                    right_const = isinstance(node.right, Constant)
                    if not left_const and not right_const:
                        return False
                return True
            
            # Breadth-first traversal to check all nodes
            from collections import deque
            queue = deque([cfg.root])
            while queue:
                node = queue.popleft()
                if not check_node(node):
                    return False
                
                # Add child nodes to queue
                if hasattr(node, 'left'):
                    queue.append(node.left)
                if hasattr(node, 'right'):
                    queue.append(node.right)
                if hasattr(node, 'var') and not isinstance(node, Power):
                    queue.append(node.var)
                if hasattr(node, 'num'):
                    queue.append(node.num)
                    queue.append(node.den)
            
            # Check if at least one variable is used
            if not used_vars:
                return False
                
            return True
        except Exception as e:
            print(f"Validation failed: {str(e)}")
            return False

    valid_formulas = []
    attempts = 0
    max_attempts = formula_num * 10
    
    while len(valid_formulas) < formula_num and attempts < max_attempts:
        attempts += 1
        try:
            new_formula = generate_formula(vars_num, is_cond, allow_power, max_depth=max_depth)
            if is_valid(new_formula, allow_power) and new_formula not in valid_formulas:
                valid_formulas.append(new_formula)
        except Exception as e:
            continue
    
    if not valid_formulas:
        raise ValueError(f"Failed to generate any valid formulas after {max_attempts} attempts")
    
    return valid_formulas

def build_system(configs, vars, var_names=None):
    """
    Build equation system, generate Z3 expressions and LaTeX format strings.
    
    Args:
        configs (list[str]): List of serialized formula configurations
        vars (list): Z3 variable list
        var_names (list[str], optional): Variable name list, used for LaTeX output
        
    Returns:
        dict: Dictionary containing the following keys:
            - 'z3_expr': List of Z3 expressions for all formulas
            - 'z3_constraint': List of all constraint conditions
            - 'latex_str': LaTeX format string representation of the system
            
    Notes:
        1. When there's only one formula, returns a single LaTeX expression
        2. Multiple formulas are wrapped in cases environment
        3. Automatically adds positive exponent constraints for power operations
    """
    vars = list(vars)
    vars_num = len(vars)
    configs = [FormulaConfig.deserialize(config, vars_num=vars_num) for config in configs]
    # print("configs: ", configs)
    
    z3_vars = vars
    str_vars = var_names if var_names else [v.decl().name() for v in vars]
    
    # Collect all expressions and constraints
    all_exprs = []
    all_constraints = []
    
    for config in configs:
        expr, constraints = config.root.to_z3(z3_vars)
        all_exprs.append(expr)
        all_constraints.extend(constraints)
        if isinstance(config.root, Power):
            all_constraints.append(config.root.exponent > 0)
    
    # print("all_exprs: ", all_exprs)
    # print("all_constraints: ", all_constraints)
    
    return {
        'z3_expr': all_exprs,
        'z3_constraint': all_constraints,
        'latex_str': r'\begin{cases} ' + ' \\\\ '.join(
            [config.get_latex(str_vars) for config in configs]
        ) + r' \end{cases}' if len(configs) > 1 else configs[0].get_latex(str_vars)
    }

def get_formula_value(config, values): 
    """
    Calculate the value of a formula given variable values.
    
    Args:
        config (str): Serialized formula configuration
        values (list): List of variable values, order corresponds to variable indices
        
    Returns:
        float: Formula calculation result
        
    Notes:
        1. Variable value list length must match the number of variables in the formula
        2. Handles all supported operation types (addition, subtraction, multiplication, division, power operations, etc.)
    """
    return FormulaConfig.deserialize(config, vars_num=len(values)).get_value(values)

if __name__ == "__main__":
    configs = generate_formulas(formula_num=2, vars_num=3, is_cond=True)
    print("configs:", configs)
    
    vars = [z3.Real('x'), z3.Real('y'), z3.Real('z')]
    
    system = build_system(configs, vars)
    print("Generated System:")
    print(system['latex_str'])
    
    solver = z3.Solver()
    solver.add(system['z3_expr'])
    print("\nZ3 Constraints:", solver)