# %% [markdown]
# # <NN-name>
# **Overview:** one sentence describing what we are exploring, building, or testing (from spec).
# **Spec:** specs/<NN-name>.md
# **Baseline (optional, for modeling experiments):** metric and number to beat.

# %%
# Uncomment if running this notebook standalone outside the project venv:
# # %pip install -q pandas numpy pyarrow matplotlib

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# %% [markdown]
# ## Config
# Paths and settings. Change values here only.

# %%
NAME = "NN-name"  # same as the spec file name, specs/NN-name.md
ROOT = next(
    (p for p in [Path.cwd(), *Path.cwd().parents] if (p / "pyproject.toml").exists()),
    Path.cwd(),
)
DATA = ROOT / "data"
MODELS = ROOT / "models"
FIGURES = ROOT / "docs" / "figures"
REFRESH_DATA = False  # set True when ## Data & Inputs changes in an iteration
SEED = 42
# Parameters, only if the spec lists some. Example:
# SAMPLE_FRAC = 1.0
FIGURES.mkdir(parents=True, exist_ok=True)
# MODELS.mkdir(parents=True, exist_ok=True)  # always use MODELS / ..., never "models/..."
np.random.seed(SEED)

# %% [markdown]
# ## 1. Get data
# Load data and keep a local cache in DATA so reruns do not re-fetch.

# %%
path = DATA / f"{NAME}.parquet"
if path.exists() and not REFRESH_DATA:
    df = pd.read_parquet(path)
else:
    # Query source data (e.g. SQL, BigQuery/Spark, or load raw file)
    SQL = """
    SELECT *
    FROM `project.dataset.table`
    """
    # df = spark.sql(SQL).toPandas()
    DATA.mkdir(exist_ok=True)
    df.to_parquet(path)
print(df.shape)

# %% [markdown]
# ## 2. Core Analysis or Baseline
# Explain what this step computes or establishes and why.

# %%
# analysis or baseline code here
results = {"step_1": 0.0}

# %% [markdown]
# ## 3. Next Step (as needed by the spec)
# Explain what this step explores, refines, or tests next.

# %%
# next-step code here

# %% [markdown]
# ## Summary
# Key findings table or comparison chart saved to FIGURES.

# %%
summary = pd.Series(results, name="metric").to_frame()
print(summary.round(4))

fig, ax = plt.subplots()
summary["metric"].plot.bar(ax=ax)
fig.savefig(FIGURES / f"{NAME}_summary.png", dpi=150, bbox_inches="tight")
