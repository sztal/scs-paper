"""Script for generating data for the analysis."""
from typing import Any, Dict
from pathlib import Path
import numpy as np
import pandas as pd
import igraph as ig
import joblib
from tqdm.auto import tqdm
from pathcensus import PathCensus
from pathcensus.nullmodels import UBCM
from pathcensus.inference import Inference
from pathcensus.utils import set_seed
from src.utils import load_graph, list_graphs


# Main functions --------------------------------------------------------------

def make_data(
    graph: ig.Graph,
    n: int = 10,
    **kwds: Any
) -> Dict[str, pd.DataFrame]:
    """Make data frame with structural coefficients and node
    degrees for the original network and ``n`` draws from the
    corresponding configuration model (UBCM).

    Parameters
    ----------
    graph
        Observed graph.
    name
        Name of the graph.
    n
        Number of null model samples.
    **kwds
        Passed to :py:class:`pathcensus.PathCensus`.
    """
    def statistics(graph):
        df = PathCensus(graph, **kwds).coefs("nodes")
        return df

    # Extract graph metadata
    def insert_metadata(df, graph):
        df.insert(0, "density", graph.density())
        df.insert(0, "n_nodes", graph.vcount())
        df.insert(0, "desc", graph["desc"])
        df.insert(0, "relation", graph["relation"])
        df.insert(0, "domain", graph["domain"])
        df.insert(0, "label", graph["label"])
        df.insert(0, "name", graph["name"])
        return df

    model = UBCM(graph)
    model.fit()
    model.validate()

    infer      = Inference(graph, model, statistics)
    null_kws   = dict(progress=True)
    data, null = infer.init_comparison(n, sample_index=True, null_kws=null_kws)
    levels     = infer.get_levels(data)

    # Calibrated node-wise coefficients
    def subsample(df, max_n=1000):
        n = max_n if (nrow := len(df)) > max_n else nrow
        return df.sample(n, replace=False)

    cnull = null.groupby(level=levels.stats) \
        .apply(subsample) \
        .reset_index(level=0, drop=True)
    cdata = np.log(data / cnull) \
        .replace([np.inf, -np.inf], np.nan) \
        .mean() \
        .to_frame().T \
        .pipe(insert_metadata, graph=graph)

    # Coverage report for sufficient statistics
    report = null.groupby(level=levels.stats).size()

    # Estimate fractions of nodes with significantly high values
    P     = PathCensus(graph)
    alpha = 0.01
    pvals = infer.estimate_pvalues(data, null, adjust=True, alpha=alpha)
    sig   = (pvals <= alpha).mean() \
        .to_frame().T[["sim", "comp"]] \
        .rename(columns={"sim": "sim_p", "comp": "comp_p"})

    sig.insert(0, "comp", P.complementarity("global"))
    sig.insert(0, "sim", P.similarity("global"))
    sig.insert(0, "density", graph.density())
    sig.insert(0, "n_nodes", graph.vcount())
    insert_metadata(sig, graph)

    # Prepare data for degree correlations
    null = null.reset_index(["di", "_sample"]).reset_index(drop=True)
    data = data.reset_index("di").reset_index(drop=True)
    data.insert(1, "_sample", -1)

    data = data[data["di"] > 0]
    null = null[null["di"] > 0]

    for df, which in [(data, "observed"), (null, "randomized")]:
        df.insert(1, "dbin", 2**np.log2(df["di"]).astype(int))
        insert_metadata(df, graph)
        df.insert(1, "which", which)

    keys = data.loc[:, "name":"desc"].columns.tolist()
    data = pd.concat([data, null], axis=0) \
        .groupby([*keys, "dbin", "_sample"], dropna=False) \
        .mean() \
        .reset_index() \
        .drop(columns="_sample")

    return dict(data=data, cdata=cdata, sig=sig, report=report)

# -----------------------------------------------------------------------------

HERE = Path(__file__).parent
DATA = HERE/"data"
DATA.mkdir(parents=True, exist_ok=True)

dataset = "domains"
names   = list_graphs(dataset)

NETWORKS = {
    name: load_graph(dataset, name, preprocess=True)
    for name in names
}

# Set seeds of random number generators
set_seed(303)

N    = 100
data = {}
pbar = tqdm(NETWORKS.items())

for name, graph in pbar:
    pbar.set_description(f"{name}")
    n = N if graph.vcount() > 1000 else N*2
    data[name] = make_data(graph, n=n)

joblib.dump(data, filename=DATA/"domains.pkl.gz", compress=True)
