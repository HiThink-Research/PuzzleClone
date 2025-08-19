from typing import List, Dict, Union, Optional
from pydantic import BaseModel, model_validator, GetCoreSchemaHandler
from pydantic_core import core_schema

class Variable(BaseModel):
    """Unified class for defining variables in puzzles.

    This class supports two mutually exclusive ways of defining variables:
    
    - By specifying `type` and `domain`.

    - By providing a custom formula in `formula`.
    """

    type: Optional[str] = None
    """The type of the variable.

    Example:
        - `"int"`: Represents an integer variable.
        - `"bool"`: Represents a boolean variable.
    """

    domain: Optional[str] = None
    """The domain of the variable.

    Example:
        - `"[1, 10]"`: Represents integers from 1 to 10.
        - `"[True, False]"`: Represents boolean values.
        - `"['red', 'blue', 'green']"`: Represents a selection from the given options.
    """

    formula: Optional[str] = None
    """The formula used to initialize the variable.

    Example:
        - `"randint(1,6) + randint(1,6)"`: Represents the sum of two dice rolls.

    Notes:
        - Custom operators defined in the `custom_operator` field of the puzzle template can be used in the formula.
        - If `formula` is defined, `type` and `domain` must not be defined.
    """

    @model_validator(mode='after')
    def validate_exclusive_fields(self):
        """Validates the mutually exclusive constraints between fields.

        Raises:
            ValueError: 
                - If both `formula` and `type`/`domain` are defined.

                - If `formula` is not defined, but `type` or `domain` is missing.

        Example:
            >>> DefinedVar(formula="x+y", type="int")  # Raises ValueError
            >>> DefinedVar(type="int")  # Raises ValueError (missing `domain`)
            >>> DefinedVar(type="int", domain="[1, 10]")  # Valid
            >>> DefinedVar(formula="randint(1,6)")  # Valid
        """
        if self.formula:
            if self.type or self.domain:
                raise ValueError("`formula` cannot be defined along with `type` or `domain`.")
        else:
            if not (self.type and self.domain):
                raise ValueError("When `formula` is not defined, both `type` and `domain` must be defined.")
        return self

class DefinedSymbol(BaseModel):
    """Base class for defining symbol templates used in puzzle generation.

    This class provides the fundamental structure for creating basic symbol elements in puzzles.

    Note: The base data structure is a dictionary, where the keys are the symbol names (or tuples when len(source) > 1) and the values are the Z3 symbols.

    If only the list of Z3 symbols are needed, use `<dict_name>.to_list()` or `list(<dict_name>)` method to convert the dictionary values to a list.
    """

    source: List[str]
    """Initialization expressions for the symbol, serving as primary keys.

    Examples:
        - When length is 1: The primary key is a string.

          Example: source = ["children"] with children = ["Alice", "Bob"] will generate two symbols 
          with primary keys "Alice" and "Bob".
          
        - When length > 1: The primary key is a tuple.
        
          Example: source = ["children", "adults"] with children = ["Alice", "Bob"], adults = ["Chris"]
          will generate symbols with primary keys ("Alice", "Chris") and ("Bob", "Chris").
    """

    attr: Optional[List[str]] = None
    """List of symbol attributes defining additional characteristics.

    Examples:
        - ["color", "size"] indicates the symbol has color and size attributes.
        
    Notes:
        - When None (default), symbols can be accessed directly via dictionary keys (event[key]).
        - When specified, symbols must be accessed using get() method (event[key].get('color')).
    """

    type: Union[str, List[str]]
    """Type definition rules for the symbol.

    Valid Values: 'int' (default), 'bool', 'float', and 'enum'.

    Examples:
        - Single type string when attr is None: "Bool"
        - Type list matching attr length when attr exists: ["int", "bool"]
    """

    desc: Optional[Union[str, List[str]]] = None
    """Description template for the symbol.

    Examples:
        - Single string when no attributes: "Basic proposition symbol"
        - List matching attr length when attributes exist: ["Color description", "Size description"]
    """

    @model_validator(mode='before')
    def validate_type_desc_based_on_attr(cls, values):
        """Validates consistency between attributes, types and descriptions.

        Raises:
            ValueError:
                - ``attr`` is ``None``, but ``type`` is a list.
                
                - ``attr`` exists, but ``type`` is not a list.

                - The format of ``desc`` does not match the presence of ``attr``.

        Examples:
            >>> DefinedSymbol(source=["A"], attr=["color"], type="Str")  # Raises ValueError
            >>> DefinedSymbol(source=["A"], desc=["desc1", "desc2"])  # Raises ValueError
        """
        attr = values.get('attr')
        type_val = values.get('type')
        desc_val = values.get('desc')

        if attr is None:
            # 当 attr 为 None 时，type 应该是 str，desc 应该是 Optional[str]
            if isinstance(type_val, list):
                raise ValueError("When attr is None, type must be str")
            if desc_val is not None and isinstance(desc_val, list):
                raise ValueError("When attr is None, desc must be str or None")
        else:
            # 当 attr 是 list 时，type 和 desc 也应该是 list
            if not isinstance(type_val, list):
                raise ValueError("When attr is list, type must be list")
            if desc_val is not None and not isinstance(desc_val, list):
                raise ValueError("When attr is list, desc must be list or None")

        return values

class DerivedSymbol(BaseModel):
    """Class defining rules for generating derived symbols from existing ones.
    
    The derivation works by first randomly selecting a number of values from the `source` list and creating new symbols with the selected values.

    Selection Process (before optimization):
    
    1. For each domain (total count specified by ``domain``):
        a. For each dimension (count specified by ``dim``):
            i. For each data source in ``source``:
                - Select ``amount[k]`` items from ``source[k]`` following ``order`` and ``duplicate`` rules
        b. Verify dimension-level conditions (``dim_cond`` and custom conditions with scope='dim')
    2. Verify domain-level conditions (``domain_cond`` and custom conditions with scope='domain')

    Example

    .. code-block:: python

        "max_num": {
            "source": ["range(p_num)", "range(2, 11)"],
            "domain": "3",
            "custom_cond": [{
                "scope": "domain",
                "fields": [0, 1],
                "constraint": "lambda l: all([item[0][1][0] < money // prices[item[0][0][0]] for item in l])"
            }],
            "formula": "num[names[_sym[0]]] <= _sym[1]",
            "desc": "The maximum number of Award {names[_sym[0]]} that a person can take is {_sym[1]}."
        }

    This configuration will:

    - Generate 3 symbols (``domain = 3``)

    - Each symbol has 1 dimension (default ``dim = 1``)

    - Each dimension uses 2 data sources (``len(source) = 2``)

    - The first source provides integers from 0 to ``p_num - 1``

    - The second source provides integers from 2 to 10

    - Selects 1 item from each source (default when ``amount`` is None)

    - Applies custom domain-level constraint on the selected values
    """

    source: List[str]
    """Data sources for the selection. 

    Each element must be a string representing either:

    - A stringified list of literals (e.g., '[True, False]')

    - A variable name containing the data
    """

    amount: Optional[list] = None
    """Number of items selected from each data source.

    Examples:
        - ["2", "1"]: Select 2 items from first source, 1 from second

        - None: Select exactly 1 item from each source (default)

    Note:
        - Length must match ``source``

        - Each value must be a string (literal or variable name)
    """

    order: Optional[List[bool]] = None
    """Permutation configuration per data source during selection.
    
    Controls whether selection order matters:

    - True: Permutation (order matters)

    - False: Combination (order doesn't matter)

    Default:
        All True (order matters for all sources)

    Note:
        Length must match ``source``
    """

    duplicate: Optional[List[bool]] = None
    """Selection repetition rules per data source during selection.
    
    Controls whether duplicates are allowed:

    - True: Allow duplicate selections

    - False: Disallow duplicates

    Default:
        All False (no duplicates allowed)

    Note:
        Length must match ``source``
    """

    domain: Optional[str] = None
    """Total number of selections.

    Examples:
        - "5": Make 5 selections from the data sources
        - "n": Use variable `n` to determine count

    Note:
        Must be a string representing a literal or variable name
    """

    domain_cond: bool = True
    """Global repetition rule for symbol selection:
    
    Controls whether identical symbol combinations are allowed:

    - True: Disallow identical combinations

    - False: Allow duplicates

    Default:
        True (no identical combinations)
    """

    dim: int = 1
    """Number of dimensions for the derived symbol.

    Example: 
        - 2 generates two-dimensional symbol matrix (useful for statements with multiple clauses).
    """

    dim_cond: Optional[list] = []
    """Inter-dimensional constraints (list of conditions).

    Example: 
        - [[0, 1], [2]] means values from `source[0]` and `source[1]` cannot be identical at the same time AND values from `source[2]` cannot be identical.

    Note: 
        - Cannot contain duplicate indices.

    Default: 
        - [[0, 1, ..., `len(source)`]] (i.e., all selections must be different in at least one source).
    """

    custom_cond: Optional[list] = []
    """Custom constraint dictionaries containing:
    
    - scope: Application level ('domain'/'dim')

    - fields: List of field indices from source

    - constraint: Constraint logic expression. Must be a valid Python lambda function string. 
        - When scope="domain", the input is a 4-dimensional list, where the selected values can be fetched by `l[domain_index][dim_index][source_index (in 'fields')][amount_index]`.
        - When scope="dim", the input is a 3-dimensional list, where the selected values can be fetched by `l[dim_index][source_index (in 'fields')][amount_index]`.
    """

    formula: Optional[str] = None
    """Symbol generation formula using Python syntax."""

    desc: str = ""
    """Symbol collection description text for puzzle generation."""


class DerivedSymbols(BaseModel):
    """Container for multiple derived symbol templates with random counts."""

    total: str
    """Total number of symbols to generate."""

    templates: List[DerivedSymbol]
    """List of symbol templates for generation."""


class StaticCondition(BaseModel):
    """Base constraint definition for puzzle rules."""

    formula: str
    """Constraint logic expression using Python syntax.

    Example: "x + y < 10"
    """

    desc: Optional[str] = None
    """Natural language description for puzzle text generation.

    Example: "Sum of two numbers must be less than 10"
    """

class DynamicCondition(StaticCondition):
    """Extended constraints with multi-dimensional parameters."""

    source: list
    """Data sources (same format as DerivedSymbol)."""

    amount: Optional[list] = None
    """Number of selections per data source. (same format as DerivedSymbol)"""

    order: Optional[List[bool]] = None
    """Permutation configuration (default all True)."""

    duplicate: Optional[List[bool]] = None
    """Repetition rule configuration (default all False)."""

    domain: Optional[str] = None
    """Total condition count. Must be a range string "[min, max]". If None, one condition will be generated.
    
    Example:
        - "[1, 5]": Generate between 1 and 5 conditions.
    """

    domain_cond: bool = True
    """Global repetition rule."""

    custom_cond: Optional[list] = []
    """Custom constraints (same format as DerivedSymbol)."""

class PostGen(BaseModel):
    """
    Initialization after computing the problem solution for the first time. (Applicable for scenarios where parameters in the actual problem need to be computed using z3)
    """
    post_gen_vars: Optional[Dict[str, str]] = None
    """Extracting the values of symbols from _sol (the selected solution) as new variables.
    
    Key: The new variable name.

    Value: The expression to compute the variable value, which can be a string of a Python expression.
    """

    post_gen_conditions: Optional[Dict[str, StaticCondition]] = None
    """New constraints to add after initial solution.
    
    Key: The new constraint name.

    Value: A string of the formula for the constraint.
    """
class Optimize(BaseModel):
    """Optimization target definition (for optimization problems only)."""

    type: str
    """Optimization type ("minimize" or "maximize")."""

    formula: str
    """Formula to optimize."""

class QueryBase(BaseModel):
    """Base class for question definitions."""

    desc: str
    """Question description text (may contain placeholders).

    Example: "Which option satisfies the condition?"
    """

class QuerySelectionBase(QueryBase):
    """Multiple-choice question definition."""

    query_type: str = "single_choice"
    """Question type:
    
    - 'single_choice': Single correct answer
    - 'multiple_choice': Multiple correct answers
    """

    select_type: bool = True
    """Whether to select the correct or incorrect option(s):
    
    - True: Select the correct option(s)
    - False: Select the incorrect option(s)
    """

    opt_num: Optional[int] = 4
    """Total number of options to present (default 4)."""

class QuerySelectionTemplate(BaseModel):
    """Template for multiple-choice options.
    
    The option generation process works by randomly selecting a number of values from the `source` list to create options.
    """

    source: list
    """Data source. (Same format as DerivedSymbol.source)"""

    amount: Optional[list] = None
    """Number of selections per source. (Same format as DerivedSymbol.amount)"""

    order: Optional[List[bool]] = None
    """Permutation configuration (default first dimension False, others True)."""

    duplicate: Optional[List[bool]] = None
    """Repetition rule configuration. (default all False)"""

    cond: str = 'any'
    """Constraint scope:
    
    - 'any': At least one solution satisfies

    - 'all': All solutions satisfy
    """

    opt_formula: str
    """Option correctness evaluation expression.

    Example: "x % 2 == 0"
    """

    opt_text: Optional[str] = None
    """Option display template (may contain placeholders).

    Example: "{_opt[0][0]}"

    Note:
        - Automatically prefixed with ABCD, no need to include in string.
    """

    custom_cond: Optional[list] = []
    """Custom constraints (same format as DerivedSymbol.custom_cond)."""

class QuerySelectionWithSingleTemplate(QuerySelectionBase, QuerySelectionTemplate):
    """Single template for multiple-choice questions."""
    pass


class QuerySelectionWithMultipleTemplates(QuerySelectionBase):
    """Multiple templates for multiple-choice questions."""

    templates: List[QuerySelectionTemplate]
    """List of option templates."""

class Query(QueryBase):
    """Open-ended question definition."""

    ans_formula: str
    """Answer generation formula."""

    ans_text: str
    """Answer text format."""

    ans_assertion: Optional[str] = "len(_solutions) == 1"
    """Assertion for answer validation."""


class PuzzleTemplate(BaseModel):
    """Main puzzle template structure integrating all components."""

    custom_operator: Optional[Dict[str, str]] = None
    """Dictionary of custom operators.

    Key: Operator name.

    Value: Python expression string defining the operator OR the path to a Python file containing the operator definition.
    
    Example: {"double": "lambda x: x * 2", "reformat": "customs/mathexpr_generator.py"}
    """

    variables: Dict[str, Variable]
    """Dictionary of variable definitions (name: definition)."""

    symbols: Optional[Dict[str, Union[DefinedSymbol, DerivedSymbols, DerivedSymbol]]] = None
    """Dictionary of symbol definitions (name: definition)."""

    conditions: Optional[Dict[str, Union[StaticCondition, DynamicCondition]]] = None
    """Dictionary of conditions."""

    calc_solution: bool = True
    """Whether to compute solutions (default True)."""

    max_solution: int = 6000
    """Maximum number of solutions to generate.
    
    Note:
        - Here, "solution" refers to a valid configuration of all symbols that satisfies all constraints. It does NOT mean the number of valid answers to the final question.
        - If the number of solutions exceeds this limit, the solver will stop and raise an exception.
    """

    post_generation: Optional[PostGen] = None
    """Post-generation configuration including:
    
    - post_gen_vars: New variables from solutions
    - post_gen_conditions: Additional constraints
    """

    optimize: Optional[Optimize] = None
    """Optimization target (for optimization problems only)."""

    queries: Optional[Dict[str, Union[QuerySelectionWithMultipleTemplates, QuerySelectionWithSingleTemplate, Query]]] = None
    """Dictionary of question definitions."""

    desc: str
    """Overall template description for puzzle introduction."""

