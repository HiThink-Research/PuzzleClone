# Randomization

When PuzzleClone creates a dynamic condition, a derived symbol, or a set of options, it doesn't just pick things at random. It follows a structured, multi-level process that you can control with remarkable precision. This section explains how that process works. We will first introduce the standard approach, and then move on details of advanced strategies.

## The Standard Randomization Workflow

Think of generating a set of rules or symbols as running a sophisticated assembly line. This assembly line has a three-level hierarchy:

1.  **Domain:** The highest level. If you ask for 3 conditions, the process will run 3 times, once for each "domain" or top-level item.
2.  **Dimension:** The middle level. Within each domain, you can have multiple parts or "dimensions." For example, a student's statement might have two clauses ("It's not iron, *and* it's not copper"). This would be a symbol with `dim: 2`. For standard conditions and options, `dim` is always 1.
3.  **Source:** The lowest level. For each dimension, PuzzleClone draws values from one or more data `source` pools you provide (like a list of numbers or names).

The randomization process flows from the top down:

> For each **Domain**...

> &nbsp;&nbsp;&nbsp;&nbsp;For each **Dimension** in that Domain...

> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;For each data **Source**...

> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;...select the specified `amount` of items.

The selected items are stored in special reserved variables: `_sym` for symbols and conditions, and `_opt` for query options. You can access a specific selected value using the format `_sym[<source_index>][<amount_index>]`.

**Pro Tip:** If you omit the `amount` field, PuzzleClone defaults to selecting exactly one item from that source. In this simpler case, you can access the value directly with `_sym[<source_index>]`.

The real power comes from adding constraints at each of these levels to guide the selection process.

### Level 1: Source Constraints

These constraints control how items are picked *from* a single source pool.

*   `order`: Controls whether the selection order matters.
    *   `true`: **Permutation**. `[A, B]` is different from `[B, A]`.
    *   `false` **Combination**. `[A, B]` is the same as `[B, A]`.
*   `duplicate`: Controls whether an item can be selected more than once from the same source.
    *   `true`: Duplicates are allowed.
    *   `false` All selected items must be unique.

### Level 2: Dimension Constraints

These constraints apply *between* the different sources used within a single dimension. They are perfect for preventing illogical combinations.

The primary tool here is `dim_cond`, which ensures that the items selected from different sources are not all identical. For example, in a statement like "X implies Y," you might want to ensure that X and Y are not the same person.

`dim_cond: [[0, 1]]` means: "The item selected from `source[0]` and the item from `source[1]` cannot be the same at the same time."

If you don't specify `dim_cond`, PuzzleClone defaults to ensuring that the selections for a dimension differ in at least one source, promoting variety.

### Level 3: Domain Constraints

These constraints apply *between* the final, fully-formed items (e.g., between two different conditions).

The `domain_cond` field (which is `true` by default) is a simple boolean that prevents the generator from creating two or more completely identical items. For example, it stops a puzzle from having the exact same rule listed twice.

### Going Further: Custom Constraints

When the built-in constraints aren't enough for your complex logic, you can define your own rules with `custom_cond`. This is a list of constraint objects, where each object has three parts:

*   `scope`: Where the constraint applies. Can be `'dim'` or `'domain'`.
*   `fields`: A list of source indices that the constraint applies to.
*   `constraint`: The logic, written as a Python `lambda` function string.
    *   If `constraint` is `None`, it's a shortcut that means the values from the specified `fields` must be unique.

#### Example 1: The House Number Puzzle

Let's generate rules for a puzzle where a house number must satisfy several conditions.
> *   If it's a multiple of 4, then it's in the 60s.
> *   If it's not a multiple of 5, then it's in the 70s.
> *   If it's not a multiple of 8, then it's in the 80s.

> What is the house number?

When we randomize this, we want to ensure that each rule uses a **unique divisor** (4, 5, 8) and a **unique decade** (60s, 70s, 80s). We can enforce this with `custom_cond`.

```yaml
conditions:
  number_condition:
    source:
    - range(3, 10) # source[0]: the divisor
    - range(2, 10) # source[1]: the decade (e.g., 6 for 60s)
    - "['eq', 'neq']" # source[2]: whether it's a multiple or not
    domain: "[3, 7]" # Generate 3-7 of these conditions
    formula: Implies(...)
    custom_cond:
    # This rule applies across all generated conditions ('domain').
    # It ensures the values from `fields: [0]` (the divisor) are all unique.
    - scope: domain
      fields: [0]
      constraint: None # `None` is a shortcut for "must be unique"
    # This rule does the same for `fields: [1]` (the decade).
    - scope: domain
      fields: [1]
      constraint: None
    desc: "({_index + 1}) If the number is {'not ' if _sym[2] == 'neq' else ''}a multiple of {_sym[0]}, then it is a number from {_sym[1] * 10} to {_sym[1] * 10 + 9}."
```

#### Example 2: The Mystery Ore Puzzle (Revisited)

Recall the puzzle introduced in the [Symbols, Conditions, and Queries](symbols.md) section where students make two-part statements about an ore. A student shouldn't make a nonsensical claim like "It is tin, but it is not tin." We can use `dim_cond` to prevent picking the same ore twice.

But what if we have a stylistic rule, like "a student cannot make two positive claims"? For instance, we want to prevent statements like "It is iron, *and* it is tin." We can enforce this with a custom `lambda` constraint.

```yaml
symbols:
  speech_s:
    source:
    - stones_s # source[0]: a list of ore symbols
    - "[False, True]" # source[1]: False for "is not", True for "is"
    domain: student_num
    dim: 2 # Each speech has two clauses (dimensions)
    dim_cond: # Prevent "It's not tin, but it is not tin"
    - - 0 # The ore from source[0] must be different in the two dimensions.
    custom_cond:
    - scope: dim # This constraint applies to the 2 dimensions within one speech.
      fields: [1] # It looks at the values selected from source[1] ([False, True]).
      # The lambda gets a list of the selections. `sum(...)` counts the number of `True`s.
      # This logic says: "The number of positive 'is' claims must be one or zero."
      constraint: 'lambda l: sum(subl[0][0] for subl in l) <= 1'
    formula: _sym[0] == _sym[1]
    desc: "{students[_index]} says: \"It {'is' if _sym[1] else 'is not'} {get_p(_sym[0], 'stones')}\""
```

## Solve-then-constrain

So far, we've introduced the standard workflow of generating random values for our puzzle variables one by one. This works great for many puzzles, but what if the variables themselves have complex, interlocking constraints? What if generating them independently has almost zero chance of creating a valid, solvable puzzle?

This is where a more advanced technique comes into play: using the solver *itself* to generate the random parameters.

### Example: The Wine Merchant's Puzzle

Let's look at a puzzle that's tricky to generate with simple randomization:

> A wine merchant has 6 barrels of wine and beer, with the following capacities: 30, 32, 36, 38, 40, and 62 gallons.

> *   Five of the barrels contain wine, and one contains beer.

> *   The first customer buys 2 barrels of wine.

> *   The second customer buys twice the *volume* of wine as the first customer.
>
> Which barrel contains the beer? (Barrels are sold whole).

> A. 30
> B. 40
> C. 42
> D. 62

Think about the numbers here. To create a new version of this puzzle, we need to generate a set of barrel volumes where a subset of them (the second customer's purchase) is exactly double the volume of another, disjoint subset (the first customer's purchase). If we just generate random numbers for the barrels, the probability of them satisfying this strict condition is astronomically low. We'd be generating invalid puzzles all day!

To solve this, PuzzleClone uses a clever two-step process:

1.  **Step 1: Generate the Scenario.** We treat the *puzzle parameters themselves* (like the barrel volumes) as unknown symbols. We write down all the constraints they must follow. Then, we ask the symbolic solver to find a valid solution. This solution gives us a complete, valid scenario: the barrel volumes, which barrel has beer, and which barrels each customer bought.
2.  **Step 2: Generate the Puzzle.** Now that we have a valid set of barrel volumes from Step 1, we "lock them in" as fixed parameters. We then run the solver *again* on the actual puzzle, this time to find the final answer (e.g., which barrel has beer). We also make sure this puzzle has a unique solution to avoid ambiguity for the user.

In the PuzzleClone DSL, we achieve this using the `post_generation` field. It allows us to inject new information *after* the first solving step.

```python
class PostGen(BaseModel):
    """
    Defines actions to take after the initial scenario is solved,
    but before the final puzzle is generated.
    """
    post_gen_vars: Optional[Dict[str, str]] = None
    """Extract values from the initial solution (`_sol`) to create new, fixed variables.
    
    Key: The name of the new variable we are creating.
    Value: A Python expression to compute the variable's value from the solution.
    """

    post_gen_conditions: Optional[Dict[str, StaticCondition]] = None
    """Add new, final constraints to the puzzle.
    
    Key: The name of the new constraint.
    Value: The formula for the constraint, which typically uses the `post_gen_vars`.
    """
```

Here is an example specification file for the wine puzzle:

```yaml
variables:
  wine_num: # Total number of barrels (wine + beer)
    type: int
    domain: "[6, 12]"
  beer_num: # Number of beer barrels
    type: int
    domain: "[1, 2]"
  bought_wine_of_first_customer: # Barrels of wine the first customer buys
    type: int
    domain: "[1, wine_num // 2]"
  vol_times: # How many times more wine the second customer buys
    type: int
    domain: "[2, 5]"
  wines: # Unique IDs for our barrels
    formula: generate_letters(wine_num)

symbols:
  # This is a powerful multi-attribute symbol! For each barrel, we have two unknowns:
  # - 'volume': An integer representing its capacity.
  # - 'belonging': An integer representing its status:
  #   0 = beer, 1 = bought by customer 1, 2 = bought by customer 2.
  wine_s:
    source:
    - wines
    attr:
    - volume
    - belonging
    type:
    - int
    - int

# =================================================================
# STEP 1: Define the constraints for a valid scenario.
# The solver will find values for 'volume' and 'belonging' that satisfy all these.
# =================================================================
conditions:
  # The 'belonging' status for each barrel must be 0, 1, or 2.
  wine_belonging:
    formula: And([Or(x == 0, x == 1, x == 2) for x in wine_s.get('belonging')])
  # The number of beer barrels must be correct.
  wine_0:
    formula: Sum([If(x == 0, 1, 0) for x in wine_s.get('belonging')]) == beer_num
    desc: "{beer_num} of the barrels contain beer"
  # The number of barrels for customer 1 must be correct.
  wine_1:
    formula: Sum([If(x == 1, 1, 0) for x in wine_s.get('belonging')]) == bought_wine_of_first_customer
    desc: "the first customer bought {bought_wine_of_first_customer} barrels of wine"
  # The core rule: Customer 2's total volume is N times Customer 1's.
  wine_times:
    formula: Sum([If(x1 == 2, x2, 0) for x1, x2 in zip(wine_s.get('belonging'), wine_s.get('volume'))])
      == vol_times * Sum([If(x1 == 1, x2, 0) for x1, x2 in zip(wine_s.get('belonging'), wine_s.get('volume'))])
    desc: "the second customer bought {vol_times} times the volume of wine as the first"
  # Give the volumes a reasonable range.
  wine_volume_domain:
    formula: And([And(x > 0, x <= 50) for x in wine_s.get('volume')])
  # Ensure all barrel volumes are unique.
  wine_volume_distinct:
    formula: gen_event_count_condition(wine_s.get('volume'), 'distinct')

# =================================================================
# STEP 2: Use the solution from Step 1 to build the final puzzle.
# =================================================================
post_generation:
  # Create a new variable 'vol' by extracting the solved volumes from the initial solution `_sol`.
  post_gen_vars:
    vol: get_value(_sol, wine_s.get('volume'))
  # Now, add a new, hard-coded constraint that locks in these volumes for the final puzzle.
  post_gen_conditions:
    vol_cond:
      formula: And([wine_s[w].get('volume') == vol[i] for i, w in enumerate(wines)])

queries:
  q1:
    desc: "Which barrel{'s' if beer_num > 1 else ''} contain{'s' if beer_num == 1 else ''} beer? (Barrels are sold whole)"
    opt_num: 4
    source:
    - range(0, wine_num) # Options are indices of barrels
    amount:
    - beer_num
    cond: all # The option must be correct in all solutions (should be unique).
    # An option is correct if the 'belonging' status of the chosen barrel is 0 (beer).
    opt_formula: sum([get_value(_model, wine_s[wines[_opt[0][i]]].get('belonging'))
      == 0 for i in range(beer_num)]) == beer_num
    # Display the volume of the barrel in the option text.
    opt_text: "{', '.join([str(vol[_opt[0][i]]) for i in range(beer_num)])}"

desc: "A wine merchant has {wine_num} barrels of wine and beer, with capacities of: {', '.join([str(v) + ' gallons' for v in vol])}.
 There are {wine_num - beer_num} barrels of wine. {wine_0}, {wine_1}, and {wine_times}. All wine barrels are sold.\n{q1}"
```

### Sample Puzzle

The resulting generated puzzle looks clean and perfectly valid, hiding all the complex generation logic from the user:

```json
{
    "problem": "A wine merchant has 9 barrels of wine and beer, with capacities of: 1 gallons, 2 gallons, 3 gallons, 4 gallons, 5 gallons, 6 gallons, 8 gallons, 29 gallons, 30 gallons. There are 8 barrels of wine. 1 of the barrels contain beer, the first customer bought 1 barrels of wine, and the second customer bought 2 times the volume of wine as the first. All wine barrels are sold.\nWhich barrel contains beer? (Barrels are sold whole)\nA. 5\nB. 3\nC. 6\nD. 1\n",
    "answer": "D",
    "parameters": {
        "cond_num": 7,
        "sym_num": 9,
        "sym_type": "[int]"
    },
    "config": {
        "wine_num": 9,
        "beer_num": 1,
        "bought_wine_of_first_customer": 1,
        "vol_times": 2,
        "wines": "['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']",
        "_sol_id": 0,
        "vol": "[1, 2, 3, 4, 5, 6, 8, 29, 30]",
        "_queries": {
            "q1": {
                "pool": "[[['__4__']], [['__2__']], [['__5__']], [['__0__']]]"
            }
        }
    }
}
```

By using this two-step "solve-then-constrain" method, you can generate puzzles with incredibly complex and interdependent parameters that would be nearly impossible to create otherwise.