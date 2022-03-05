"""Script generating data for the analysis."""
from typing import Any, Dict, Callable
from pathlib import Path
from time import time
import numpy as np
import pandas as pd
import igraph as ig
import joblib
from tqdm import tqdm
from pathcensus import PathCensus
from pathcensus.nullmodels import UBCM
from pathcensus.utils import set_seed
from src.utils import list_graphs, load_graph


# Functions -------------------------------------------------------------------

def get_metadata(graph: ig.Graph) -> Dict[str, Any]:
    """Get graph metadata dictionary."""
    P = PathCensus(graph)
    D = P.degree
    A = graph.get_adjacency_sparse()
    N = (A@A).multiply(A)

    i ,j = A.nonzero()
    De   = np.column_stack([D[i], D[j]]) - 1

    N = np.array(N[i, j]).squeeze()
    S = De - N[:, None]

    return dict(
        label=graph["label"],
        n_nodes=graph.vcount(),
        n_edges=graph.ecount(),
        density=graph.density(),
        dmin=D.min(),
        dmax=D.max(),
        dbar=D.mean(),
        dcv=D.std() / D.mean(),
        clust=P.similarity("global"),
        star_max=S.max(),
        star_mean=S.mean(),
        star_minmax=S.min(axis=1).max(),
        star_minmean=S.min(axis=1).mean()
    )

def measure_time(func: Callable, *args: Any, **kwds: Any):
    """Measure execution time of a function."""
    start = time()
    func(*args, **kwds)
    return time() - start

# Prepare data ----------------------------------------------------------------

DSET = "proteins"
HERE = Path(__file__).parent
DATA = HERE/"data"
DATA.mkdir(parents=True, exist_ok=True)

# Number of repetitions
NREP = 5

# Seed for the random number generator
# used for sampling from the null model
set_seed(303)

rawdata = []

kwds = dict(parallel=False)

for network in tqdm(list_graphs(DSET)):
    graph = load_graph(DSET, network, preprocess=True)
    meta  = get_metadata(graph)

    # Measure runtime on the original network
    times = []
    for _ in range(NREP):
        elapsed = measure_time(PathCensus, graph, **kwds)
        times.append(elapsed)

    meta["times_original"] = times

    # Measure runtime on the randomized network
    model = UBCM(graph).fit()
    times = []
    rand  = model.sample_one()
    for _ in range(NREP):
        elapsed = measure_time(PathCensus, rand, **kwds)
        times.append(elapsed)
    meta["times_randomized"] = times

    rawdata.append(meta)

# Prepare data frame ----------------------------------------------------------

times = pd.DataFrame(rawdata)

# Save data -------------------------------------------------------------------

joblib.dump(times, DATA/"times.pkl.gz", compress=True)
