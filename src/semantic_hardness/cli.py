from __future__ import annotations
import argparse, json
from pathlib import Path
from .experiments import run_all
from .cnf import random_3cnf, random_2cnf, cycle_graph_cnf, horn_chain, xor_chain_3cnf, tseitin_cubic_cnf, pigeonhole_3cnf
from .analysis import exact_profile, representation_hop, stage_cost_bound, same_image_realizability_diagnostic


def _make(family,n,seed):
    if family=='random3': return random_3cnf(n,4.2,seed)
    if family=='random2': return random_2cnf(n,2.0,seed)
    if family=='cycle': return cycle_graph_cnf(n)
    if family=='horn': return horn_chain(n)
    if family=='xor': return xor_chain_3cnf(n)
    if family=='php': return pigeonhole_3cnf(3,2)
    nv=max(4,n if n%2==0 else n-1); return tseitin_cubic_cnf(nv,True)


def main():
    p=argparse.ArgumentParser(prog='semantic-hardness',description='Semantic Hardness Conservation reproducibility CLI')
    sub=p.add_subparsers(dest='cmd',required=True)
    r=sub.add_parser('reproduce'); r.add_argument('--out',default='results')
    q=sub.add_parser('profile'); q.add_argument('--family',choices=['random3','random2','cycle','horn','xor','tseitin','php'],default='random3'); q.add_argument('--n',type=int,default=8); q.add_argument('--seed',type=int,default=2026)
    s=sub.add_parser('same-image'); s.add_argument('--max-n',type=int,default=14)
    c=sub.add_parser('bound')
    for name,default in [('e',10),('q',5),('r',20),('p',4),('s',15),('u',30),('stages',10)]: c.add_argument(f'--{name}',type=int,default=default)
    a=p.parse_args()
    if a.cmd=='reproduce': print(json.dumps(run_all(Path(a.out)),indent=2))
    elif a.cmd=='same-image': print(same_image_realizability_diagnostic(tuple(range(6,a.max_n+1,2))).to_string(index=False))
    elif a.cmd=='bound': print(json.dumps(stage_cost_bound(a.e,a.q,a.r,a.p,a.s,a.u,a.stages),indent=2))
    else:
        f=_make(a.family,a.n,a.seed)
        print(exact_profile(f,min(f.n_vars,10)).to_string(index=False)); print('\nRoute:',representation_hop(f))

if __name__=='__main__': main()
