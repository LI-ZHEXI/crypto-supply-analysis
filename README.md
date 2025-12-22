加密货币供应量与宏观经济分析

本项目用于分析 USDT（EVM-only）稳定币供应量 与 美国 3 个月期国债利率（3M T-bill） 之间的周频关系，旨在从宏观经济视角探讨稳定币作为"链上影子现金（shadow cash）"的行为特征。

· 项目概述

本项目用于分析 USDT（EVM-only）稳定币供应量 与 美国 3 个月期国债利率（3M T-bill） 之间的周频关系，

旨在从宏观经济视角探讨稳定币作为"链上影子现金（shadow cash）"的行为特征。

· 数据来源

- USDT 供应量：DeFiLlama（EVM-compatible chains）
- 链上活动指标（辅助）：Dune Analytics（ERC-20 Transfer Events）
- 宏观利率数据：FRED API（U.S. 3-Month Treasury Bill）

· 研究方法

- 时间频率统一为 周频（weekly）
- 对 USDT 供应量取对数以提高稳健性与经济解释性
- 使用 OLS 回归（Newey–West / HAC 稳健标准误） 进行轻量经济建模
- 结合描述性统计与可视化进行经济机制解释

· 项目目的

该项目为 Economic Insight 课程作业的一部分，

重点展示数据驱动的经济分析思路，而非复杂的工程实现。

· 项目结构

crypto-supply-analysis/
├── data_raw/              # 原始数据文件夹
├── data_processed/        # 处理后的数据文件夹
├── scripts/               # Python 脚本文件夹
├── figures/               # 图表和可视化输出文件夹
├── .gitignore            # Git 忽略文件
├── requirements.txt      # Python 依赖列表
└── README.md            # 项目说明文档
...

`MIT License
