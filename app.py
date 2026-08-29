from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'src'))
import gradio as gr
from semantic_hardness.cnf import (
    random_3cnf, planted_3cnf, cycle_graph_cnf, horn_chain,
    xor_chain_3cnf, pigeonhole_3cnf, tseitin_cubic_cnf, random_2cnf
)
from semantic_hardness.analysis import (
    exact_profile, bottleneck_profile, representation_hop, stage_cost_bound,
    same_image_realizability_diagnostic, channel_ablation_table,
    audit_completeness_table, path_normalization_table
)


def make(family,n,ratio,seed):
    n=int(n); seed=int(seed)
    if family=='Random 3-CNF': return random_3cnf(n,float(ratio),seed)
    if family=='Planted 3-CNF': return planted_3cnf(n,float(ratio),seed)
    if family=='Random 2-CNF': return random_2cnf(n,float(ratio),seed)
    if family=='Cycle graph CNF': return cycle_graph_cnf(n)
    if family=='Horn chain': return horn_chain(n)
    if family=='Pigeonhole 3->2': return pigeonhole_3cnf(3,2)
    if family=='Tseitin cubic':
        nv=max(4,n if n%2==0 else n-1)
        return tseitin_cubic_cnf(nv,True)
    return xor_chain_3cnf(max(2,n))


def profile(family,n,ratio,seed):
    f=make(family,n,ratio,seed)
    return exact_profile(f,min(f.n_vars,10))

def spectrum(family,n,ratio,seed):
    return bottleneck_profile(profile(family,n,ratio,seed))[['stage','E','R','S','T','semantic_classes','boundary_fraction']]

def boundary(family,n,ratio,seed):
    return profile(family,n,ratio,seed)[['stage','accept_prefixes','reject_prefixes','boundary_prefixes','boundary_fraction']]

def hop(family,n,ratio,seed): return representation_hop(make(family,n,ratio,seed))
def same_image(max_n):
    vals=tuple(range(6,int(max_n)+1,2)); return same_image_realizability_diagnostic(vals or (6,))
def cost(e,q,r,p,s,u,stages): return stage_cost_bound(e,q,r,p,s,u,stages)

with gr.Blocks(title='Semantic Hardness Conservation Lab') as demo:
    gr.Markdown('# Semantic Hardness Conservation Lab\nExact finite diagnostics for the E/R/S/T theory. The application **does not** claim a polynomial-time solver for arbitrary 3-SAT.')
    with gr.Row():
        family=gr.Dropdown(['Random 3-CNF','Planted 3-CNF','Random 2-CNF','Cycle graph CNF','Horn chain','XOR chain','Pigeonhole 3->2','Tseitin cubic'],value='Random 3-CNF',label='Formula family')
        n=gr.Slider(4,12,value=8,step=1,label='Size parameter')
        ratio=gr.Slider(1.0,6.0,value=4.2,step=.1,label='Clause ratio')
        seed=gr.Number(value=2026,precision=0,label='Seed')
    with gr.Tab('Exact quotient'):
        b=gr.Button('Compute exact profile'); out=gr.Dataframe(); b.click(profile,[family,n,ratio,seed],out)
    with gr.Tab('E/R/S/T spectrum'):
        b2=gr.Button('Compute spectrum'); out2=gr.Dataframe(); b2.click(spectrum,[family,n,ratio,seed],out2)
    with gr.Tab('Reverse boundary'):
        b3=gr.Button('Compute boundary'); out3=gr.Dataframe(); b3.click(boundary,[family,n,ratio,seed],out3)
    with gr.Tab('Representation route'):
        b4=gr.Button('Inspect certified route'); out4=gr.JSON(); b4.click(hop,[family,n,ratio,seed],out4)
    with gr.Tab('Same-image separation'):
        maxn=gr.Slider(6,18,value=14,step=2,label='Maximum variables')
        b5=gr.Button('Compare 2-CNF vs 3-CNF'); out5=gr.Dataframe(); b5.click(same_image,[maxn],out5)
    with gr.Tab('Convergence and ablation'):
        gr.Markdown('These tables expose which semantic paths normalize to E/R/S/T and what an audit misses when one channel is omitted.')
        b6=gr.Button('Show convergence'); out6=gr.Dataframe(); b6.click(lambda:path_normalization_table(),None,out6)
        b7=gr.Button('Show channel ablation'); out7=gr.Dataframe(); b7.click(lambda:channel_ablation_table(),None,out7)
        b8=gr.Button('Show audit-completeness witnesses'); out8=gr.Dataframe(); b8.click(lambda:audit_completeness_table(),None,out8)
    with gr.Tab('Runtime-bound calculator'):
        with gr.Row():
            e=gr.Number(10,label='E: encoding work'); q=gr.Number(5,label='R calls'); r=gr.Number(20,label='R cost/call')
            p=gr.Number(4,label='S calls'); s=gr.Number(15,label='S cost/call'); u=gr.Number(30,label='T work'); stages=gr.Number(10,label='Stages')
        b9=gr.Button('Evaluate theorem bound'); out9=gr.JSON(); b9.click(cost,[e,q,r,p,s,u,stages],out9)

if __name__=='__main__':
    demo.launch()
