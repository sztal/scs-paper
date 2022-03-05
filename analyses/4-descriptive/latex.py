"""Function for converting data frames to latex tables."""
import re
import pandas as pd

def to_latex(data: pd.DataFrame, dataset: str, **kwds) -> str:
    """Convert data frame to latex table."""
    data    = data.xs(dataset, level="group")
    n_nodes = data["n_nodes"].tolist()
    n_nodes[:-1] = [ str(int(n)) for n in n_nodes[:-1] ]
    n_nodes[-1]  = f"{n_nodes[-1]:.2f}"
    data["n_nodes"] = n_nodes

    columns = {
        "sim":     r"$s$",
        "comp":    r"$c$",
        "comp_w":  r"$h$",
        "n_nodes": r"$n$",
        "relsize": r"$S$",
        "density": r"$\rho$",
        "dbar":    r"$\langle{d_i}\rangle$",
        "dcv":     r"$\sigma_{d_i}$",
        "dmax":    r"$d_{\text{max}}$"
    }
    datasets = {
        "social":  r"Ugandan village networks",
        "domains": r"Social and biological networks"
    }

    N = len(data) - 1
    label = datasets[dataset]
    kwds = {
        "float_format": "%.2f",
        "escape":       False,
        "position":     "h!",
        "label":        f"app:tab:stats-{dataset}",
        "caption":      rf"Descriptive statistics for {label} ($N = {N}$)",
        **kwds
    }
    latex = data.rename(columns=columns).to_latex(**kwds).strip().split("\n")
    pre   = latex[:4]
    top   = latex[4:9]
    mid   = "\n".join(latex[9:-4]).replace("_", "\_")
    rx    = re.compile(r"\.00(\s*\\\\\s*)", re.IGNORECASE)
    mid   = rx.sub(r"\1", mid)
    mid  += "\n\\midrule"
    rx    = re.compile(r"^\s*(\S*)\s*$", re.IGNORECASE)
    avg   = latex[-4][:-2].strip().split("&")
    avg   = [ rx.sub(r" \\textbf{\1} ", x) for x in avg ]
    avg   = "&".join(avg) + r" \\"
    bot   = [
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}",
        "\t\\footnotesize",
        "\t\\item $s$ - global similarity (clustering)",
        "\t\\item $c$ - global complementarity",
        "\t\\item $n$ - number of nodes in the giant component",
        "\t\\item $S$ - relative size of the giant component",
        "\t\\item $\\rho$ - edge density",
        "\t\\item $\\langle{d_i}\\rangle$ - average node degree",
        "\t\\item $\\sigma_{d_i}$ - coefficient of variation of node degrees",
        "\t\\item $d_{\\text{max}}$ - maximum node degree",
        r"\end{tablenotes}",
        r"\end{threeparttable}",
        r"\end{table}"
    ]

    # Add font formatting
    pre.append(r"\sffamily")
    pre.append(r"\footnotesize")
    pre.append(r"\begin{threeparttable}")

    latex = "\n".join([*pre, *top, mid, avg, *bot])
    return latex.strip()
