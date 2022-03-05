#!/usr/bin/python
"""Download network datasets required for running the '{analysis}' notebook
from the `Netzschleuder <https://networks.skewed.de/>`_ repository.

The following datasets are downloaded:

#. Zachary Karate Club network (`karate/78`)
#. Interpersonal contacts among windsurfer (`windsurfers`)
#. Friendship between students in a residence hall (`residence_hall`)
#. Combined network of 10 ego-net samples from Facebook (`ego_social/facebook_combined`)
#. Facebook friendships within several organizations (`facebook_organizations`)
#. Network of mentions in the Dutch field of literary criticism (`dutch_criticism`)
#. Trust between physicians in four American cities (`physician_trust`)
#. Trust network from Epinions.com (`epinions_trust`)
#. Trust network among users on Advogato platform (`advogato`)
#. Strongly connected component of Pretty-Good-Privacy (PGP) web of trust (`pgp_strong`)
#. Interactome network for the PDZ-domian proteins (`interactome_pdz`)
#. Joshi-Tope human protein interactome (`reactome`)
#. A network of human proteins and their binding interactions (`interactome_figeys`)
#. A network of human proteins and their binding interactions (`interactome_stelzl`)
#. A network of human proteins and their binding interactions (`interactome_vidal`)
#. Network of protein-protein interactions in Saccharomyces cerevisiae (`interactome_collins`)
#. A network of protein-protein binding interactions among yeast proteins (`interactome_yeast`)
#. Gene transcription factor-based regulation, within the bacteria E. coli (`ecoli_transcription`)
#. Gene transcription factor-based regulation, within the yeast (`yeast_transcription`)

Details information including citation data can be found of pages
corresponding to individual datasets
(for instance `https://networks.skewed.de/net/karate`).
"""
import graph_tool.all as gt
from src import DATA
from src._ns import Netzschleuder
from src._argparse import get_parser


def get_component(idx: int, *, directed: bool = False):
    """Component extraction function factory."""
    def component_getter(graph):
        comp = gt.label_components(graph, directed=directed)[0].get_array()
        return gt.GraphView(graph, vfilt=comp == idx).copy()
    return component_getter


def fetch(force: bool = False):
    ns = Netzschleuder(DATA/"domains", force=force)
    # Metdata
    friendship    = dict(domain="social", relation="friendship")
    recognition   = dict(domain="social", relation="recognition")
    trust         = dict(domain="social", relation="trust")
    interactome   = dict(domain="biological", relation="interactome")
    genetic       = dict(domain="biological", relation="genetic")
    # Friendship (offline)
    meta = { **friendship, "desc": "offline" }
    ns("karate").fetch(network="78", **meta, label="Karate")
    ns("windsurfers").fetch(**meta, label="Windsurfers")
    ns("residence_hall").fetch(**meta, label="Residence hall")
    # Friendship (online)
    meta = { **friendship, "desc": "online" }
    ns("ego_social").fetch(network="facebook_combined", **meta, label="FB (ego-nets)")
    ns("facebook_friends").fetch(**meta, label="FB (Maier)")
    ns("facebook_organizations").fetch(network="S1", **meta, label="FB (S1)")
    ns("facebook_organizations").fetch(network="S2", **meta, label="FB (S2)")
    ns("facebook_organizations").fetch(network="M1", **meta, label="FB (M1)")
    ns("facebook_organizations").fetch(network="M2", **meta, label="FB (M2)")
    ns("facebook_organizations").fetch(network="L1", **meta, label="FB (L1)")
    ns("facebook_organizations").fetch(network="L2", **meta, label="FB (L2)")
    # Recognition (offline)
    meta = { **recognition, "desc": "offline" }
    ns("dutch_criticism").fetch(**meta, label="Dutch criticism")
    # Trust (offline)
    meta = { **trust, "desc": "offline" }
    for i in range(4):
        label = f"Physicians ({i+1})"
        ns("physician_trust").fetch(
            postprocess=get_component(i),
            alias=str(i+1),
            label=label,
            **meta
        )
    # Recognition (online)
    meta = { **trust, "desc": "online" }
    ns("epinions_trust").fetch(**meta, label="Epinions")
    ns("advogato").fetch(**meta, label="Advogato")
    ns("pgp_strong").fetch(**meta, label="PGP")
    # Interactomes (PDZ)
    meta = { **interactome, "desc": "PDZ" }
    ns("interactome_pdz").fetch(**meta, label="PDZ")
    # Interactomes (Human)
    meta = { **interactome, "desc": "human" }
    ns("reactome").fetch(**meta, label="Reactome")
    ns("interactome_figeys").fetch(**meta, label="Figeys")
    ns("interactome_stelzl").fetch(**meta, label="Stelzl")
    ns("interactome_vidal").fetch(**meta, label="Vidal")
    # Interactomes (yeast)
    meta = { **interactome, "desc": "yeast" }
    ns("collins_yeast").fetch(**meta, label="Collins")
    ns("interactome_yeast").fetch(**meta, label="Coulomb")
    # Gene transcription
    meta = { **genetic }
    ns("ecoli_transcription").fetch(network="v1.1", **meta, label="E. coli", desc="E. coli")
    ns("yeast_transcription").fetch(**meta, label="Yeast", desc="yeast")


if __name__ == "__main__":
    parser = get_parser(__file__, __doc__)
    args = parser.parse_args()
    fetch(args.force)
