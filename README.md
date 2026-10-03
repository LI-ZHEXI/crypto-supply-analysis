Cryptocurrency Supply and Macroeconomic Analysis

This project analyzes the weekly relationship between USDT (EVM-only) stablecoin supply and the U.S. 3-month Treasury bill rate (3M T-bill), aiming to examine, from a macroeconomic perspective, the behavior of stablecoins as on-chain "shadow cash".

· Project Overview

This project analyzes the weekly relationship between USDT (EVM-only) stablecoin supply and the U.S. 3-month Treasury bill rate (3M T-bill),

aiming to examine, from a macroeconomic perspective, the behavior of stablecoins as on-chain "shadow cash".

· Data Sources

- USDT supply: DeFiLlama (EVM-compatible chains)
- On-chain activity indicators (supplementary): Dune Analytics (ERC-20 Transfer Events)
- Macroeconomic interest rate data: FRED API (U.S. 3-Month Treasury Bill)

· Methodology

- Unify the time frequency to weekly
- Take the logarithm of USDT supply to improve robustness and economic interpretability
- Use OLS regression (Newey–West / HAC robust standard errors) for lightweight economic modeling
- Combine descriptive statistics and visualization to interpret the economic mechanisms

· Project Purpose

This project is part of an Economic Insight course assignment,

and focuses on demonstrating a data-driven approach to economic analysis rather than complex engineering implementation.

· Project Structure

crypto-supply-analysis/
├── data_raw/              # Raw data folder
├── data_processed/        # Processed data folder
├── scripts/               # Python scripts folder
├── figures/               # Charts and visualization output folder
├── .gitignore            # Git ignore file
├── requirements.txt      # Python dependency list
└── README.md            # Project documentation
...

`MIT License
