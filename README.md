# Semantic Hardness Conservation — Reproducibility Package

This repository accompanies **Semantic Hardness Conservation: An Operational Normal Form for Exact Reasoning After Compression**.

The software implements exact small-instance future-equivalence quotients, Semantic Lifetime Width diagnostics, GF(2) future-row rank, reverse decision boundaries, constant-image and same-image realizability diagnostics, representation routing, E/R/S/T convergence and ablation tables, cubic Tseitin contradictions, and theorem-bound calculators.

**Scope.** The package does not claim a polynomial-time algorithm for arbitrary 3-SAT and does not claim `P=NP`. Exhaustive routines are deliberately restricted to small finite instances and are separated from polynomial routines such as the SCC-based 2-SAT solver.

## Reproduce everything

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
pytest -q
python run_all.py
```

The final fixed-seed run produces 369 exact stage profiles across 45 controlled families, 10 table families, and 7 figure families. Generated artifacts are written under `results/`.

## CLI

```bash
semantic-hardness reproduce --out results
semantic-hardness profile --family tseitin --n 8 --seed 2026
semantic-hardness same-image --max-n 14
semantic-hardness bound --e 10 --q 5 --r 20 --p 4 --s 15 --u 30 --stages 10
```

## Interactive app

```bash
python app.py
```

The seven tabs expose exact quotient profiles, E/R/S/T spectra, reverse boundaries, representation routes, same-image separation, convergence/ablation diagnostics, and the theorem runtime-bound calculator.

## License

Apache-2.0. Copyright (C) 2026 Mohammad Amir Khusru Akhtar.

## Repository

https://github.com/Arithmetic-Power-Geometry/Semantic-Hardness-Conservation
