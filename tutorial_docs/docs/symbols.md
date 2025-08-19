# Symbols, Conditions, and Queries

In this section, we will dive into the detailed features within the symbols, conditions, and queries in PuzzleClone's specfications.

## Symbols

Think of symbols as the "unknowns" or the "moving parts" of your puzzle. They are the logical variables that the solver will work to figure out. PuzzleClone offers several powerful ways to create and define them.

### Mapping Variables to Symbols

At its simplest, you create symbols by mapping them to a list of names or items you defined in `vars`. We saw this in the Quick Start, where we mapped student names to Boolean symbols representing their selection status.

```yaml
symbols:
  # 'events' will be a dictionary of student names to boolean symbols.
  # e.g., {'J': Bool('J'), 'K': Bool('K'), ...}
  events:
    source: # The keys for our dictionary come from the 'names' variable.
    - names
    type: Bool # Each symbol will be a Boolean (True/False).
    # This is the default description when a symbol is True.
    desc: "{_names} is selected for the ceremony"
```

Under the hood, PuzzleClone treats `events` as a dictionary. You can access an individual symbol using its key, like `events["<student_name>"]`.

#### Multiple Sources for Complex Mappings

What if your puzzle involves matching students to different groups? For a rule like, "If Student A is in Group X, then Student B must be in Group Y," you need symbols for each `(student, group)` possibility. PuzzleClone handles this by accepting multiple sources.

```yaml
symbols:
  events:
    source:
    - names
    - groups
    type: Bool # Each symbol will be a Boolean (True/False).
    desc: "{_names} is assigned to group {_groups}"
```

PuzzleClone will create a symbol for every possible pair in the Cartesian Product of the sources. You can then access a specific symbol using a tuple as the key: `events[("<student_name>", "<group_name>")]`.

#### Attributes for Multi-Faceted Entities

Sometimes, an entity in your puzzle has several properties. A person might have a gender and an age; a car might have a color and a speed. The `attr` field lets you define these properties neatly.

```yaml
symbols:
  events:
    source:
    - names
    attr: # Each name will have a 'gender' and 'age' attribute.
    - gender
    - age
    type: # The type for each attribute, in the same order.
    - bool # True for male, False for female.
    - int
    desc: # A description for each attribute.
    - "{_names} is {'male' if _gender else 'female'}"
    - "{_names}'s age is {_age}"
```

This creates two symbols for each person. You can access them intuitively using the `.get()` method: `events["<student_name>"].get("gender")` and `events["<student_name>"].get("age")`.

#### From Dict to List: A Handy Shortcut

While symbols are structured like dictionaries, PuzzleClone offers shortcuts that let you treat them like lists. If a symbol set like `events` has only one source and one attribute, you can simply write `Sum(events)`, and PuzzleClone will automatically sum all the symbol values. If it has multiple attributes, you can get a list for a specific attribute using `events.get("<attr_name>")`.

### Creating Symbols from Other Symbols

This is where things get really interesting. PuzzleClone allows you to derive new symbols from symbols you've already defined. The simplest way is with a direct `formula`:

```yaml
symbols:
  events:
    ...
  # Creates a new symbol that is the sum of all symbols in 'events'.
  sum_events:
    formula: "Sum(events)"
```

But what about more complex scenarios where the derivation logic itself needs to be randomized?

#### Advanced Derivation: The Mystery Ore Puzzle

Consider this puzzle:
> During a geology class, a teacher presents an ore for identification.

> *   **Sroan says:** "It's not iron, and it's not copper."

> *   **Pasber says:** "It's not iron, but it is tin."

> *   **Ayu says:** "It's not tin, but it is iron."
>
> The teacher reveals: "Among you, one person made two correct statements, one person made two incorrect statements, and one person made one correct and one incorrect statement."
>
> Based on this, what is the ore?

> A. Copper

> B. Tin

> C. Iron

First, we define our base symbols: a Boolean for each ore type.

```yaml
symbols:
  stones_s:
    source:
    - stones # A var list like ['iron', 'copper', 'tin']
    type: Bool
    desc: "The ore is {_stones}"
```

The real challenge is representing the students' statements. Let's analyze them.

**Why are they symbols and not conditions?**
A condition is a fact that is always true. But here, we don't know if a student's statement is true or false—that's part of the puzzle! So, each statement's truthfulness is an *unknown* we need to solve for, making it a symbol.

**Why is each speech a "combination of two symbols"?**
The teacher's final clue evaluates each *part* of a student's statement separately ("one correct and one incorrect"). This means we can't just `And` the two clauses together. We need to treat each clause as its own sub-symbol.

To handle this, we can create a **multi-dimensional symbol**. Each student's speech will be a group of 2 symbols, where each symbol is a randomized logical expression.

```yaml
symbols:
  # ... stones_s from above ...
  speech_s:
    # We will draw from our 'stones_s' symbols and a boolean value.
    source:
    - stones_s
    - "[False, True]"
    # Create 'student_num' groups of these symbols (one for each student).
    domain: student_num
    # The key part: each group will have 2 dimensions (sub-symbols).
    dim: 2
    # The recipe for each sub-symbol: pick one ore `_sym[0]` and one boolean `_sym[1]`,
    # then form the expression `ore == boolean`.
    # e.g., stones_s['iron'] == False, which means "it's not iron".
    formula: _sym[0] == _sym[1]
    desc: "{students[_index]} says: \"It is {' ' if _sym[1] else 'not '}{get_p(_sym[0], 'stones')}\""
```

The result, `speech_s`, is a 2D list. You can access the symbol for the `j`-th clause of the `i`-th student's speech with `speech_s[i][j]`.

#### Derived Symbols with Multiple Templates: The Surgeon Puzzle

What if the statements in a puzzle don't all follow the same pattern?
> A patient needs surgery. There are four surgeons: A, B, C, and D.
> *   **Witness 1 says:** "C's success rate is lower than the other three."
> *   **Witness 2 says:** "C and D are better than A and B."
> *   **Witness 3 says:** "D is not the best."
> ...and so on.
> An old doctor says, "Of these six statements, only one is false."
> Who is the best surgeon?

Here, the statements have different logical structures. To handle this, PuzzleClone lets you define a list of `templates`. When generating a symbol, it will randomly pick one of these templates to use as its blueprint.

```yaml
symbols:
  # A boolean for each (doctor1, doctor2) pair, true if doctor1 is better than doctor2.
  is_better:
    source:
    - dnames # ['A', 'B', 'C', 'D']
    - dnames2 # another copy of ['A', 'B', 'C', 'D']
    type: Bool
  speeches_s:
    total: speech_num # The total number of speeches to generate.
    templates: # A list of possible statement structures.
    # Template 1: "X is worse than everyone else."
    - source:
      - dnames
      amount:
      - '1'
      formula: And([is_better[(p, _sym[0][0])] for p in dnames if p != _sym[0][0]])
      desc: "{snames[_index]} says: 'Dr. {_sym[0][0]}'s success rate is lower than the other {doctor_num - 1}.'"
    # Template 2: "X and Y are better than Z and W."
    - source:
      - dnames
      amount:
      - '4'
      formula: And(is_better[(_sym[0][0], _sym[0][2])], is_better[(_sym[0][1], _sym[0][2])],
        is_better[(_sym[0][0], _sym[0][3])], is_better[(_sym[0][1], _sym[0][3])])
      desc: "{snames[_index]} says: 'Drs. {_sym[0][0]} and {_sym[0][1]} are more skilled than {_sym[0][2]} and {_sym[0][3]}.'"
    # Template 3: "X is not the best."
    - source:
      - dnames
      formula: And([is_better[(p, _sym[0])] for p in dnames if p != _sym[0]])
      desc: "{snames[_index]} says: 'Dr. {_sym[0]} is not the best.'"
    # ... and so on for other templates
```

## Conditions

Think of `conditions` as the rulebook for your puzzle. They are logical assertions about the symbols that must be true for a solution to be valid. As covered in the [Quick Start](quickstart.md), they can be:

*   **Static Conditions**: Fixed rules that appear in every generated puzzle.
*   **Dynamic Conditions**: Rules that are randomly generated from a template, appearing a variable number of times.

**Note:** Just like derived symbols, dynamic conditions also support multi-template generation, giving you immense flexibility in creating varied rule sets.

## Queries

PuzzleClone supports two main types of questions: multiple-choice and open-ended (essay) questions. Every query has a `desc` field for its text. Here are the type-specific fields.

### Multiple-Choice Questions

*   `opt_num`: The number of options to generate (e.g., 5 for A-E).
*   `source`, `amount`: How to randomly select entities to form a candidate option.
*   `opt_formula`: The logical formula that an option must satisfy to be considered "correct".
*   `cond`: The condition for correctness.
    *   `'any'`: An option is correct if the `opt_formula` is true in **at least one** possible solution.
    *   `'all'`: An option is correct only if the `opt_formula` is true in **all** possible solutions.
*   `opt_text`: The text template for rendering an option. No need to add the prefix indices (e.g., "A.", "B.") as they will be automatically added.
*   `select_type`: Controls the question's goal.
    *   `true` (default): Asks the user to find the only **correct** choice.
    *   `false`: Asks the user to find the only **incorrect** choice.

### Essay Questions

*   `ans_formula`: The formula used to calculate the correct answer from the solution (e.g., `_value` in optimization problems).
*   `ans_text`: A template for how the answer should be rendered as a string.
*   `ans_assertion`: A final check. This is an assertion that the calculated answer must satisfy. If it fails, PuzzleClone will discard the current puzzle and try generating a new one from scratch. This is great for ensuring the final answer meets certain criteria (e.g., is a positive number).