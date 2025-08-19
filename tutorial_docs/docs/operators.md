# Operators

In PuzzleClone, **operators** are powerful helper functions you can use directly in your specification files. They handle common tasks like generating random data, creating dynamic formulas, and formatting text, keeping your YAML clean and readable.

PuzzleClone comes with a rich set of built-in operators, and you can even add your own for maximum flexibility.

## Built-in Operators

Here are a few of the most commonly used operators that come standard with PuzzleClone.

### generate_random_list

Creates a list of random values with fine-grained control. Perfect for when you need a list of numbers or items that follow specific rules.

```python
def generate_random_list(size, ele_type, ele_domain, cond=[], per_ele_domain=None):
    """
    Returns a random list with element-level range control.

    - size (int): The desired length of the list.
    - ele_type (str): The type of elements, such as 'int', 'bool', or 'float'.
    - ele_domain (list | tuple): The global value range for all elements.
    - cond (list): A list of functions (as strings) that the final list must satisfy.
      Example: ["lambda l: sum(l) > 10", "lambda l: l[0] != l[1]"]
    - per_ele_domain (list, optional): A list of specific domains for each element,
      overriding the global `ele_domain`. Use `None` for elements that should use
      the global domain.
    """
```

### generate_random_list_with_total

A specialized and faster version of `generate_random_list` for a common scenario: creating a list of random integers that must add up to a specific total.

```python
def generate_random_list_with_total(size, ele_domain, total, per_ele_domain=None):
    """
    Returns a random integer list with a fixed sum.

    - size (int): The length of the list.
    - ele_domain (list | tuple): The global value range for each element, e.g., [1, 10].
    - total (int): The exact sum that all elements in the list must add up to.
    - per_ele_domain (list, optional): Independent value ranges for each element.
    """
```

### get_faker

Generates realistic-looking fake data (like names, addresses, or phone numbers) using the popular [Faker](https://faker.readthedocs.io/) library. This is fantastic for adding flavor and realism to your puzzles.

```python
def get_faker(num, provider_name, locale='en_US', seed=None):
    """
    Generates a specified number of unique fake data entries using Faker.

    - num (int): The number of unique data entries to generate.
    - provider_name (str): The name of the Faker provider method to call (e.g., 'name', 'city').
    - locale (str): The locale for the data (e.g., 'en_US', 'ja_JP').
    - seed (int, optional): A random seed for reproducible results.
    """
```

### make_expr

A powerful utility for dynamically building complex logical or mathematical formulas. This lets you construct `Z3` expressions piece by piece.

```python
def make_expr(op: str, *operands):
    """
    Constructs a Z3 expression from an operator and operands.

    - op (str): An operator identifier.
        - Comparison: "eq" (==), "neq" (!=), "gt" (>), "ge" (>=), "lt" (<), "le" (<=)
        - Logical: "and" (&&), "or" (||), "not" (!), "implies" (=>)
        - Arithmetic: "add" (+), "sub" (-), "mul" (*), "div" (/)

    - *operands: The Z3 symbols or values to operate on.

    Examples:
        # Creates the Z3 expression: x >= 5
        make_expr("ge", x, 5)

        # Creates the Z3 expression: And(x > 0, y < 10)
        make_expr("and", x > 0, y < 10)
    """
```

### to_unique

A handy cleanup tool that removes duplicate items from a list while preserving the original order of the first appearance.

```python
def to_unique(l: list):
    """
    Removes duplicates from a list, preserving order.

    - l (list): The input list.

    Example:
        # Returns [1, 2, 3]
        to_unique([1, 2, 1, 3])
    """
```

### Mathematical Expression Generators

PuzzleClone includes specialized operators for generating complex mathematical expressions and equation systems. These are particularly useful for creating algebra problems, optimization puzzles, and constraint satisfaction problems.

```python
def generate_formula(vars_num, is_cond=False, allow_power=True, max_depth=5):
    """
    Generate a single mathematical formula expression.
    
    - vars_num (int): Number of variables (determines variable index range 0 to vars_num-1)
    - is_cond (bool): Whether to generate comparison expressions (like x > 0)
    - allow_power (bool): Whether to allow power operations (x², x³)
    - max_depth (int): Maximum expression tree depth (controls complexity)
    
    Returns a serialized formula that can be used with Z3 solver and converted to LaTeX.
    """

def generate_formulas(formula_num, vars_num, is_cond=False, allow_power=True, max_depth=5):
    """
    Generate multiple valid mathematical formulas for equation systems.
    
    - formula_num (int): Number of formulas to generate
    - vars_num (int): Number of variables
    - is_cond (bool): Generate comparison expressions instead of equations
    - allow_power (bool): Allow power operations (x², x³)
    - max_depth (int): Expression complexity control
    
    Returns a list of serialized formulas with guaranteed validity and uniqueness.
    """

def build_system(configs, vars, var_names=None):
    """
    Build complete equation systems with Z3 integration and LaTeX output.
    
    - configs (list): List of serialized formula configurations
    - vars (list): Z3 variable list
    - var_names (list, optional): Variable names for LaTeX display
    
    Returns a dictionary with Z3 expressions, constraints, and LaTeX formatting.
    """
```

**Example Usage:**
```yaml
# Generate a system of 3 equations with 2 variables
equations: "{{ generate_formulas(3, 2, false, true, 4) }}"

# Generate inequality constraints
constraints: "{{ generate_formulas(2, 3, true, false, 3) }}"
```

For the complete list of all built-in operators and their details, please refer to our full **[API Documentation](https://puzzleclone.github.io/PuzzleClone/api/index.html)**.

## Custom Operators

While the built-in operators cover many cases, you are not limited by them. You can easily define your own reusable functions using the `custom_operator` field in your specification file.

This is perfect for housing complex logic that you use often or for keeping your YAML templates from getting cluttered.

There are two ways to define a custom operator:

1.  **Simple, In-line Functions:** For short, one-line operations, you can use a `lambda` function directly in the YAML.

2.  **External Python Files:** For more complex logic, it's best practice to define your function in a separate `.py` file and simply point to it.

```yaml
custom_operator:
  # Method 1: A simple lambda function to double a number.
  double: lambda x: x * 2

  # Method 2: A more complex function defined in an external file.
  # PuzzleClone will import the 'reformat' function from this file.
  reformat: customs/mathexpr_generator.py
```