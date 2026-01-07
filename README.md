# PuzzleClone

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/puzzleclone/PuzzleClone?style=social)](https://github.com/puzzleclone/PuzzleClone/stargazers)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=yellow)

<html>
    <h3 align="center">
      An open-source data generation framework for batch construction of verifiable, controllable, and diverse puzzles.
    </h3>
    <h3 align="center">
      Important Links:
      <a href="https://puzzleclone.github.io/PuzzleClone/api/index.html">API Docs</a>, 
      <a href="https://puzzleclone.github.io/PuzzleClone/tutorial/">Tutorials</a>,
      <a href="https://github.com/puzzleClone/PuzzleCloneData/">Benchmark</a>,
      <a href="https://github.com/puzzleclone/PolyhedronEvaluator">Evaluation Toolkit</a>
    </h3>
</html>


## 📋 Overview

**PuzzleClone** is a data synthesis framework and comprehensive dataset for logical reasoning problems. It features:
- ✅ **Guaranteed Verifiability:** Every problem is generated with a ground-truth solution and is verifiable by symbolic  solvers, ensuring correctness.
- 🎯 **Granular Control:** Offers fine-grained control over problem attributes like scale, structure, and difficulty through a set of adjustable parameters, enabling large-scale batch generation.
- ✨ **Flexible Adaptation:** Facilitates the easy customization of problem scenarios and translation into different languages or domains.
- 📊 **Expansive and Diverse Coverage:** Based on PuzzleClone, we have curated a [benchmark](https://github.com/puzzleClone/PuzzleCloneData/) including 83,657 unique logical reasoning puzzles procedurally generated from 86 seed questions. The dataset spans:
  - Various applications of Satisfiability Modulo Theories (SMT) and SMT-like puzzles,
  - Classic logical puzzles like Sudoku, the Knapsack problem, and linear optimization (LP).
  - Diverse mathematical problems of varying difficulties.
- 🚀 **State-of-the-Art Performance:** Achieves SOTA results among open-source datasets, outperforming the public dataset by 18.4 points on SATBench (from 51.4 to 70.0).

## 🚀 Quick Start
```
git clone https://github.com/puzzleclone/PuzzleClone.git
cd PuzzleClone
pip install -r requirements.txt
```

Here are a few common use cases.

### Generate a single test case for debugging
This runs the translator in test mode (`-t`), generating a sample question based on the specification file.
```
python translator.py -t path/to/spec.yaml
```

### Generate a full dataset for production
This runs the translator in production mode (`-d`) to generate a large number of problems and saves them to a specified output file (`-o`).
```
python translator.py -d path/to/spec.yaml -o data.jsonl
```

### Apply a new template to existing data
This uses the `-g` flag to load existing problem data and applies a new problem description or template (`new_spec.yaml`) to it.
```
python translator.py -d path/to/new_spec.yaml -g old_data.jsonl -o new_data.jsonl
```

### Data transformation
A handful of [scripts](https://github.com/puzzleclone/PuzzleClone/tree/main/data_processing_scripts) are provided to transform the data generated above to the standard formats for a benchmark. Please refer to the scripts and documentation in the `data_processing_scripts/` directory.

### Evaluation

See our evaluation toolkit [PolyhedronEvaluator](https://github.com/puzzleclone/PolyhedronEvaluator).

## ⚖️ License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
