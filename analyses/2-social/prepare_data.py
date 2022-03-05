"""Script for generating data for the analysis."""
from typing import Dict
from pathlib import Path
import numpy as np
import pandas as pd
import igraph as ig
import joblib
from tqdm import tqdm
from pathcensus import PathCensus
from pathcensus.nullmodels import UBCM
from pathcensus.inference import Inference
from pathcensus.utils import set_seed
from src.utils import list_graphs, load_graph, preprocess_graph


# Graph statistics function ---------------------------------------------------

def statistics(graph: ig.Graph) -> pd.DataFrame:
    """Function for calculating graph statistics."""
    paths = PathCensus(graph)
    coefs = paths.coefs("nodes")
    df = pd.DataFrame({
        "sim_g":   paths.similarity("global"),
        "sim":     coefs["sim"].mean(),
        "sim_e":   paths.similarity("edges").mean(),
        "comp_g":  paths.complementarity("global"),
        "comp":    coefs["comp"].mean(),
        "comp_e":  paths.complementarity("edges").mean(),
        "coefs":   [coefs]
    }, index=[0])
    return df

def get_metadata(graph: ig.Graph) -> Dict:
    """Get graph metadata dictionary."""
    name = graph["name"]
    return {
        "dataset":    name.split()[0],
        "name":       name,
        "domain":     graph["domain"],
        "relation":   graph["relation"],
        "desc":       graph["desc"],
        "label":      graph["label"],
        "idx":        graph["idx"] if "idx" in graph.attributes() else 0
    }


# Prepare data ----------------------------------------------------------------

HERE = Path(__file__).parent
DATA = HERE/"data"
DATA.mkdir(parents=True, exist_ok=True)

# Number of null model samples
N_SAMPLES = 200

# Seed for the random number generator
# used for sampling from the null model
set_seed(1019)

rawdata = []

for network in tqdm(list_graphs("social")):
    graph   = load_graph("social", network, preprocess=False)
    n_total = graph.vcount()
    graph   = preprocess_graph(graph)
    n_giant = graph.vcount()
    degseq  = np.array(graph.degree())
    name    = graph["name"]

    net = pd.DataFrame({
        **get_metadata(graph),
        "graph":      [graph],
        "n_nodes":    n_giant,
        "frac_total": n_giant / n_total,
        "density":    graph.density(),
        "dbar":       degseq.mean(),
        "dcv":        degseq.std() / degseq.mean(),
        "dmax":       degseq.max()
    }, index=[0])
    # Structural coefficients and null distributions
    model = UBCM(graph)
    model.fit()
    model.validate()
    infer = Inference(graph, model, statistics)
    data, null = infer.init_comparison(n=N_SAMPLES)

    # Estimate fractions of significant nodes
    odf = pd.concat(data.pop("coefs").tolist())
    ndf = pd.concat(null.pop("coefs").tolist())

    infer.add_stats_index(odf)
    infer.add_stats_index(ndf)

    odf = pd.concat([odf], keys=[0], names=["_"])
    ndf = pd.concat([ndf], keys=[0], names=["_"])

    alpha = 0.01
    pvals = infer.estimate_pvalues(odf, ndf, alpha=alpha, adjust=True)
    sig   = (pvals <= alpha)[["sim", "comp"]]

    sig["both"] = sig.all(axis=1)
    sig = sig.mean().to_frame().T

    # Compute calibrated coefficients
    cdata = np.log(data / null).reset_index(drop=True) \
        .replace([np.inf, -np.inf], np.nan) \
        .dropna() \
        .mean() \
        .to_frame().T

    net["rawdata"]     = [data]
    net["calibrated"]  = [cdata]
    net["significant"] = [sig]

    rawdata.append(net)


# Prepare data frames ---------------------------------------------------------

villages = pd.concat(rawdata, axis=0, ignore_index=True)

# Save data -------------------------------------------------------------------

joblib.dump(villages, DATA/"social.pkl.gz", compress=True)
