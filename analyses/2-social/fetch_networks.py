"""Download network datasets for running the '{analysis}' notebook
from the `Netzschleuder <https://networks.skewed.de/>`_ repository.

The following datasets are downloaded:

#. Ugandan villages dataset from Chami et al. (``ugandan_village``)

References
----------

Chami, G. F., Ahnert, S. E., Kabatereine, N. B., & Tukahebwa, E. M. (2017).
Social network fragmentation and community health.
Proceedings of the National Academy of Sciences, 114(36), E7425–E7431.
https://doi.org/10.1073/pnas.1700166114
"""
from tqdm import tqdm
from src import DATA
from src._ns import Netzschleuder
from src._argparse import get_parser


def fetch(force: bool = False):
    ns = Netzschleuder(
        datapath=DATA/"social",
        name="ugandan_village",
        force=force
    )
    # Download Ugandan villages data
    for network in tqdm(ns.networks):
        if "friendship" in network:
            relation = "friendship"
        else:
            relation = "health advice"

        if relation == "friendship":
            idx = int(network.split("-")[-1])
        else:
            idx = int(network.split("_")[-1])

        meta = dict(
            vp={"name": "name"},
            domain="social",
            relation=relation,
            desc="offline",
            idx=idx,
            label=f"{relation.split()[-1].capitalize()} ({idx})"
        )
        ns.fetch(network, **meta)


if __name__ == "__main__":
    parser = get_parser(__file__, __doc__)
    args = parser.parse_args()
    fetch(args.force)
