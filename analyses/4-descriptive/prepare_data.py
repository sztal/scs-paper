"""Prepare descriptive statistics data for network datasets."""
from pathlib import Path
import pandas as pd
import joblib
from natsort import natsort_keygen
from tqdm.auto import tqdm
from pathcensus import PathCensus
from src.utils import load_graph, list_graphs, preprocess_graph


HERE = Path(__file__).absolute().parent
ROOT = HERE.parent.parent
DATA = HERE/"data"
DATA.mkdir(parents=True, exist_ok=True)


def get_descriptive_stats(name: str) -> pd.DataFrame:
    """Get data frame with descriptive stats for a given dataset.

    Statistics are calculated for the giant component as only
    giant components were considered in all the analyses presented
    in the paper.
    """
    fnames = list_graphs(name)

    def get_network_stats(name, network):
        graph    = load_graph(name, network, preprocess=False)
        domain   = graph["domain"]
        graph    = graph.as_undirected()
        n_total  = graph.vcount()
        graph    = preprocess_graph(graph)
        n_nodes  = graph.vcount()
        paths    = PathCensus(graph)
        degseq   = paths.degree

        dataset, network = network.split("__")

        return pd.DataFrame({
            "domain":  domain,
            "group":   name,
            "dataset": dataset,
            "network": network if network != dataset else "",
            "sim":     paths.similarity("global"),
            "comp":    paths.complementarity("global"),
            "n_nodes": n_nodes,
            "relsize": n_nodes / n_total,
            "density": graph.density(),
            "dbar":    degseq.mean(),
            "dcv":     degseq.std() / degseq.mean(),
            "dmax":    degseq.max()
        }, index=[0])

    data = pd.concat([
        get_network_stats(name, fn) for fn in tqdm(fnames)
    ], ignore_index=True)

    keys    = ["domain", "group", "dataset", "network"]
    average = data.set_index(keys).mean().to_frame().T
    average["domain"]  = ""
    average["group"]   = name
    average["dataset"] = ""
    average["network"] = "Average"
    average.set_index(keys, drop=True, inplace=True)

    data = data \
        .sort_values(keys, key=natsort_keygen()) \
        .set_index(keys, drop=True)
    data = pd.concat([data, average], ignore_index=False)
    return data


# PREPARE DATA ----------------------------------------------------------------

datasets = ["domains", "social"]
data     = pd.concat([
    get_descriptive_stats(dataset)
    for dataset in tqdm(datasets)
], ignore_index=False)

joblib.dump(data, DATA/"descriptive-statistics.pkl.gz", compress=3)
