# Specification

In this section, we introduce the details of PuzzleClone's specification file. The meaning and format of each attribute will be explained here. Please note that the attributes will be parsed **in order**, and the order is the same as the introduction order below. For example, as the first attribute introduced below, `custom_operator` is processed first, so operators defined in this attribute can be used by any other attributes. But the opposite is invalid: **please make sure when specifying an attribute, don't use any variables, symbols, or operators defined in attributes that will be later parsed.** In addition, please make sure the names for custom operators, variables, symbols, and conditions do not duplicate or conflict with Python reserved words.

## custom_operator

**Type:** `Dict[str, str]`

Dictionary of custom operators. You can define a list of custom operators (functions) here for later use in the definition of variables, symbols, and conditions.

Key: Operator name.

Value: Python lambda-expression string defining the operator OR the path to a Python file containing the operator definition (the path should be relative to the root directory).

**Example:**
```
custom_operator:
    double: "lambda x: x * 2"
    reformat: "customs/mathexpr_generator.py"
```

## variables

**Type:** `Dict[str, Variable]`

Dictionary of custom variables. Variables should be defined in order without dependency conflicts, i.e., the definition of previous variables should not include any variables defined later.

**Key:** Variable name.

**Value:** A `Variable` object with the following attributes. Please note that PuzzleClone supports two mutually exclusive ways of defining variables: 

- By specifying `type` and `domain`.
- By providing a custom formula in `formula`.

### Variable Attributes

#### type
**Type:** `Optional[str]`

The type of the variable.

**Examples:**

- `"int"`: Represents an integer variable.
- `"bool"`: Represents a boolean variable.

#### domain
**Type:** `Optional[str]`

The domain of the variable.

**Examples:**

- `"[1, 10]"`: Represents integers from 1 to 10.
- `"[True, False]"`: Represents boolean values.
- `"['red', 'blue', 'green']"`: Represents a selection from the given options.

#### formula
**Type:** `Optional[str]`

The formula used to initialize the variable.

**Example:**

- `"randint(1,6) + randint(1,6)"`: Represents the sum of two dice rolls.

**Notes:**

- If `formula` is defined, `type` and `domain` must not be defined.
- If `formula` is not defined, both `type` and `domain` must be defined.

**Example:**
```yaml
variables:
    n:
        type: "int"
        domain: "[3, 5]"
    dice_sum:
        formula: "randint(1,6) + randint(1,6)"
```

## symbols

**Type:** `Optional[Dict[str, Union[DefinedSymbol, DerivedSymbols, DerivedSymbol]]]`

Dictionary of symbol definitions. Symbols are the core elements in puzzle generation representing entities in the puzzle. Symbols differ from Variables in that Symbols are often unknown and to be solved, while Variables are often known values explicitly specified in the puzzle description.

**Key:** Symbol name.

**Value:** A symbol object which can be one of:

- `DefinedSymbol`: Basic symbol definition
- `DerivedSymbol`: Symbol derived from other symbols using operators
- `DerivedSymbols`: Container for multiple derived symbol templates with random counts (i.e., a fixed number of symbols will be generated, but each symbol can randomly follow the structure defined in any of the provided templates.)

### DefinedSymbol

Defines basic symbol templates used in puzzle generation.

**Note:** Symbols defined in this attribute will be processed as follows. First, PuzzleClone iterates over all values of each data source defined in `source` below. Each value (if there is one data source) or each unique value pair (if there are multiple data sources) will be used as a *key* and mapped to a Z3 symbol, with the symbol's content dependent on `type`, `attr`, and `desc`. One can use `<symbol_name>[<key>]` to get the Z3 symbol corresponding to the provided key. If only the list of Z3 symbols are needed, use `<dict_name>.to_list()` or `list(<dict_name>)` method to convert the dictionary values to a list.

#### source
**Type:** `List[str]`

A list of data sources. Each element should be a string of the data source's name (e.g., variables). When one data source is provided, each value of that data source will be used as a symbol key. When multiple sources exist, each value tuple in the Cartesian Product of the data sources' values will be used as a symbol key.

**Examples:**

- When length is 1: The primary key is a string.
  - Example: `source = ["children"]` with `children = ["Alice", "Bob"]` will generate two symbols with primary keys "Alice" and "Bob".
  
- When length > 1: The primary key is a tuple.
  - Example: `source = ["children", "adults"]` with `children = ["Alice", "Bob"]`, `adults = ["Chris"]` will generate symbols with primary keys `("Alice", "Chris")` and `("Bob", "Chris")`.

#### attr
**Type:** `Optional[List[str]]`

List of symbol attributes defining additional characteristics.

**Examples:**

- `["color", "size"]` indicates the symbol has color and size attributes.

**Notes:**

- When `None` (default), symbols can be accessed directly via dictionary keys (e.g., `symbol[key]`).
- When specified, symbols must be accessed using `get()` method (`symbol[key].get('color')`).

#### type
**Type:** `Union[str, List[str]]`

Type definition rules for the symbol. When `attr` is `None`, the value should be a *single type*. Otherwise, the value should be a list of *single types*. The list should has the same length with the value of `attr`, with each type in the list corresponding to each attribute of the symbol.

**Valid single types:** `'int'`, `'bool'`, `'float'`, and `'enum'`.

**Examples:**

- Single type string when `attr` is `None`: `"bool"`
- Type list matching `attr` length when `attr` exists: `["int", "bool"]`

#### desc
**Type:** `Optional[Union[str, List[str]]]`

Description template for the symbol. Similar to `type`, the type of this attribute should be `str` if `attr` is `None`, or `List[str]` otherwise (length equal to `attr`).

**Examples:**

- Single string when no attributes: `"Basic proposition symbol"`. It can also be a Python f-string, e.g., `{_names} is selected` (the prefix 'f' is omitted here). To use the values in the data sources, the value if the brackets can be "_" appended with the data source name.
- List matching `attr` length when attributes exist: `["Color description", "Size description"]`

### DerivedSymbol

Symbols from existing ones using operators or formulas. The derivation works by first randomly selecting a number of values from the `source` list and creating new symbols with the selected values.

**Selection Process (before optimization):**

1. For each domain (total count specified by `domain`):
    - a. For each dimension (count specified by `dim`):
        - i. For each data source in `source`:
            - Select `amount[k]` items from `source[k]` following `order` and `duplicate` rules
    - b. Verify dimension-level conditions (`dim_cond` and custom conditions with `scope='dim'`)
2. Verify domain-level conditions (`domain_cond` and custom conditions with `scope='domain'`)

#### source
**Type:** `List[str]`

Data sources for the selection. Each element must be a string representing either:

- A stringified list of literals (e.g., `'[True, False]'`)
- A variable name containing the data

#### amount
**Type:** `Optional[list]`

Number of items selected from each data source.

**Examples:**

- `["2", "1"]`: Select 2 items from first source, 1 from second
- `None`: Select exactly 1 item from each source (default)

**Note:**

- Length must match `source`
- Each value must be a string (literal or variable name)

#### order
**Type:** `Optional[List[bool]]`

Permutation configuration per data source during selection. Controls whether selection order matters:

- `True`: Permutation (order matters)
- `False`: Combination (order doesn't matter)

**Default:** All `True` (order matters for all sources)

**Note:** Length must match `source`

#### duplicate
**Type:** `Optional[List[bool]]`

Selection repetition rules per data source during selection. Controls whether duplicates are allowed:

- `True`: Allow duplicate selections
- `False`: Disallow duplicates

**Default:** All `False` (no duplicates allowed)

**Note:** Length must match `source`

#### domain
**Type:** `Optional[str]`

Total number of selections.

**Examples:**

- `"5"`: Make 5 selections from the data sources
- `"n"`: Use variable `n` to determine count

**Note:** Must be a string representing a literal or variable name

#### domain_cond
**Type:** `bool`

Global repetition rule for symbol selection. Controls whether identical symbol combinations are allowed:

- `True`: Disallow identical combinations
- `False`: Allow duplicates

**Default:** `True` (no identical combinations)

#### dim
**Type:** `int`

Number of dimensions for the derived symbol.

**Example:** `2` generates two-dimensional symbol matrix (useful for statements with multiple clauses).

**Default:** `1`

#### dim_cond
**Type:** `Optional[list]`

Inter-dimensional constraints (list of conditions).

**Example:** `[[0, 1], [2]]` means values from `source[0]` and `source[1]` cannot be identical at the same time **AND** values from `source[2]` cannot be identical.

**Note:** Cannot contain duplicate indices.

**Default:** `[[0, 1, ..., len(source)]]` (i.e., all selections must be different in at least one source).

#### custom_cond
**Type:** `Optional[list]`

Custom constraint dictionaries containing:

- `scope`: Application level (`'domain'`/`'dim'`)
- `fields`: List of field indices from source
- `constraint`: Constraint logic expression. Must be a valid Python lambda function string.
  - When `scope="domain"`, the input is a 4-dimensional list, where the selected values can be fetched by `l[domain_index][dim_index][source_index (in 'fields')][amount_index]`.
  - When `scope="dim"`, the input is a 3-dimensional list, where the selected values can be fetched by `l[dim_index][source_index (in 'fields')][amount_index]`.

#### formula
**Type:** `Optional[str]`

Symbol generation formula using Python syntax.

#### desc
**Type:** `str`

The description text associated with each symbol. To refer to the symbol key, one can use the reserved word `_sym`, which is a 1-dimensional list if `account` is `None` (`_sym[k]` stands for the value of the `k`-th data source in the key), or a 2-dimensional list if `account` is not `None` (`_sym[j][k]` stands for the `k`-th value of the `j`-th data source in the key).

**Default:** `""`

**Example:**
```yaml
# Seed puzzle: There are three boys: A, B and C. One boy broke the vase. When Mom asked them, they responded as follows: A said that C didn't break the vase. B said that A broke the vase. C said that A didn't break the vase. Mom knew that there was exactly one boy who was lying. Question: Who broke the vase?
# In this seed puzzle, the words from the boys were modeled as "symbols" rather than "conditions" because a condition must be true in the final solution while a symbol's value can be either true or false.
symbols:
  names_s: # symbols that represent if each boy broke the vase
    source:
    - names # the names of the boys
    type: Bool
    desc: "{_names} broke the vase"
  speeches_s: # symbols that represent the words from each boy
    source:
    - names_s
    - "[True, False]"
    domain: p_num
    domain_cond: false
    formula: _sym[0] == _sym[1]
    desc: "{names[_index]} said that {get_p(_sym[0], 'names')}{'broke' if _sym[1] else 'didn't break'} the vase."
```

### DerivedSymbols

For deriving a fixed number of symbols of different templates. (i.e., a fixed number of symbols will be generated, but each symbol can randomly follow the structure defined in any of the provided templates.)

#### total
**Type:** `str`

Total number of symbols to generate.

#### templates
**Type:** `List[DerivedSymbol]`

List of symbol templates for generation.

## conditions

**Type:** `Optional[Dict[str, Union[StaticCondition, DynamicCondition]]]`

Conditions defining constraints on symbols and variables.

**Key:** Condition name.

**Value:** A condition object which can be one of:

- `StaticCondition`: Basic constraint definition
- `DynamicCondition`: Advanced constraints whose formulas depend on the selection of values from multiple data sources.

### StaticCondition

Basic constraint definition for puzzle rules.

#### formula
**Type:** `str`

Constraint logic expression using Python syntax.

**Example:** `"x + y < 10"`

#### desc
**Type:** `Optional[str]`

Natural language description for the constraint.

**Example:** `"Sum of two numbers must be less than 10"`

**Default:** `None`

### DynamicCondition

Advanced constraints whose formulas depend on the selection of values from multiple data sources. Includes all attributes from `StaticCondition` plus additional ones listed below.

#### source
**Type:** `list`

Data sources (same format as `DerivedSymbol.source`).

#### amount
**Type:** `Optional[list]`

Number of selections per data source (same format as `DerivedSymbol.amount`).

#### order
**Type:** `Optional[List[bool]]`

Permutation configuration(same format as `DerivedSymbol.order`).

**Default:** All `True`

#### duplicate
**Type:** `Optional[List[bool]]`

Repetition rule configuration (same format as `DerivedSymbol.duplicate`).

**Default:** All `False`

#### domain
**Type:** `Optional[str]`

The range of total condition count. Must be a range string `"[min, max]"`. If `None`, one condition will be generated.

**Example:** `"[1, 5]"`: Generate between 1 and 5 conditions.

#### domain_cond
**Type:** `bool`

Global repetition rule for selection (same format as `DerivedSymbol.domain_cond`).

**Default:** `True`

#### custom_cond
**Type:** `Optional[list]`

Custom constraints (same format as `DerivedSymbol.custom_cond`).

**Example:**
```yaml
conditions:
    basic_constraint:
        formula: "x + y < 10"
        desc: "The sum of x and y must be less than 10."
    
    dynamic_constraint:
        source: ["children"]
        domain: "[2, 4]"
        formula: "age[_sym[0]] > 5"
        desc: "{_sym[0]}'s age is greater than 5."
```

## calc_solution

**Type:** `bool`

Whether to compute solutions (`true` by default). It will be set to `false` in some cases when no SMT calculation is needed at all to derive the puzzle solution.

**Default:** `True`

## max_solution

**Type:** `int`

Maximum number of solutions to generate. This attribute can be set to prevent over time-consuming calculation.

**Note:**

- Here, "solution" refers to a valid configuration of all symbols that satisfies all constraints (i.e., a Z3 solution). It does NOT mean the number of valid answers to the final question in the puzzle.
- If the number of solutions exceeds this limit, the solver will stop and raise an exception.

**Default:** `6000`

## post_generation

**Type:** `Optional[PostGen]`

Initialization after computing the problem solution for the first time. Applicable for scenarios where parameters in the actual puzzle description need to be computed using Z3. In these cases, one solution will be randomly selected from all Z3 solutions (accessible by the reserved word `_sol`), and the solution can be used to determine the puzzle parameters. After this initialization, the Z3 solver will be called again to solve the updated model.

### PostGen Attributes

#### post_gen_vars
**Type:** `Optional[Dict[str, str]]`

Extracting the values of symbols from `_sol` (the selected solution) as new variables.

**Key:** The new variable name.

**Value:** The expression to compute the variable value, which can be a string of a Python expression.

#### post_gen_conditions
**Type:** `Optional[Dict[str, StaticCondition]]`

New constraints to add based on the selected solution.

**Key:** The new constraint name.

**Value:** A string of the formula for the constraint.

**Example:**
```yaml
post_generation:
    post_gen_vars:
        max_value: "max([_sol[key] for key in _sol])"
    post_gen_conditions:
        new_constraint:
            formula: "x < max_value" # x is a symbol defined before
            desc: "x must be less than the maximum value."
```

## optimize

**Type:** `Optional[Optimize]`

Optimization target definition (for optimization problems only).

### Optimize Attributes

#### type
**Type:** `str`

Optimization type (i.e., whether the puzzle aims to maximize or minimize a given formula).

**Valid Values:**

- `"minimize"`: Minimize the formula
- `"maximize"`: Maximize the formula

#### formula
**Type:** `str`

Formula to optimize.

**Example:**
```yaml
optimize:
    type: "minimize"
    formula: "x + 2*y"
```

## queries

**Type:** `Optional[Dict[str, Union[QuerySelectionWithMultipleTemplates, QuerySelectionWithSingleTemplate, Query]]]`

Dictionary of question definitions.

**Key:** Query name.

**Value:** A query object which can be one of:

- `Query`: Open-ended question
- `QuerySelectionWithSingleTemplate`: Multiple-choice question whose options follow a single template
- `QuerySelectionWithMultipleTemplates`: Multiple-choice question whose options follow multiple templates

### Query

#### desc
**Type:** `str`

Question description text (may contain placeholders).

**Example:** `"What is the value of x?"`

#### ans_formula
**Type:** `str`

Answer generation formula. The result can be referred to as `_ans` and used in `ans_text`.

#### ans_text
**Type:** `str`

A textual string representing the puzzle answer. Can be a normal string or a Python f-string (no need to specify the prefix "f").

#### ans_assertion
**Type:** `Optional[str]`

Assertion for answer validation. For example, if the puzzle should only have one valid solution, one can use `len(_solutions) == 1`. (Note: this assertion means that there is only one Z3 solution. While in most cases it will lead to a unique solution for the entire puzzle, it is not always the case, so please be cautious.)

**Default:** `"len(_solutions) == 1"`

### QuerySelectionWithSingleTemplate

Multiple-choice question with a single template for generating options.

#### desc
**Type:** `str`

Question description text (may contain placeholders).

**Example:** `"Which option satisfies the condition?"`

#### query_type
**Type:** `str`

Question type.

**Valid Values:**

- `'single_choice'`: Single correct answer
- `'multiple_choice'`: Multiple correct answers *(not supported for now)*

**Default:** `'single_choice'`

#### select_type
**Type:** `bool`

Whether the question asks the reader to select the correct or incorrect option(s). (e.g., Which of the following options is true (or false)?)

**Valid Values:**

- `True`: Select the correct option(s)
- `False`: Select the incorrect option(s)

**Default:** `True`

#### opt_num
**Type:** `Optional[int]`

Total number of options.

**Default:** `4`

#### source
**Type:** `list`

Data source (same format as `DerivedSymbol.source`). Please note that the result should be accessed by the reserved word `_opt`.

#### amount
**Type:** `Optional[list]`

Number of selections per source (same format as `DerivedSymbol.amount`).

#### order
**Type:** `Optional[List[bool]]`

Permutation configuration (same format as `DerivedSymbol.order`; Please note that the default value is different).

**Default:** First dimension `False`, others `True`

#### duplicate
**Type:** `Optional[List[bool]]`

Repetition rule configuration (same format as `DerivedSymbol.duplicate`; Please note that the default value is different).

**Default:** All `False`

#### cond
**Type:** `str`

Defines when an option should be treated as valid. The validity of an option will be determined by iterating on all solutions generated by the Z3 solver (can be accessed by `_model` in `opt_formula`) and then evaluating the `opt_formula`. When `cond = 'any'`, if the `opt_formula` is `True` for at least one Z3 solution, the option will be viewed as a correct option, otherwise incorrect. When `cond = 'all'`, if the `opt_formula` is `True` for all Z3 solutions, the option will be viewed as a correct option, otherwise incorrect.

**Valid Values:**

- `'any'`: The option is true if at least one Z3 solution satisfies `opt_formula`
- `'all'`: The option is true if all Z3 solutions satisfy

**Default:** `'any'`

#### opt_formula
**Type:** `str`

Option correctness evaluation expression. Note: one can use `_model` to access the Z3 solution being iterated on, or `_solutions` to access the list of all Z3 solutions.

**Example:** `"x % 2 == 0"`

#### opt_text
**Type:** `Optional[str]`

Template for the option description (a regular Python string or a f-string without the prefix "f").

**Example:** `"{_opt[0][0]}"`

**Note:** Automatically prefixed with ABCD, no need to include in string.

#### custom_cond
**Type:** `Optional[list]`

Custom constraints (same format as `DerivedSymbol.custom_cond`). Options should be referred to by `_opt`.

### QuerySelectionWithMultipleTemplates

Multiple-choice question whose options follow multiple templates.

Includes the same attributes as `QuerySelectionWithSingleTemplate`: `desc`, `query_type`, `select_type`, and `opt_num`, plus additional ones listed below.

A total of `opt_num` options will be generated, but each option can randomly follow any of the specified template (the option number specified in each template will still be considered). 

#### templates
**Type:** `List[QuerySelectionTemplate]`

List of option templates. Each template contains the attributes: `source`, `amount`, `order`, `duplicate`, `cond`, `opt_formula`, `opt_text`, and `custom_cond`.

**Example:**
```yaml
queries:
    q1:
        desc: "Which of the following must be true?"
        opt_num: 4
        templates:
            - source:
                  - names
              amount:
                  - '2'
              domain: "[2, 2]"
              cond: all
              opt_formula: "all([get_value(_model, buy[(_opt[0][0], f)]) != None and get_value(_model, buy[(_opt[0][1], f)]) != None for f in food]) and sum([get_value(_model, buy[(_opt[0][0], f)]) and get_value(_model, buy[(_opt[0][1], f)]) for f in food]) == 1"
              opt_text: "There is exactly 1 type of food that both {_opt[0][0]} and {_opt[0][1]} bought."
            - source:
                  - names
                  - food
                  - "[False, True]"
              amount:
                  - '1'
                  - '1'
                  - '1'
              domain: "[2, 2]"
              cond: all
              opt_formula: "get_value(_model, buy[(_opt[0][0], _opt[1][0])]) == _opt[2][0]"
              opt_text: "{_opt[0][0]} {'bought' if _opt[2][0] else 'did not buy'} {_opt[1][0]}."
```

## desc

**Type:** `str`

Overall template description for puzzle description. Should be a regular Python string or a Python f-string without the prefix "f". E.g., `There are three boys: {', '.join(names)}. ...` where `names` is a list of names defined in the variables of the puzzle specification.