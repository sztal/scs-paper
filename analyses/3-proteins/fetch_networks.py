"""Downaload networks for running the '{analysis}' notebook
from the `Netzschleuder <https://networks.skewed.de/>`_ repository.

The following datasets are downloaded:

#. Protein-protein iteraction networks ("interactome") for 1,840 species.
   An interactome captures all physical protein-protein interactions within
   one species, from direct biophysical protein-protein interactions to
   regulatory protein-DNA and metabolic interactions.

References
----------

Zitnik, M., Sosič, R., Feldman, M. W., & Leskovec, J. (2019).
Evolution of resilience in protein interactomes across the tree of life.
Proceedings of the National Academy of Sciences, 116(10), 4426–4433.
https://doi.org/10.1073/pnas.1818013116
"""
from tqdm import tqdm
from src import DATA
from src._ns import Netzschleuder
from src._argparse import get_parser


def fetch(force: bool = False):
    ns = Netzschleuder(
        datapath=DATA/"proteins",
        name="tree-of-life",
        force=force
    )
    for network in tqdm(ns.networks):
        meta = dict(
            vp={"name": "name"},
            domain="biological",
            relation="interactome",
            desc="tree of life",
            label=int(network)
        )
        ns.fetch(network, **meta)


if __name__ == "__main__":
    parser = get_parser(__file__, __doc__)
    args = parser.parse_args()
    fetch(args.force)
