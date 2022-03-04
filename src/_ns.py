"""Classes and other utilities for downloading network datasets
from `Netzschleuder <https://networks.skewed.de/>`_,
a network catalogue, repository and centrifuge.

This module depends on :py:mod:`graph_tool` package which
may be problematic to install, in particular on Windows machines,
so its dependencies are not included in the main list of dependencies
for the rest of the project. However, if one does not need to downlaod
the raw data there is no need to run any of the code defined here,
so there is also no need for installing :py:mod:`graph_tool`.
"""
from typing import Any, Optional, Union, Iterable, List, Dict, Callable
import os
from pathlib import Path
from functools import cached_property
import requests
import igraph as ig
import graph_tool.all as gt


class Netzschleuder:
    """Main class for downloading network datasets
    from the `Netzschleuder <https://networks.skewed.de/>`_
    repository.

    Attributes
    ----------
    name
        Dataset name.
    datapath
        Path to a directory in which data is to be stored.
    force
        Default value for the ``force`` in the
        :py:meth:`fetch` function.
    """
    apiurl = "https://networks.skewed.de/api/net"

    def __init__(
        self,
        datapath: Union[str, bytes, os.PathLike],
        name: Optional[str] = None,
        *,
        force: bool = False
    ) -> None:
        """Initialization method."""
        self.name = name
        self.datapath = Path(datapath).absolute()
        if not self.datapath.exists():
            self.datapath.mkdir(exist_ok=True, parents=True)
        self.force = force

    def __call__(self, name: str):
        """Set name and return `self`."""
        self.name = name
        return self

    @cached_property
    def networks(self) -> List[str]:
        """List of networks available for the given dataset."""
        resp = requests.get(f"{self.apiurl}/{self.name}")
        resp.raise_for_status()
        data = resp.json()
        return data["nets"]

    # Main methods ------------------------------------------------------------

    def download(
        self,
        network: Optional[str] = None,
        postprocess: Optional[Callable] = None,
        **kwds: Any
    ) -> ig.Graph:
        """Download network data.

        Parameters
        ----------
        network
            Name of a specific network to download.
            If ``None`` then `self.name` is used.
            This is a correct behavior for datasets
            consisting of only one network.
        postprocess
            Optional callable for postprocessing
            graph. It should have the following signature
            ``(graph_tool.Graph) -> (graph_tool.Graph)``.
        **kwds
            Passed to :py:meth:`gt_to_igraph`.
        """
        network = network or self.name
        graph = gt.collection.ns[f"{self.name}/{network}"]
        if postprocess is not None:
            graph = postprocess(graph)
        return self.gt_to_igraph(graph, **kwds)

    def fetch(
        self,
        network: Optional[str] = None,
        *,
        alias: Optional[str] = None,
        force: Optional[bool] = None,
        **kwds: Any
    ) -> ig.Graph:
        """Fetch network data by downloading or retrieving from disk.

        Parameters
        ----------
        network
            Name of a specific network to download.
            If ``None`` then `self.name` is used.
            This is a correct behavior for datasets
            consisting of only one network.
        alias
            Optional alias to use instead of the network name.
            Useful when saving parts of the same network as different files.
        force
            Should download be forced even if network is already downloaded.
            If ``None`` the an instance attribute is used.
        **kwds
            Passed to :py:meth:`gt_to_igraph`.
        """
        if force is None:
            force = self.force

        network = network or self.name
        alias = alias if alias else network
        fpath = self.datapath/f"{self.name}__{alias}.pkl.gz"
        if force or not fpath.exists():
            graph = self.download(network, **kwds)
            graph.write_picklez(str(fpath))
            return graph
        return ig.Graph.Read_Picklez(str(fpath))

    # Auxiliary method --------------------------------------------------------

    @staticmethod
    def gt_to_igraph(
        graph: gt.Graph,
        vp: Optional[Dict[str, str]] = None,
        ep: Optional[Dict[str, str]] = None,
        add_tags: Optional[Iterable[str]] = (),
        **kwds
    ) -> ig.Graph:
        """Convert :py:class:`graph_tool.Graph` to :py:class:`igraph.Graph`.

        Parameters
        ----------
        graph
            Graph object.
        vp
        List of vertex properties to retain.
        ep
            List of edge properties to retain.
        **kwds
            Additional graph properties.
        """
        i, j = gt.adjacency(graph).nonzero()
        G = ig.Graph(graph.num_vertices(), directed=graph.is_directed())
        G.add_edges(list(zip(i, j)))

        if  vp:
            for attr, prop in vp.items():
                G.vs[attr] = list(graph.vp[prop])
        if ep:
            for attr, prop in ep.items():
                G.es[attr] = list(graph.ep[prop])
        for prop in graph.gp:
            if prop == "tags":
                G[prop] = list(set(graph.gp[prop]) | set(add_tags))
            else:
                G[prop] = str(graph.gp[prop])
        for k, v in kwds.items():
            G[k] = v
        return G
