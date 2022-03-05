"""Script for generating data for the analysis."""
from typing import Dict
import ast
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
from src.utils import list_graphs, load_graph


# Graph statistics function ---------------------------------------------------

def statistics(graph: ig.Graph) -> pd.DataFrame:
    """Function for calculating graph statistics."""
    paths = PathCensus(graph)
    coefs = paths.coefs("nodes")
    return pd.DataFrame({
        "sim_g":   paths.similarity("global"),
        "sim":     coefs["sim"].mean(),
        "sim_e":   paths.similarity("edges").mean(),
        "comp_g":  paths.complementarity("global"),
        "comp":    coefs["comp"].mean(),
        "comp_e":  paths.complementarity("edges").mean(),
        "coefs":   [coefs]
    }, index=[0])

def get_metadata(graph: ig.Graph) -> Dict:
    """Get graph metadata dictionary."""
    degseq   = np.array(graph.degree())
    taxonomy = ast.literal_eval(graph["taxonomy"])
    bio1     = taxonomy[1]
    bio2     = taxonomy[2]
    bio3     = taxonomy[3]

    if bio3 == "Metazoa":
        bio = "Animal"
    elif bio3 == "Fungi":
        bio = bio3
    elif bio2 == "Viridiplantae":
        bio = bio2
    else:
        bio = bio1

    return {
        "dataset":     "tree-of-life",
        "domain":      graph["domain"],
        "relation":    graph["relation"],
        "label":       graph["label"],
        "name":        graph["name"],
        "long_name":   graph["long_name"],
        "taxonomy":    [taxonomy],
        "taxonomy_l2": graph["taxonomy_level2"],
        "biodomain":   bio,
        "evo_length":  len(taxonomy),
        "evo_time":    np.float64(graph["evo_time"]),
        "pub_count":   int(graph["pub_count"]),
        "n_nodes":     graph.vcount(),
        "density":     graph.vcount(),
        "dbar":        degseq.mean(),
        "dcv":         degseq.std() / degseq.mean(),
        "dmin":        degseq.min(),
        "dmax":        degseq.max()
    }

# Prepare data ----------------------------------------------------------------

HERE = Path(__file__).parent
DATA = HERE/"data"
DATA.mkdir(parents=True, exist_ok=True)

# Number of null model samples
N_SAMPLES = 100

# Seed for the random number generator
# used for sampling from the null model
set_seed(44)

rawdata    = []
nulltrend  = []
calibrated = []
signif_01  = []
signif_05  = []
signif_10  = []

pbar = tqdm(list_graphs("proteins"))

for network in pbar:
    pbar.set_description(network.split("__")[-1])
    graph = load_graph("proteins", network, preprocess=True)
    meta  = get_metadata(graph)

    model = UBCM(graph)
    model.fit()
    model.validate()

    infer      = Inference(graph, model, statistics)
    data, null = infer.init_comparison(N_SAMPLES, null_kws=dict(progress=True))

    # Estimate fractions of significant nodes
    odf = pd.concat(data.pop("coefs").tolist())
    ndf = pd.concat(null.pop("coefs").tolist())

    infer.add_stats_index(odf)
    infer.add_stats_index(ndf)

    odf = pd.concat([odf], keys=[0], names=["_"])
    ndf = pd.concat([ndf], keys=[0], names=["_"])

    pvals = infer.estimate_pvalues(odf, ndf, adjust=False)
    sigs  = []

    for alpha in (.01, .05, .1):
        pv  = infer.adjust_pvalues(pvals, alpha=alpha, copy=True)
        sig = (pv <= alpha)[["sim", "comp"]]

        sig["both"]    =  sig.all(axis=1)
        sig["sim"]    &= ~sig["both"]
        sig["comp"]   &= ~sig["both"]
        sig["neither"] = 1 - sig[["sim", "comp", "both"]].sum(axis=1)
        sig = sig.mean().to_frame().T
        # Add graph metadata
        for k, v in reversed(meta.items()):
            sig.insert(0, k, v)
        # Append to data list
        sigs.append(sig)

    # Unpack significance data
    sig01, sig05, sig10 = sigs

    # Compute null model averages
    null_avg = null.mean().to_frame().T

    # Compute calibrated coefficients
    cdata = np.log(data / null).reset_index(drop=True) \
        .replace([np.inf, -np.inf], np.nan) \
        .dropna() \
        .mean() \
        .to_frame().T
    # Add graph metadata
    for k, v in reversed(meta.items()):
        cdata.insert(0, k, v)
        data.insert(0, k, v)
        null_avg.insert(0, k, v)

    rawdata.append(data)
    nulltrend.append(null_avg)
    calibrated.append(cdata)
    signif_01.append(sig01)
    signif_05.append(sig05)
    signif_10.append(sig10)

# Prepare data frame ----------------------------------------------------------

proteins = {
    "raw":        pd.concat(rawdata, axis=0, ignore_index=True),
    "null_trend": pd.concat(nulltrend, axis=0, ignore_index=True),
    "calibrated": pd.concat(calibrated, axis=0, ignore_index=True),
    "signif_01":  pd.concat(signif_01, axis=0, ignore_index=True),
    "signif_05":  pd.concat(signif_05, axis=0, ignore_index=True),
    "signif_10":  pd.concat(signif_10, axis=0, ignore_index=True),
}

# Save data -------------------------------------------------------------------

joblib.dump(proteins, DATA/"proteins.pkl.gz", compress=True)
