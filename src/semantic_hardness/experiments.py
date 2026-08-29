from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from .cnf import (
    random_3cnf, planted_3cnf, cycle_graph_cnf, horn_chain, xor_chain_3cnf,
    pigeonhole_3cnf, tseitin_cubic_cnf, random_2cnf
)
from .analysis import (
    exact_profile, constant_image_barrier, representation_hop, bottleneck_profile,
    same_image_realizability_diagnostic, audit_completeness_table,
    channel_ablation_table, path_normalization_table
)


def families_small():
    fam=[]
    # Classical tractable / structurally controlled families.
    for n in [4,6,8,10]:
        fam += [cycle_graph_cnf(n), horn_chain(n), random_2cnf(n,2.0,1000+n)]
    # Several seeds expose variation without pretending to prove asymptotics.
    for n in [4,6,8,10]:
        for seed in [11,29,47]:
            fam += [random_3cnf(n,4.2,2000+100*n+seed), planted_3cnf(n,4.2,3000+100*n+seed)]
    for k in [3,4,5,6]:
        fam.append(xor_chain_3cnf(k))
    fam += [pigeonhole_3cnf(3,2), pigeonhole_3cnf(4,3)]
    # Cubic Tseitin contradictions give a proof-complexity stress family.
    for nv in [4,6,8]:
        fam.append(tseitin_cubic_cnf(nv, odd_charge=True))
    return fam


def ensure(out: Path):
    for x in ['raw','tables','figures']:
        (out/x).mkdir(parents=True,exist_ok=True)


def _save(fig, out:Path, stem:str):
    fig.tight_layout()
    fig.savefig(out/'figures'/f'{stem}.pdf')
    fig.savefig(out/'figures'/f'{stem}.png',dpi=180)
    plt.close(fig)


def run_all(outdir: str|Path) -> dict:
    out=Path(outdir); ensure(out)
    profiles=[]
    for f in families_small():
        # Exact future rows cost O((tmax+1)2^n); keep the audit finite and explicit.
        maxp=min(f.n_vars,10)
        profiles.append(exact_profile(f,maxp))
    prof=pd.concat(profiles,ignore_index=True)
    prof.to_csv(out/'raw'/'exact_profiles.csv',index=False)
    bott=bottleneck_profile(prof)
    bott.to_csv(out/'raw'/'bottleneck_profiles.csv',index=False)

    summary=(bott.groupby('family').agg(
        n_vars=('n_vars','max'), max_classes=('semantic_classes','max'),
        max_slw=('slw_bits','max'), max_rank=('semantic_rank','max'),
        max_boundary=('boundary_prefixes','max'), total_runtime_ms=('runtime_ms','sum')
    ).reset_index())
    summary.to_csv(out/'tables'/'table_exact_summary.csv',index=False)

    rep=bott[bott['stage'].isin([0,2,4,6,8,10])][[
        'family','n_vars','stage','semantic_classes','slw_bits','semantic_rank',
        'boundary_fraction','runtime_ms']]
    rep.to_csv(out/'tables'/'table_stage_profiles.csv',index=False)

    barriers=[]
    for n in [8,10,12,14,16,18]:
        # fixed-seed, high-ratio formulas; exact exhaustive nonemptiness is diagnostic only.
        f=random_3cnf(n,5.5,9000+n)
        barriers.append(constant_image_barrier(f))
    barr=pd.DataFrame(barriers)
    barr.to_csv(out/'tables'/'table_constant_image_barrier.csv',index=False)

    hops=pd.DataFrame([representation_hop(f) for f in families_small()])
    hops.to_csv(out/'tables'/'table_representation_hopping.csv',index=False)

    convergence=path_normalization_table().rename(columns={'strategy':'path','semantic_object':'primary_object','normal_form':'converges_to'})
    convergence.to_csv(out/'tables'/'table_convergence_paths.csv',index=False)

    same=same_image_realizability_diagnostic()
    same.to_csv(out/'tables'/'table_same_image_separation.csv',index=False)

    complete=audit_completeness_table()
    complete.to_csv(out/'tables'/'table_audit_completeness.csv',index=False)

    ablation=channel_ablation_table()
    ablation.to_csv(out/'tables'/'table_ablation.csv',index=False)

    natural=(summary[summary.family.str.contains('tseitin|php_|xor_chain|random3_n10|horn_chain_n10|cycle_graph_n10',regex=True)]
             [['family','n_vars','max_classes','max_slw','max_rank','max_boundary','total_runtime_ms']])
    natural.to_csv(out/'tables'/'table_natural_families.csv',index=False)

    theorem=pd.DataFrame([
        ('Canonical bridge','Future-observation image is isomorphic to future-equivalence quotient','proved'),
        ('Minimal exact interface','Every exact future-sufficient interface refines the canonical image','proved'),
        ('Same-image separation','One-state image nonemptiness is in P for 2-CNF and NP-complete for 3-CNF','proved from classical SAT results'),
        ('Audit completeness','No proper subset of E/R/S/T bounds the full stage-cost identity without a domination assumption','proved in audit model'),
        ('Representation invariance','Polynomially intertranslatable semantic representations preserve polynomiality of the normalized profile','proved under stated emulation assumptions'),
        ('Akhtar semantic convergence','Polynomial E/R/S/T and call counts over polynomial stages imply polynomial total computation','proved'),
        ('Hardness localization','If P != NP, an exact polynomial-stage pipeline for an NP-hard language must lose polynomial control somewhere','conditional corollary'),
        ('Boundary sufficiency','Polynomial exact boundary encoding/refinement over polynomial stages implies tractability','conditional theorem'),
        ('No P=NP claim','No theorem supplies a universal polynomial resolver for arbitrary 3-SAT','scope constraint'),
    ],columns=['result','statement','status'])
    theorem.to_csv(out/'tables'/'table_theorem_status.csv',index=False)

    # Figure 1: class growth for representative families.
    pattern='random3_n10|cycle_graph_n10|horn_chain_n10|xor_chain_inputs6|tseitin_cubic_v8_odd'
    sel=bott[bott['family'].str.contains(pattern,regex=True)]
    fig,ax=plt.subplots(figsize=(7.4,4.6))
    for fam,g in sel.groupby('family'):
        ax.plot(g.stage,g.semantic_classes,marker='o',label=fam)
    ax.set_xlabel('Stage / assigned-prefix length'); ax.set_ylabel('Exact future-semantic classes')
    ax.set_yscale('log',base=2); ax.legend(fontsize=6.5); ax.grid(alpha=.25)
    _save(fig,out,'fig1_semantic_classes')

    # Figure 2: E/R/S/T proxies.
    cats=[]
    for fam,g in bott.groupby('family'):
        row=g.loc[g.stage.idxmax()]
        cats.append(row[['family','E','R','S','T']])
    cdf=pd.DataFrame(cats)
    keep=cdf[cdf.family.str.contains('cycle_graph_n10|horn_chain_n10|random3_n10|planted3_n10|xor_chain_inputs6|tseitin_cubic_v8|php_4_3',regex=True)].head(12)
    fig,ax=plt.subplots(figsize=(8.4,4.9)); x=np.arange(len(keep)); width=.18
    for j,k in enumerate(['E','R','S','T']): ax.bar(x+(j-1.5)*width,keep[k],width,label=k)
    ax.set_xticks(x); ax.set_xticklabels(keep.family,rotation=50,ha='right',fontsize=7)
    ax.set_ylabel('log2 operational proxy'); ax.legend()
    _save(fig,out,'fig2_bottleneck_spectrum')

    # Figure 3: reverse boundary fraction.
    fig,ax=plt.subplots(figsize=(7.4,4.6))
    for fam,g in sel.groupby('family'):
        ax.plot(g.stage,g.boundary_fraction,marker='s',label=fam)
    ax.set_xlabel('Stage'); ax.set_ylabel('Unresolved boundary fraction'); ax.set_ylim(-.02,1.02)
    ax.legend(fontsize=6.5); ax.grid(alpha=.25)
    _save(fig,out,'fig3_boundary_fraction')

    # Figure 4: constant-image realizability diagnostic.
    fig,ax=plt.subplots(figsize=(6.5,4.2)); ax.plot(barr.n_vars,barr.realizability_ms,marker='o')
    ax.set_yscale('log'); ax.set_xlabel('Variables'); ax.set_ylabel('Exact realizability time (ms, log scale)')
    ax.set_title('One-state image does not remove realizability work'); ax.grid(alpha=.25)
    _save(fig,out,'fig4_realizability_barrier')

    # Figure 5: convergence graph.
    G=nx.DiGraph(); paths=list(convergence.path); core=['E','R','S','T']
    for p in paths:
        G.add_node(p)
        for c in convergence.loc[convergence.path==p,'converges_to'].iloc[0].split(','): G.add_edge(p,c)
    for c in core: G.add_node(c)
    pos={}
    for i,p in enumerate(paths): pos[p]=(0, i-len(paths)/2)
    for i,c in enumerate(core): pos[c]=(3, (i-1.5)*2)
    fig,ax=plt.subplots(figsize=(8,6)); nx.draw_networkx(G,pos,ax=ax,node_size=1500,font_size=8,arrows=True); ax.axis('off')
    _save(fig,out,'fig5_convergence_graph')

    # Figure 6: same one-state image, different realizability mechanisms.
    fig,ax=plt.subplots(figsize=(6.8,4.4))
    for problem,g in same.groupby('problem'):
        ax.plot(g.n_vars,g.runtime_ms,marker='o',label=problem)
    ax.set_yscale('log'); ax.set_xlabel('Variables'); ax.set_ylabel('Measured diagnostic time (ms, log scale)')
    ax.set_title('Same one-state image; different realizability mechanisms'); ax.legend(); ax.grid(alpha=.25)
    _save(fig,out,'fig6_same_image_separation')

    # Figure 7: natural-family maximum SLW / rank.
    nf=natural.head(14)
    fig,ax=plt.subplots(figsize=(8.2,4.8)); x=np.arange(len(nf)); width=.38
    ax.bar(x-width/2,nf.max_slw,width,label='max SLW'); ax.bar(x+width/2,nf.max_rank,width,label='max GF(2) rank')
    ax.set_xticks(x); ax.set_xticklabels(nf.family,rotation=50,ha='right',fontsize=7); ax.set_ylabel('bits / rank'); ax.legend()
    _save(fig,out,'fig7_natural_family_spectrum')

    return {
        'profiles':len(prof),'families':prof.family.nunique(),'barrier_rows':len(barr),
        'same_image_rows':len(same),'figures':7,'tables':10
    }
