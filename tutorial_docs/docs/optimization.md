# Solving Optimization Puzzles

So far, we've dealt with puzzles where we need to find *any* valid solution that follows the rules. But what about puzzles where the goal is to find the **best** solution?

Problems like the classic [Knapsack problem](https://en.wikipedia.org/wiki/Knapsack_problem) or [Linear Programming](https://en.wikipedia.org/wiki/Linear_programming) challenges fall into this category. The goal isn't just to find a valid combination, but to **minimize** a cost or **maximize** a value. These puzzles can have a massive number of potential solutions, making it impossible to check them all manually.

This is where PuzzleClone's `optimize` field comes in. Powered by a symbolic optimizer, it lets you generate puzzles that find the single best answer. The `optimize` field is simple; it just needs two things:

```python
class Optimize(BaseModel):
    """Defines the goal for an optimization problem."""

    type: str
    """The goal: "minimize" or "maximize"."""

    formula: str
    """The mathematical expression to optimize."""
```

Let's dive into an example!

## Example: The Treasure Hunter's Dilemma

Consider this classic knapsack puzzle:

> You are an adventurer who has discovered N precious treasures in an ancient ruin:
> *   Treasure 1 weighs 2kg and is worth 6 gold coins.
> *   Treasure 2 weighs 2kg and is worth 3 gold coins.
> *   Treasure 3 weighs 6kg and is worth 5 gold coins.
> *   Treasure 4 weighs 5kg and is worth 4 gold coins.
> *   Treasure 5 weighs 4kg and is worth 6 gold coins.
>
> Your backpack can carry a maximum of 10kg. You want to choose which treasures to take to maximize their total value, without exceeding your backpack's weight limit.
> What is the maximum value you can obtain?

Here’s how we can build a specification file to generate endless variations of this treasure hunt:

```yaml
# =================================================================
# Puzzle Variables: The stats for our treasures and backpack.
# =================================================================
vars:
  item_num: # The total number of treasures to discover.
    type: int
    domain: "[5, 12]"
  weight: # The weight of each treasure.
    # Generates a list of `item_num` random integers, each between 1 and 10.
    formula: generate_random_list(item_num, 'int', [1, 10])
  price: # The value of each treasure.
    formula: generate_random_list(item_num, 'int', [1, 10])
  bag_size: # The maximum weight the backpack can hold.
    type: int
    # We set the bag size to be a fraction of the total weight of all items.
    # This ensures the puzzle is challenging—you can't just take everything!
    domain: "[sum(weight) // 3, sum(weight) // 2]"
  items: # The unique IDs for each treasure.
    formula: generate_letters(item_num)

# =================================================================
# Symbols: The decision for each treasure - take it or leave it?
# =================================================================
symbols:
  # 'v' will be a dictionary of item IDs to boolean symbols.
  # e.g., {'A': Bool('A'), 'B': Bool('B'), ...}
  # A symbol being True means we take the item.
  v:
    source:
    - items
    type: bool

# =================================================================
# Conditions: The single, most important rule of our adventure.
# =================================================================
conditions:
  weight_constraint: # The total weight of items taken cannot exceed the bag's capacity.
    # Let's break down this formula:
    # For each item `i`, If its symbol `v[items[i]]` is True,
    # then we add its `weight[i]` to the sum. Otherwise, we add 0.
    # The final `Sum(...)` must be less than or equal to `bag_size`.
    formula: Sum([If(v[items[i]], weight[i], 0) for i in range(item_num)]) <= bag_size

# =================================================================
# Optimization: The main objective - get the most gold!
# =================================================================
optimize:
  type: maximize # We want to make the result as large as possible.
  # This formula is similar to the weight constraint, but with price.
  # It calculates the total value of all the items we decided to take.
  formula: Sum([If(v[items[i]], price[i], 0) for i in range(item_num)])

# =================================================================
# Queries: The question we ask the user.
# =================================================================
queries:
  q1:
    desc: "What is the maximum value you can obtain?"
    # For optimization problems, `_value` is a special variable
    # that holds the final optimized result (e.g., the max value).
    ans_formula: _value
    ans_text: str(_value)

# =================================================================
# Description: The final story template for the puzzle.
# =================================================================
desc: "You are an adventurer who has discovered {item_num} precious treasures in an ancient ruin: {' and '.join(['Treasure ' + str(i + 1) + ' weighs ' + str(w) + 'kg and is worth ' + str(p) + ' gold coins' for i, (w, p) in enumerate(zip(weight, price))])}. Your backpack can carry a maximum of {bag_size}kg. You want to choose which treasures to take to maximize their total value without exceeding the weight limit. {q1}"
```

## Sample Puzzle

After running the generator, you'll get a puzzle like this:

```json
{
  "problem": "You are an adventurer who has discovered 9 precious treasures in an ancient ruin: Treasure 1 weighs 9kg and is worth 2 gold coins and Treasure 2 weighs 1kg and is worth 5 gold coins and Treasure 3 weighs 1kg and is worth 4 gold coins and Treasure 4 weighs 2kg and is worth 6 gold coins and Treasure 5 weighs 9kg and is worth 9 gold coins and Treasure 6 weighs 4kg and is worth 5 gold coins and Treasure 7 weighs 7kg and is worth 8 gold coins and Treasure 8 weighs 4kg and is worth 2 gold coins and Treasure 9 weighs 1kg and is worth 5 gold coins. Your backpack can carry a maximum of 17kg. You want to choose which treasures to take to maximize their total value without exceeding the weight limit. What is the maximum value you can obtain?\n",
  "answer": "33",
  "parameters": {
    "cond_num": 1,
    "sym_num": 9,
    "sym_type": [
      "bool"
    ],
    "opt_solution": "[v_A1 = False, v_A2 = True, v_A3 = True, v_A4 = True, v_A5 = False, v_A6 = True, v_A7 = True, v_A8 = False, v_A9 = True]"
  },
  "config": {
    "item_num": 9,
    "weight": [9, 1, 1, 2, 9, 4, 7, 4, 1],
    "price": [2, 5, 4, 6, 9, 5, 8, 2, 5],
    "bag_size": 17,
    "items": ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"],
    "_query": {}
  }
}
```

Notice the new field in the `parameters` section: `"opt_solution"`. This not only tells you the *what* (the answer is "33") but also the *how*—it shows the exact combination of items (`True` means taken, `False` means left behind) that achieves this maximum value. It's the perfect way to verify your solution!

## Caution

**Avoid non-linear optimization:** Under the hood, PuzzleClone uses the powerful [Z3.Optimize](https://z3prover.github.io/api/html/ml/Z3.Optimize.html) module to solve these puzzles. For the `optimize` field to work, make sure the formulas in your `conditions` and the optimization `formula` are **linear**. This means you can use addition, subtraction, and multiplication by constants, but avoid things like multiplying two symbols together or using non-linear functions. Our knapsack example is perfectly linear, and it's a great template for many other optimization problems.

**About the uniqueness of the solution:** By default, the optimizer only ensures that the optimal value of the target function is accurate. However, it does not make sure that the value configurations of the symbols to satisfy the optimal result are unique. If you want to make sure a unique configuration exists, include `max_solution: 1` in the specification. This would make PuzzleClone automatically discard the puzzle if more than one optimal configuration exists.