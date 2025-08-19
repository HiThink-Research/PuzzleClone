# PuzzleClone

## What is PuzzleClone?

**PuzzleClone** is an open-source data synthesis framework and comprehensive dataset for logical reasoning problems. It features:

- 📊 **Expansive and Diverse Coverage:** Contains over **83,657** unique logical reasoning tasks procedurally generated from 86 seed questions. The dataset spans:
    * Various applications of Satisfiability Modulo Theories (SMT) and SMT-like puzzles,
    * Classic logical puzzles like Sudoku, the Knapsack problem, and linear optimization (LP).
    * Diverse mathematical problems of varying difficulties.
- ✅ **Guaranteed Verifiability:** Every problem is generated with a ground-truth solution and is verifiable by a symbolic SMT solver, ensuring correctness.
- 🎯 **Granular Control:** Offers fine-grained control over problem attributes like scale, structure, and difficulty through a set of adjustable parameters, enabling large-scale batch generation.
- ✨ **Flexible Adaptation:** Facilitates the easy customization of problem scenarios and translation into different languages or domains.
- 🚀 **State-of-the-Art Performance:** Achieves SOTA results among open-source datasets, outperforming the public dataset by 12.5 points on AMC2023 (from 52.5 to 65.0).

## Tutorials
Please visit [here](quickstart.md) to learn how to batch generate puzzles with PuzzleClone. 

## API document
Please visit [here](https://puzzleclone.github.io/PuzzleClone/api/index.html) for detailed information on the APIs.
