# Validation report

23 of 23 checks passed.

| Check | What is compared | Measured | Criterion | Result |
|---|---|---|---|---|
| V1a partial correlation formula | P_ij = -Theta_ij / sqrt(Theta_ii Theta_jj) against the partial correlation computed from the covariance (Schur complement), all 300 pairs | max error 1.11e-16 | below 1e-9 | pass |
| V1b zero in Theta means conditional independence | partial correlation of every pair with Theta_ij = 0, computed independently from the covariance | max |partial correlation| 1.91e-17 | below 1e-9 | pass |
| V1c partial correlation in samples | formula against correlation of regression residuals on 300000 samples (60 pairs) | max error 0.0048 | below 0.01 (sampling noise) | pass |
| V2a Theta update solves the stationarity equation | gradient of the relaxed objective, -Theta^-1 + S + lambda (Theta - Z), at the closed form Theta (20 random cases) | max gradient norm 2.27e-13 | below 1e-8 | pass |
| V2b Theta update is positive definite | smallest eigenvalue of Theta over 20 random cases | 0.239 | above 0 | pass |
| V2c Theta update is a minimum | objective after a small random move minus objective at Theta, worst case | 0.00e+00 | never negative | pass |
| V3a matrix square root forward | eigendecomposition square root against scipy.linalg.sqrtm | max error 1.03e-14 | below 1e-10 | pass |
| V3b matrix square root backward | hand written gradient against finite differences (torch gradcheck) | gradcheck passed | passes | pass |
| V4a AM never increases its objective | relaxed objective after every AM iteration (1500 iterations, lambda 0.5, 2, 8). Each step is an exact minimization over one block, so it cannot go up | largest single-step increase 2.7e-15 | below 1e-10 | pass |
| V4b AM fixed point is the true minimizer | Theta from AM after 3000 iterations against the minimizer of the same objective found by an independent optimizer (L-BFGS) | relative difference 1.0e-08 | below 1e-6 | pass |
| V4c speed of AM with fixed settings (reported, no threshold) | relative gap of the AM objective to its final value on a D = 25 problem at the scale used in the experiments (rho 0.01, lambda 5) | after 15, 100, 1000, 5000 iterations: 6.7e-01, 3.7e-01, 9.6e-02, 1.3e-02 | reported only | pass |
| V5a every Theta step is positive definite | smallest eigenvalue of Theta_k over the 15 unrolled steps | min over steps 4.049 | above 0 | pass |
| V5b output is symmetric | max |Z - Z^T| | 2.78e-16 | below 1e-12 | pass |
| V5c parameter count does not depend on D | learnable parameters of the network, built for D = 10, 25, 100 | 42, 42, 42 | all equal | pass |
| V5d training reduces the loss | training loss in the first and the last epoch of the selected fold | -33.45 to -54.39 | last below first | pass |
| V6a conditional mean given all other variables | -Theta_ij / Theta_ii against regression coefficients from 400000 samples | max coefficient error 0.0027 | below 0.01 | pass |
| V6b conditional variance given all other variables | 1 / Theta_ii against the residual variance of that regression | 0.3505 against 0.3505 | relative error below 1% | pass |
| V6c conditional given a subset of variables | mean and covariance of X_0, X_1 given X_2..X_5, with the other variables integrated out, against regression on samples | max error 0.0013 | below 0.01 | pass |
| V6d marginal | Sigma[0:3, 0:3] against the sample covariance of X_0..X_2 | max error 0.0014 | below 0.01 | pass |
| V6e factorization into node and edge factors | sum of node and edge log factors minus the exact log density, for 50 random points (must be one constant) | spread 4.97e-14 | below 1e-9 | pass |
| V6f local Markov property | prediction of a variable from its neighbours only against prediction from all other variables (200 samples, 25 variables) | max difference 3.33e-16 | below 1e-9 | pass |
| V7a moralization | collider adds an edge between the parents, chain does not, for both the DAG and the CPDAG converters | True, True, True, True | all True | pass |
| V7b metrics on a hand worked example | SHD, precision, F1 and perfect-ranking AUC and AUPR against values worked out by hand | 2 TP, 1 FP, 1 FN, SHD 2; AUC 1.0 | equal to hand values | pass |

## Inference query time

|   D |   predict one variable (microseconds) |   conditional of 2 given 10 (microseconds) |   all partial correlations (milliseconds) |
|----:|--------------------------------------:|-------------------------------------------:|------------------------------------------:|
|  25 |                                 12.57 |                                      67.75 |                                      0.13 |
| 100 |                                 23.27 |                                      50.88 |                                      0.09 |
| 400 |                                 56.08 |                                      65.07 |                                      1.23 |
