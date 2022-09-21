"""Utility functions."""
from typing import Any, Optional, Union, List, Callable
import os
from pathlib import Path
import numpy as np
import igraph as ig
from . import DATA


def get_root_path(
    *,
    origin: str | bytes | os.PathLike = ".",
    root_dir: str = "scs-paper"
) -> Path:
    """Get root path of the project.

    Parameters
    ----------
    origin
        Path to start the search from.
    root_dir
        Name of the root directory to look for.

    Raises
    ------
    ValueError
        If ``root_dir`` cannot be found.
    """
    path = Path(origin).absolute()
    while path.stem != root_dir:
        if path is path.parent:
            raise ValueError(f"'{root_dir}' cannot be found")
        path = path.parent
    return path

def list_graphs(
    dataset: str,
    *,
    datapath: Union[str, bytes, os.PathLike] = DATA
) -> List[str]:
    """List graphs available for a dataset.

    Parameters
    ----------
    dataset
        Name of a dataset.
    datapath
        Path to the main data directory.
    """
    path = Path(datapath)/dataset
    return [
        ".".join(fpath.stem.split(".")[:-1]) for fpath
        in path.glob("*.pkl.gz")
    ]

def load_graph(
    dataset: str,
    name: Optional[str] = None,
    *,
    datapath: Union[str, bytes, os.PathLike] = DATA,
    preprocess: bool = False,
    **kwds: Any
) -> ig.Graph:
    """Load graph from a given dataset.

    Parameters
    ----------
    dataset
        Name of a dataset.
    name
        Name of a particular network.
        It is assumed to be equal to `dataset` if ``None``.
    datapath
        Path to the main data directory.
    preprocess
        Should the graph be preprocess after loading.
    **kwds
        Passed to :py:func:`preprocess_graph` when ``preprocess=True``.
        Ignored otherwise.
    """
    name = name or dataset
    if "__" not in name:
        name += "__" + name
    name += ".pkl.gz"

    fpath = Path(datapath)/dataset/name
    graph = ig.Graph.Read_Picklez(str(fpath))
    if preprocess:
        graph = preprocess_graph(graph, **kwds)
    return graph

def get_largest_component(graph: ig.Graph, **kwds: Any) -> ig.Graph:
    """Get largest component of a graph.

    ``**kwds`` are passed to :py:meth:`igraph.Graph.components`.
    """
    vids = None
    for component in graph.components(**kwds):
        if vids is None or len(component) > len(vids):
            vids = component
    return graph.induced_subgraph(vids)

def preprocess_graph(
    graph: ig.Graph,
    simplify: bool = True,
    undirected: bool = True,
    largest_component: bool = True,
    mode: Optional[str] = None,
    *,
    combine_edges: Optional[Union[str, Callable]] = None,
    **kwds: Any
) -> ig.Graph:
    """Preprocess a graph.

    Parameters
    ----------
    graph
        Graph object.
    simplify
        Whether to simplify the graph.
    largest_component
        Whether only the largest component should be taken.
    mode
        Passed to :py:meth:`igraph.Graph.components`.
    combine_edges
        Optional edge combination method.
        Passed to :py:meth:`igraph.Graph.simplify`
        and :py:meth:`igraph.Graph.to_undirected`.
    **kwds
        Passed to :py:meth:`igraph.Graph.simplify`.

    Returns
    -------
    graph
        Preprocess copy of the original `graph`.
    """
    graph = graph.copy()
    if simplify:
        graph.simplify(combine_edges=combine_edges, **kwds)
    if undirected:
        graph.to_undirected(combine_edges=combine_edges)
    if largest_component:
        mode = dict(mode=mode) if mode else {}
        graph = get_largest_component(graph, **mode)
    return graph

def rescale(X: np.ndarray, m0=0, m1=1) -> np.ndarray:
    """Rescale numeric 1D array.

    Parameters
    ----------
    X
        1D array.
    m0
        Minimum value. Has to be lower than ``m1``.
    m1
        Maximum value. Has to be greater than ``m0``.
    """
    if not isinstance(X, np.ndarray):
        X = np.array(X)
    if m0 >= m1:
        raise ValueError("'m0' has to be lower than 'm1'")
    if X.ndim != 1:
        raise AttributeError("'X' has to be 1D")

    X -= X.min()
    xmax = X.max()
    if xmax != 0:
        X /= X.max()

    if m1 != 1:
        X *= m1 - m0
    if m0 != 0:
        X += m0

    return np.clip(X, m0, m1)

def make_er_graph(n: int, kbar: float) -> ig.Graph:
    """Make ER random graph with given number of nodes
    and average degree.
    """
    p = kbar / (n-1)
    return ig.Graph.Erdos_Renyi(n, p=p, directed=False)

def make_rgg(n: int, kbar: float) -> ig.Graph:
    """Make Random Geometric Graph with given number of nodes
    and average degree.
    """
    radius = np.sqrt(kbar/(np.pi*(n-1)))
    return ig.Graph.GRG(n, radius=radius, torus=True)
