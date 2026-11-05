# Data

No dataset is stored in this repository. They are large or public and can be rebuilt.

## Synthetic data

Generated with the authors' generator (`causica.data_generation.temporal_synthetic`) by `Code/scripts/gen_datasets.py`.
Grid: dimensions 5, 10 and 20, graph type ER or SF, with or without instantaneous effects, with or without history-dependent noise, seeds 0 to 4.
That gives 40 datasets per dimension. Each dataset has 4N instantaneous edges (when enabled) and 2N lagged edges, 50 series of 200 steps (50 burn-in steps).
A 5-node dataset already needs about 45 MB because of the stored interventions, so the 120 datasets are not part of the repository.
The paper reports 160 datasets (4 dimensions) and the authors' released generator writes 480. This run uses the 120 datasets of 5, 10 and 20 nodes from the paper's grid. See `Results/STATUS.md`, assumption 1.

## DREAM3 (in silico, size 100)

Source: http://gnw.sourceforge.net/resources/DREAM3%20in%20silico%20challenge.zip
Used: `Size100/DREAM3 data/InSilicoSize100-<Network>-trajectories.tsv` and the matching gold standard in `Size100/DREAM3 gold standards/`.
Five networks (E. coli 1 and 2, Yeast 1, 2 and 3). Each has 46 trajectories with 21 time points and 100 genes.
Preprocessing (`Code/scripts/prep_real_data.py`): drop the time column, number the series 0 to 45, split the series 80/20 into `train.csv` (37 series) and `val.csv` (9 series).
`test.csv` is a copy of `val.csv` (it is not used for the discovery metrics). The gold standard becomes a 100 x 100 matrix with `adj[i, j] = 1` for the edge i to j.
Edge counts after conversion: E. coli 1: 125, E. coli 2: 119, Yeast 1: 166, Yeast 2: 389, Yeast 3: 551. The diagonal is ignored in the evaluation.

## Netsim (Sim-3)

Source: https://github.com/sakhanna/SRU_for_GCI/tree/master/data/netsim (50 files `sim3_subject_<k>.npz`, each 15 nodes and 200 time steps).
Training: subjects 2 to 6. Validation: subjects 7 and 8. This follows the paper (Appendix G.4). The numbering of the files starts at 0 (assumption).
The ground truth `Gref` has 18 edges between different nodes and 15 self-connections. In the file, `Gref[i, j] = 1` means j causes i.
This was checked on the data: a pooled VAR(1) fit gives AUROC 0.974 for this reading and 0.861 for the opposite one. So `adj_matrix.npy` stores `Gref` transposed.
Self-connections are counted in the evaluation, as in the paper.

## Checksums of the downloaded files

See `checksums.txt` (SHA-256).
