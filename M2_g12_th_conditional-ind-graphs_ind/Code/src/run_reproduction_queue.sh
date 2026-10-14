#!/bin/bash
R=../../Results/reproduction
python reproduce_table1.py --out $R/table1_author_generator/table1_raw.csv --workers 2 --graphs 20 --sizes 10 25 50 \
  --epochs 250 --generator author --matrix_dir $R/table1_author_generator/matrices \
  --progress $R/table1_author_generator/progress.json --tag "A: Table 1, 250 epochs"
