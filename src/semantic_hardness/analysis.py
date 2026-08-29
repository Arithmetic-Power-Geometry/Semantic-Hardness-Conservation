from __future__ import annotations
from itertools import product
from math import ceil, log2
import time
import numpy as np
import pandas as pd
from .cnf import CNF, is_horn, is_2sat


def gf2_rank(rows: list[tuple[int,...]]) -> int:
    if not rows: return 0
    a=np.array(rows,dtype=np.uint8)%2
    m,n=a.shape; r=0
    for c in range(n):
        piv=next((i for i in range(r,m) if a[i,c]),None)
        if piv is None: continue
        if piv!=r: a[[r,piv]]=a[[piv,r]]
        for i in range(m):
            if i!=r and a[i,c]: a[i]^=a[r]
        r+=1
        if r==m: break
    return r


def exact_profile(f: CNF, max_prefix: int|None=None) -> pd.DataFrame:
    """Exact future-behavior quotient profile. Intended for small n only."""
    max_prefix=f.n_vars if max_prefix is None else min(max_prefix,f.n_vars)
    rows=[]
    for t in range(max_prefix+1):
        st=time.perf_counter()
        signatures=[]; accept=reject=boundary=0
        for p in product((0,1),repeat=t):
            sig=f.truth_row(p); signatures.append(sig)
            ones=sum(sig)
            if ones==0: reject+=1
            elif ones==len(sig): accept+=1
            else: boundary+=1
        uniq=list(dict.fromkeys(signatures))
        rank=gf2_rank(uniq)
        elapsed=(time.perf_counter()-st)*1000
        nclasses=len(uniq)
        slw=0 if nclasses<=1 else ceil(log2(nclasses))
        raw_state_bits=t*max(1,2**t)
        future_bits=len(signatures)*(2**(f.n_vars-t))
        rows.append(dict(family=f.name,n_vars=f.n_vars,stage=t,prefixes=2**t,
                         semantic_classes=nclasses,slw_bits=slw,semantic_rank=rank,
                         accept_prefixes=accept,reject_prefixes=reject,boundary_prefixes=boundary,
                         boundary_fraction=boundary/(2**t),future_table_bits=future_bits,
                         runtime_ms=elapsed,raw_state_bits=raw_state_bits))
    return pd.DataFrame(rows)


def exhaustive_sat(f: CNF) -> tuple[bool,float,int]:
    st=time.perf_counter(); checks=0
    for a in product((0,1),repeat=f.n_vars):
        checks+=1
        if f.evaluate(a):
            return True,(time.perf_counter()-st)*1000,checks
    return False,(time.perf_counter()-st)*1000,checks


def constant_image_barrier(f: CNF) -> dict:
    sat,ms,checks=exhaustive_sat(f)
    return dict(family=f.name,n_vars=f.n_vars,codomain_states=1,image_nonempty=int(sat),
                exhaustive_checks=checks,realizability_ms=ms)


def syntactic_signature(f: CNF) -> dict:
    n=f.n_vars; m=len(f.clauses)
    pos=sum(l>0 for c in f.clauses for l in c)
    neg=sum(l<0 for c in f.clauses for l in c)
    widths=[len(c) for c in f.clauses]
    occ=[0]*n
    for c in f.clauses:
        for l in c: occ[abs(l)-1]+=1
    return dict(n_vars=n,n_clauses=m,horn=int(is_horn(f)),two_sat=int(is_2sat(f)),
                mean_width=sum(widths)/m if m else 0,max_width=max(widths,default=0),
                polarity_balance=abs(pos-neg)/max(1,pos+neg),max_occ=max(occ,default=0),
                mean_occ=sum(occ)/max(1,n))


def representation_hop(f: CNF) -> dict:
    s=syntactic_signature(f)
    if s['horn']:
        route='Horn'; certificate='syntactic Horn check'; tractable=1
    elif s['two_sat']:
        route='2-SAT'; certificate='clause-width check'; tractable=1
    elif f.name.startswith('xor_chain'):
        route='Affine-origin'; certificate='generator provenance'; tractable=1
    elif f.name.startswith('cycle_graph'):
        route='Graph/cardinality'; certificate='bipartite-cycle structure'; tractable=1
    else:
        route='Generic-CNF'; certificate='none'; tractable=0
    return {**s,'family':f.name,'selected_route':route,'certificate':certificate,'certified_tractable':tractable}


def bottleneck_profile(df: pd.DataFrame) -> pd.DataFrame:
    out=df.copy()
    # Operational proxies from exact enumerator; logs keep scales comparable.
    out['E']=np.log2(out['semantic_classes'].clip(lower=1))
    out['R']=np.log2(out['prefixes'].clip(lower=1))
    out['S']=np.log2((out['semantic_classes']**2).clip(lower=1))
    out['T']=np.log2((out['semantic_classes']+out['boundary_prefixes']).clip(lower=1))
    return out



def two_sat_scc(f: CNF) -> tuple[bool,float]:
    """Exact linear-size implication-graph solver for width-at-most-2 CNF."""
    if not is_2sat(f):
        raise ValueError('two_sat_scc requires clauses of width <= 2')
    import networkx as nx
    st=time.perf_counter(); G=nx.DiGraph()
    def node(lit: int): return lit
    for v in range(1,f.n_vars+1):
        G.add_node(v); G.add_node(-v)
    for c in f.clauses:
        if len(c)==0:
            return False,(time.perf_counter()-st)*1000
        if len(c)==1:
            a=c[0]; G.add_edge(-a,a)
        else:
            a,b=c; G.add_edge(-a,b); G.add_edge(-b,a)
    comp={}
    for i,cc in enumerate(nx.strongly_connected_components(G)):
        for v in cc: comp[v]=i
    sat=all(comp[v]!=comp[-v] for v in range(1,f.n_vars+1))
    return sat,(time.perf_counter()-st)*1000


def stage_cost_bound(e:int,q:int,r:int,p:int,s:int,u:int,stages:int=1) -> dict:
    """Evaluate the E/R/S/T accounting identity used by the convergence theorem."""
    vals=[int(x) for x in (e,q,r,p,s,u,stages)]
    if any(x<0 for x in vals): raise ValueError('costs must be nonnegative')
    e,q,r,p,s,u,stages=vals
    per=e+q*r+p*s+u
    return dict(E=e,R_calls=q,R_each=r,S_calls=p,S_each=s,T=u,
                stage_cost=per,stages=stages,total_bound=stages*per)


def same_image_realizability_diagnostic(n_values=(8,10,12,14,16), seed=4400):
    """Natural same-image diagnostic: constant codomain on 2-CNF vs 3-CNF.

    2-CNF nonemptiness is solved by SCC; the selected 3-CNF diagnostic uses exact exhaustive
    search only as an executable baseline. The theorem-level NP-completeness statement relies
    on Schaefer/Cook-Karp, not on these timings.
    """
    from .cnf import contradictory_2cnf, contradictory_3cnf
    rows=[]
    for n in n_values:
        f2=contradictory_2cnf(n)
        sat2,ms2=two_sat_scc(f2)
        f3=contradictory_3cnf(n,seed+n)
        sat3,ms3,checks=exhaustive_sat(f3)
        rows.append(dict(n_vars=n,problem='2-CNF',codomain_states=1,image_nonempty=int(sat2),
                         algorithm='SCC implication graph',checks_or_edges=2*len(f2.clauses),runtime_ms=ms2,
                         complexity='P'))
        rows.append(dict(n_vars=n,problem='3-CNF',codomain_states=1,image_nonempty=int(sat3),
                         algorithm='exhaustive diagnostic',checks_or_edges=checks,runtime_ms=ms3,
                         complexity='NP-complete (image nonemptiness)'))
    return pd.DataFrame(rows)


def audit_completeness_table() -> pd.DataFrame:
    """Formal audit-completeness witnesses for the four terms in C=e+qr+ps+u.

    These rows are accounting witnesses, not complexity lower bounds: omitting a term permits
    that unrecorded term to grow while the displayed retained terms stay fixed.
    """
    return pd.DataFrame([
        ('E','explicit semantic object/materialization','encoding/storage term can dominate','audit-essential'),
        ('R','constant task image with SAT fiber','realizability can carry NP-hard work','audit-essential'),
        ('S','future-equivalence/equivalence certification','separation/certification can dominate','audit-essential'),
        ('T','representation conversion or exact update','transformation/output work can dominate','audit-essential'),
    ],columns=['omitted_channel','witness_pattern','hidden_work','status'])


def channel_ablation_table() -> pd.DataFrame:
    return pd.DataFrame([
        ('Full E/R/S/T','E,R,S,T','complete stage-cost audit within model'),
        ('Remove E','R,S,T','can miss representation/materialization growth'),
        ('Remove R','E,S,T','can misclassify a one-state image with hard nonemptiness'),
        ('Remove S','E,R,T','can miss expensive equivalence/certificate discovery'),
        ('Remove T','E,R,S','can miss conversion/update/composition blow-up'),
    ],columns=['audit','channels_kept','failure_mode'])


def path_normalization_table() -> pd.DataFrame:
    return pd.DataFrame([
        ('TSI','task image','E,R,T'),('SLW','future quotient/retirement','E,S,T'),
        ('ASR','canonical future interface','E,S'),('CSR','certified resolution','S,T'),
        ('RHSR','representation hopping','E,T'),('SBI','symbolic basis image','E,S'),
        ('Fiber','tractable fibers','R,T'),('Dual','accept/reject regions','E,R,T'),
        ('Reverse','falsifying coverage','E,R,T'),('Boundary','unresolved frontier','E,S,T')
    ],columns=['strategy','semantic_object','normal_form'])
