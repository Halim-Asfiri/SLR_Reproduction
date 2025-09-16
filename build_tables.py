#!/usr/bin/env python3
import argparse, sys, re, json, hashlib
from pathlib import Path
import pandas as pd

def load_bibmap(path):
    if path and Path(path).exists():
        m = {}
        df = pd.read_csv(path)
        for _, r in df.iterrows():
            t = str(r.get("Title","")).strip().lower()
            k = str(r.get("BibKey","")).strip()
            if t and k:
                m[t] = k
        return m
    return {}

def pick_rep_operator(row):
    txt = " ".join(str(row.get(c,"")) for c in
        ["Compression function","Relation to Graph Reduction and Compression","Objective","Steps","Title","Detailed summary"]).lower()
    if any(k in txt for k in ["sketch","count-min","minhash"]): return "Summaries/Sketches"
    if any(k in txt for k in ["coarsen","pooling","hierarchical","supernode","topology-aware"]): return "Coarsening"
    if any(k in txt for k in ["sparsif","prune","top-k","threshold","sampling","subgraph"]): return "Sampling/Sparsification"
    if any(k in txt for k in ["quantization","codec"]): return "Quantization/Codec"
    if any(k in txt for k in ["embedding","graph2vec","node2vec","representation learning","latent","gnn","graph neural","stgnn","hgnn","gcn","gat","gin"]):
        return "Embeddings"
    return "Embeddings"

def pick_update_regime(row):
    txt = " ".join(str(row.get(c,"")) for c in ["Evaluation process","Detailed summary","Objective","Title"]).lower()
    if any(k in txt for k in ["stream","online","real-time"]): return "Streaming"
    if any(k in txt for k in ["mini-batch","minibatch","batch","window","sliding"]): return "Mini-batch"
    if any(k in txt for k in ["episodic","per subject","per patient","per scene","offline","cross validation"]): return "Episodic"
    t = str(row.get("Title","")).lower()
    if any(k in t for k in ["intrusion","encrypted","malicious","traffic","web shell"]): return "Streaming"
    if any(k in t for k in ["wind","meteorolog","forecast","prediction"]): return "Mini-batch"
    if any(k in t for k in ["point cloud","shape","3d","pose","stratigraph"]): return "Episodic"
    return "NR"

def pick_fidelity(row):
    txt = " ".join(str(row.get(c,"")) for c in ["Evaluation method (reconstruction? Down-stream task?…)","Relation to Graph Reduction and Compression","Objective","Detailed summary"]).lower()
    if any(k in txt for k in ["homophily","modularity","nmi","betti","topological","spectral","path","edge type","relation type","adjacency","reconstruction"]):
        return "Topology"
    if "label" in txt or "semantic" in txt: return "Labels/Semantics"
    return "Task-aware"

def pick_learning(row):
    txt = " ".join(str(row.get(c,"")) for c in ["Compression function","Objective","Steps","Detailed summary","Title"]).lower()
    if any(k in txt for k in ["gnn","graph neural","stgnn","hgnn","gat","gcn","gin"]): return "GNN-based"
    if any(k in txt for k in ["embedding","graph2vec","node2vec","manifold","metric learning"]): return "Embedding-based"
    if any(k in txt for k in ["granger","spectral clustering","pagerank","coarsen","sparsif"]): return "Classical/Algorithmic"
    return "Embedding-based"

def structural_types(row):
    txt = " ".join(str(row.get(c,"")) for c in ["Evaluation method (reconstruction? Down-stream task?…)","Evaluation process","Detailed summary"]).lower()
    tags=[]
    if any(k in txt for k in ["edge type","relation type","adjacency","link prediction","reconstruct"]): tags.append("Adjacency/Type")
    if any(k in txt for k in ["homophily","modularity","nmi","community"]): tags.append("Homophily/Comm.")
    if any(k in txt for k in ["spectral","laplacian","eigen"]): tags.append("Spectral")
    if any(k in txt for k in ["betti","tda","persistent"]): tags.append("Topological (TDA)")
    if any(k in txt for k in ["path","shortest path","walk length"]): tags.append("Paths")
    return ", ".join(tags) if tags else "NR"

def system_types(row):
    txt = " ".join(str(row.get(c,"")) for c in ["Evaluation method (reconstruction? Down-stream task?…)","Results (model does better with x% than model xyz)","Evaluation process","Detailed summary"]).lower()
    tags=[]
    if any(k in txt for k in ["latency","ms","millisecond","response time"]): tags.append("Latency")
    if any(k in txt for k in ["throughput","fps","qps","pps"]): tags.append("Throughput/FPS")
    if any(k in txt for k in ["memory","ram","gb","mb","parameters","params","flops","gflops"]): tags.append("Memory/Params/FLOPs")
    if any(k in txt for k in ["edge device","jetson","raspberry","embedded"]): tags.append("Edge device")
    return ", ".join(tags) if tags else "NR"

def cite_from_bibmap(title, bibmap):
    t = str(title).strip().lower()
    if t in bibmap:
        return f"\\cite{{{bibmap[t]}}}"
    # fallback: just emit title (rare)
    return "\\emph{(key-missing)}"

def write_and_hash(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    print(f"[emit] {path}  sha256={h}")

def emit_table5(df, outdir, bibmap):
    # longtable with citations in first column
    rows=[]
    for _, r in df.iterrows():
        rows.append([
            cite_from_bibmap(r.get("Title",""), bibmap),
            pick_rep_operator(r),
            pick_update_regime(r),
            pick_fidelity(r),
            pick_learning(r),
            "Yes" if structural_types(r)!="NR" else "No/NR",
            "Yes" if system_types(r)!="NR" else "No/NR",
        ])
    header = r"""\begin{footnotesize}
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.1}
\begin{longtable}{p{0.16\textwidth} p{0.20\textwidth} p{0.12\textwidth} p{0.13\textwidth} p{0.17\textwidth} p{0.07\textwidth} p{0.07\textwidth}}
\caption{Mapping of the corpus to taxonomy axes (A--D) with evidence flags for structural and system metrics. NR = not reported.}
\label{tab:taxonomy-map-long}\\
\toprule
Paper & Representation operator & Update regime & Fidelity target & Learning vs algorithmic & Struct.? & System?\\
\midrule
\endfirsthead
\toprule
Paper & Representation operator & Update regime & Fidelity target & Learning vs algorithmic & Struct.? & System?\\
\midrule
\endhead
\midrule
\multicolumn{7}{r}{\emph{Continued on next page}}\\
\midrule
\endfoot
\bottomrule
\endlastfoot
"""
    lines=[header]
    for row in rows:
        esc = lambda s: s if row.index(s)==0 else str(s).replace("&","\\&").replace("_","\\_")
        cells=[row[0]]+[str(c).replace("&","\\&").replace("_","\\_") for c in row[1:]]
        lines.append(" " + " & ".join(cells) + r" \\")
    lines.append(r"\end{longtable}")
    lines.append(r"\end{footnotesize}")
    write_and_hash(Path(outdir)/"table5_taxonomy_map_longtable_cited.tex", "\n".join(lines))

def emit_table7(df, outdir, bibmap):
    rows=[]
    s_yes=sys_yes=0
    for _, r in df.iterrows():
        s_type = structural_types(r); sys_type = system_types(r)
        s_flag = "Yes" if s_type!="NR" else "No/NR"
        sys_flag = "Yes" if sys_type!="NR" else "No/NR"
        s_yes += (s_flag=="Yes"); sys_yes += (sys_flag=="Yes")
        rows.append([cite_from_bibmap(r.get("Title",""), bibmap), s_flag, s_type, sys_flag, sys_type])
    header = r"""\begin{footnotesize}
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.1}
\begin{longtable}{p{0.20\textwidth} p{0.10\textwidth} p{0.28\textwidth} p{0.10\textwidth} p{0.28\textwidth}}
\caption{Per-paper evidence of \emph{fidelity} and \emph{system} reporting. We mark whether a study reports any explicit structural metric (e.g., homophily/NMI, spectral, TDA, adjacency/type) and any system metric (e.g., latency, throughput/FPS, memory/params/FLOPs). NR = not reported.}
\label{tab:fidelity-system}\\
\toprule
Paper & Structural? & Structural metric type(s) & System? & System metric type(s)\\
\midrule
\endfirsthead
\toprule
Paper & Structural? & Structural metric type(s) & System? & System metric type(s)\\
\midrule
\endhead
\midrule
\multicolumn{5}{r}{\emph{Continued on next page}}\\
\midrule
\endfoot
\bottomrule
\endlastfoot
"""
    lines=[header]
    for row in rows:
        cells=[row[0]]+[str(c).replace("&","\\&").replace("_","\\_") for c in row[1:]]
        lines.append(" " + " & ".join(cells) + r" \\")
    lines.append(r"\end{longtable}")
    lines.append(r"\end{footnotesize}")
    write_and_hash(Path(outdir)/"table7_fidelity_system_evidence.tex", "\n".join(lines))
    print(f"[summary] structural={s_yes}/{len(rows)}  system={sys_yes}/{len(rows)}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", required=True)
    ap.add_argument("--bibmap", default=None)
    ap.add_argument("--emit", choices=["table5","table7","all"], default="all")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    df = pd.read_excel(args.excel, sheet_name="Summerization")
    required_cols = ["Title","Detailed summary","Evaluation method (reconstruction? Down-stream task?…)",
                     "Evaluation process","Objective"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"[error] Missing required columns in Excel: {missing}", file=sys.stderr)
        sys.exit(2)

    bibmap = load_bibmap(args.bibmap)

    if args.emit in ("table5","all"):
        emit_table5(df, args.outdir, bibmap)
    if args.emit in ("table7","all"):
        emit_table7(df, args.outdir, bibmap)

if __name__=="__main__":
    main()
