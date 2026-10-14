# Reproduction of Table 1 of the uGLAD paper

Graphs per M: {10: 20, 25: 20, 50: 20}. D = 25, edge probability 0.1, edge values U(-1, 1). uGLAD is the authors' public code in CV mode (250 epochs, learning rate 0.002, 3 folds). SGLCV is scikit-learn GraphicalLassoCV with default settings.

## Paper against my run

| metric   | method   |   M |   paper mean |   paper std |   mine mean |   mine std |   graphs |   difference (mine - paper) |
|:---------|:---------|----:|-------------:|------------:|------------:|-----------:|---------:|----------------------------:|
| AUPR     | SGLCV    |  10 |        0.112 |       0.013 |       0.123 |      0.05  |       20 |                       0.011 |
| AUPR     | SGLCV    |  25 |        0.132 |       0.012 |       0.153 |      0.048 |       20 |                       0.021 |
| AUPR     | SGLCV    |  50 |        0.219 |       0.085 |       0.24  |      0.07  |       20 |                       0.021 |
| AUPR     | uGLAD    |  10 |        0.159 |       0.029 |       0.119 |      0.031 |       20 |                      -0.04  |
| AUPR     | uGLAD    |  25 |        0.174 |       0.018 |       0.122 |      0.03  |       20 |                      -0.052 |
| AUPR     | uGLAD    |  50 |        0.223 |       0.062 |       0.147 |      0.075 |       20 |                      -0.076 |
| AUC      | SGLCV    |  10 |        0.505 |       0.007 |       0.518 |      0.041 |       20 |                       0.013 |
| AUC      | SGLCV    |  25 |        0.532 |       0.031 |       0.54  |      0.04  |       20 |                       0.008 |
| AUC      | SGLCV    |  50 |        0.617 |       0.083 |       0.604 |      0.054 |       20 |                      -0.013 |
| AUC      | uGLAD    |  10 |        0.572 |       0.027 |       0.518 |      0.05  |       20 |                      -0.054 |
| AUC      | uGLAD    |  25 |        0.595 |       0.044 |       0.52  |      0.035 |       20 |                      -0.075 |
| AUC      | uGLAD    |  50 |        0.651 |       0.021 |       0.544 |      0.074 |       20 |                      -0.107 |

## Paired comparison on the same datasets

| metric   |   M |   graphs |   mean (uGLAD - SGLCV) |   std |   uGLAD higher on |   ties |   paired t statistic |
|:---------|----:|---------:|-----------------------:|------:|------------------:|-------:|---------------------:|
| AUPR     |  10 |       20 |                 -0.004 | 0.036 |                 7 |      2 |                -0.54 |
| AUPR     |  25 |       20 |                 -0.031 | 0.042 |                 2 |      2 |                -3.3  |
| AUPR     |  50 |       20 |                 -0.093 | 0.084 |                 1 |      0 |                -4.94 |
| AUC      |  10 |       20 |                 -0     | 0.047 |                 8 |      0 |                -0.01 |
| AUC      |  25 |       20 |                 -0.02  | 0.037 |                 7 |      1 |                -2.47 |
| AUC      |  50 |       20 |                 -0.06  | 0.079 |                 4 |      0 |                -3.42 |

## Predicted edges, empty graphs and run time

| method   |   M |   mean predicted edges |   empty graphs |   median seconds |
|:---------|----:|-----------------------:|---------------:|-----------------:|
| SGLCV    |  10 |                   30   |              3 |              1.1 |
| uGLAD    |  10 |                  130   |              0 |             63.4 |
| SGLCV    |  25 |                   17   |              2 |              1.1 |
| uGLAD    |  25 |                   15.9 |             11 |             61.1 |
| SGLCV    |  50 |                   24.2 |              0 |              0.7 |
| uGLAD    |  50 |                   25.3 |             12 |             63.3 |
