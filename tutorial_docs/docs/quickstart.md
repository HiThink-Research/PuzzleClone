Ready to become a puzzle-making wizard? This tutorial will guide you through the basics of PuzzleClone. We'll start with a simple example and incrementally build up to more powerful concepts and techniques. By the end, you'll be able to batch-produce your own unique logic puzzles!

## Step 1: Find Your Seed Puzzle

Every great creation starts with an idea. For us, that's a "seed puzzle" that will act as the blueprint for our generated puzzles. Let's start with a classic logic puzzle, which describes a common [Boolean Satisfiability Problem](https://en.wikipedia.org/wiki/Boolean_satisfiability_problem) (SAT):

> From a group of 7 graduates—J, K, L, M, N, P, and Q—exactly 4 will be selected for a graduation ceremony.
> The selection must satisfy the following conditions:

> *   Either J or K must be selected, but not both.

> *   Either N or P must be selected, but not both.

> *   Unless L is selected, N cannot be selected.

> *   Unless K is selected, Q cannot be selected.
>
> **Question 1:** Which of the following is a possible selection of people?
> *(Options listing groups of 4 graduates)*
>
> **Question 2:** The selected group must include:
> *(Options listing pairs like "L or M or both")*
>
> **Question 3:** Which two people cannot be selected at the same time?
> *(Options listing pairs like "J and N")*

Think of all the ways we could change this puzzle to make a new one. We could modify:

*   The total number of graduates and the number to be selected.
*   The names of the graduates.
*   The specific graduates mentioned in the rules.
*   The number of rules of each type (e.g., have more "either/or" rules).
*   The number and content of the questions and options.

With PuzzleClone, you can control all of these variations at once. How? By creating a **specification file**. Let's build one now!

## Step 2: Constructing a Specification File

At the heart of PuzzleClone is its specification file. This file uses a special language (a DSL, or Domain-Specific Language) that acts as a powerful and precise blueprint for your puzzles. Think of it as a recipe for generating puzzles.

For our graduate selection puzzle, our recipe needs these main ingredients:

*   `vars`: The basic parameters of our puzzle. This is where we define things that can change, like the number of students, their names, and any values derived from them.
*   `symbols`: The "unknowns" in our puzzle. We'll create a Boolean symbol for each student to represent whether they are selected or not.
*   `conditions`: The rules of the game. These are the logical constraints that the `symbols` must obey. We can have two types:
    *   *Static conditions*: Rules that are the same in every puzzle, like "exactly four students will be selected."
    *   *Dynamic conditions*: Rules that are randomly constructed. For example, the rule "`student1` cannot be selected unless `student2` is selected" can be generated a variable number of times, each time with different, randomly chosen students.
*   `queries`: The questions we want to ask. For multiple-choice questions, PuzzleClone lets you define how to generate both correct and incorrect options automatically.
*   `desc`: The final presentation. This is a text template that assembles all the pieces into a human-readable puzzle.

Let's create a file named `spec.yaml` and add the following content.

```yaml
# =================================================================
# Puzzle Variables: The core numbers and names for our puzzle.
# =================================================================
vars:
  p_num: # The total number of students.
    type: int
    domain: "[6, 12]" # We'll randomly pick a number between 6 and 12.
  select_num: # The number of students to be selected.
    type: int
    domain: "[p_num // 2 - 1, p_num // 2 + 1]" # A range based on p_num.
  names: # The students' names.
    # `generate_letters` is a built-in helper to create unique names.
    formula: generate_letters(p_num)
  name_desc: # A nicely formatted string of all student names.
    formula: "', '.join(names)"

# =================================================================
# Symbols: The logical entities that the puzzle will solve for.
# =================================================================
symbols:
  # 'events' will be a dictionary of student names to boolean symbols.
  # e.g., {'J': Bool('J'), 'K': Bool('K'), ...}
  events:
    source: # The keys for our dictionary come from the 'names' variable.
    - names
    type: Bool # Each symbol will be a Boolean (True/False).
    # This is the default description when a symbol is True.
    desc: "{_names} is selected for the ceremony"

# =================================================================
# Conditions: The rules and constraints of the puzzle.
# =================================================================
conditions:
  # --- Static Condition ---
  the_number_of_selections: # This rule is always present.
    # The sum of all 'events' symbols must equal 'select_num'.
    # This enforces that the correct number of students are selected.
    formula: Sum(events) == select_num
    desc: "{select_num} people will be selected for the graduation ceremony"

  # --- Dynamic Conditions ---
  # The following conditions will be generated a random number of times.
  s1_and_s2_have_one_selected: # Rule type 1: "Either A or B, but not both".
    domain: "[1, 3]" # Generate between 1 and 3 of these rules.
    source:
    - events # Parameters for this rule will be drawn from our 'events' symbols.
    amount:
    - '2' # Draw 2 symbols for each rule instance.
    # Now, we create the logical formula for this rule.
    # `_sym` is a special variable holding the drawn symbols.
    # `_sym[0][0]` is the first symbol, `_sym[0][1]` is the second.
    formula: Xor(_sym[0][0], _sym[0][1]) # Xor means "exclusive or".
    # `get_p` retrieves the original property (like the name) of a symbol.
    desc: "Either {get_p(_sym[0][0], 'names')} or {get_p(_sym[0][1], 'names')} is selected, but not both."

  s1_cannot_be_selected_unless_s2_is_selected: # Rule type 2: "A implies B".
    domain: "[1, 3]" # Generate between 1 and 3 of these rules.
    source:
    - events
    amount:
    - '2'
    # The formula `Implies(A, B)` is logically equivalent to "If A, then B".
    # This translates to "Unless B is true, A cannot be true".
    formula: Implies(_sym[0][1], _sym[0][0])
    desc: "Unless {get_p(_sym[0][0], 'names')} is selected, {get_p(_sym[0][1], 'names')} cannot be selected."

# =================================================================
# Queries: The questions to be asked, with auto-generated options.
# =================================================================
queries:
  # --- Question 1: Find a valid group ---
  q1:
    desc: "Which of the following is a possible selection of people?"
    opt_num: 5 # Generate 5 multiple-choice options.
    # To generate a candidate option, we'll draw a group of students.
    source:
    - events
    amount:
    - select_num # Draw 'select_num' students. The result is stored in `_opt`.
    # How do we know if an option is correct? We check it against the solutions.
    # `_model` is a special variable representing a valid solution found by the solver.
    # We check if every student in our option (`_opt`) is actually selected in the solution (`_model`).
    opt_formula: sum([get_value(_model, _opt[0][i]) for i in range(select_num)]) == select_num
    cond: any # An option is CORRECT if it's valid in ANY possible solution.
    # This defines how to display each option's text.
    opt_text: "{', '.join(get_p(_opt[0], 'names'))}"

  # --- Question 2: Find a necessary pair ---
  q2:
    desc: "The selected group of people must include:"
    opt_num: 4
    source:
    - events
    amount:
    - '2' # Candidate options are pairs of students.
    cond: all # An option is CORRECT if it holds true in ALL possible solutions.
    # The formula is true if at least one of the two students in the pair is selected.
    opt_formula: sum([get_value(_model, _opt[0][i]) for i in range(2)]) >= 1
    opt_text: "{get_p(_opt[0][0], 'names')} or {get_p(_opt[0][1], 'names')} or both."

  # --- Question 3: Find an impossible pair ---
  q3:
    desc: "Which two people cannot be selected at the same time?"
    opt_num: 5
    source:
    - events
    amount:
    - '2'
    cond: all # This must be true for ALL possible solutions.
    # The formula is true if the sum of the two selected students is 1 or 0 (i.e., not both are selected).
    opt_formula: sum([get_value(_model, _opt[0][i]) for i in range(2)]) <= 1
    opt_text: "{get_p(_opt[0][0], 'names')} and {get_p(_opt[0][1], 'names')}"

# =================================================================
# Description: The final text template for the puzzle.
# =================================================================
desc: >
    From a group of {p_num} graduates ({name_desc}), {the_number_of_selections}.
    The selection must satisfy the following conditions:\n
    {s1_and_s2_have_one_selected}\n{s1_cannot_be_selected_unless_s2_is_selected}\n{queries}\n"
```

## Step 3: Make a Sample Puzzle

With our recipe (`spec.yaml`) complete, let's generate a single sample puzzle to see how it looks. Run the following command in your terminal:

```bash
python translator.py -t spec.yaml -o sample.json -c
```

This tells PuzzleClone to use `spec.yaml` to create one puzzle and save it as `sample.json`. The output file will look something like this:

```json
{
  "problem": "From a group of 10 graduates (Laura, Corey, Austin, Micheal, Julie, Brad, Ryan, Gina, Cody, Lori), 6 people will be selected for the graduation ceremony. The selection must satisfy the following conditions:\nEither Brad or Micheal is selected, but not both. Either Austin or Micheal is selected, but not both.\nUnless Gina is selected, Julie cannot be selected. Unless Julie is selected, Austin cannot be selected. Unless Brad is selected, Laura cannot be selected.\n1. Which of the following is a possible selection of people?\nA. Micheal, Julie, Ryan, Gina, Cody, Lori\nB. Austin, Micheal, Julie, Ryan, Cody, Lori\nC. Laura, Corey, Micheal, Julie, Cody, Lori\nD. Laura, Austin, Micheal, Brad, Gina, Cody\nE. Laura, Corey, Austin, Micheal, Ryan, Gina\n\n2. The selected group of people must include:\nA. Brad or Lori or both.\nB. Laura or Julie or both.\nC. Julie or Gina or both.\nD. Corey or Cody or both.\n\n3. Which two people cannot be selected at the same time?\nA. Julie and Ryan\nB. Laura and Gina\nC. Julie and Lori\nD. Corey and Gina\nE. Laura and Micheal\n\n\n",
  "answer": "A====C====E",
  "parameters": {
    "cond_num": 6,
    "sym_num": 10,
    "sym_type": [
      "Bool"
    ]
  },
  "config": {
    "p_num": 10,
    "select_num": 6,
    "names": ["Laura", "Corey", "Austin", "Micheal", "Julie", "Brad", "Ryan", "Gina", "Cody", "Lori"],
    "name_desc": "Laura, Corey, Austin, Micheal, Julie, Brad, Ryan, Gina, Cody, Lori",
    "..."
  }
}
```

Looks great! Let's quickly break down the output:

*   `problem` and `answer`: The fully formed puzzle text and its corresponding solution. PuzzleClone uses `====` to separate answers for different questions.
*   `parameters`: Useful metadata for analysis, like the number of conditions (`cond_num`) and symbols (`sym_num`), which can help you gauge puzzle difficulty.
*   `config`: A snapshot of all the randomized variables (`p_num`, `names`, etc.) used to generate this specific puzzle. This is great for debugging or recreating a specific instance.

## Step 4: Batch Generation

Generating one puzzle is cool, but generating thousands is powerful. To create a large dataset of puzzles, use the `-d` flag for "dataset" and `-n` for the number of puzzles you want.

```bash
python translator.py -d spec.yaml -o batch_data.jsonl -n 1000
```

This command will generate **1000 unique puzzles** based on your `spec.yaml` blueprint and save them to the file `batch_data.jsonl`.

## Congratulations!

You've successfully learned the basic workflow of PuzzleClone! You took a seed idea, defined its logic in a specification file, and used it to generate both single samples and a large batch of new puzzles.

Now that you've mastered the fundamentals, you're ready to explore the more advanced features of PuzzleClone in the upcoming sections. Happy puzzle-making!