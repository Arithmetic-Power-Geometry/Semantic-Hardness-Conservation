from pathlib import Path
import pandas as pd
r=Path(__file__).parent/'results'
out=r/'latex_tables'; out.mkdir(exist_ok=True)

def esc(x): return str(x).replace('_','\\_').replace('%','\\%').replace('&','\\&')

def write(name,lines): (out/name).write_text('\n'.join(lines))

s=pd.read_csv(r/'tables/table_exact_summary.csv')
patterns=['cycle_graph_n10','horn_chain_n10','xor_chain_inputs6','php_4_3','tseitin_cubic_v8_odd']
sel=s[s.family.isin(patterns)]
# add one random and one planted n10 deterministically
for key in ['random3_n10','planted3_n10']:
    x=s[s.family.str.startswith(key)].head(1); sel=pd.concat([sel,x])
lines=['\\begin{tabular}{lrrrrr}','\\toprule','Family & $n$ & Max classes & Max SLW & Max rank & Max boundary \\\\','\\midrule']
for _,x in sel.iterrows(): lines.append(f"{esc(x.family)} & {int(x.n_vars)} & {int(x.max_classes)} & {int(x.max_slw)} & {int(x.max_rank)} & {int(x.max_boundary)} \\\\")
lines+=['\\bottomrule','\\end{tabular}']; write('exact_summary.tex',lines)

b=pd.read_csv(r/'tables/table_constant_image_barrier.csv')
lines=['\\begin{tabular}{rrrrr}','\\toprule','$n$ & Codomain & Nonempty & Checks & Time (ms) \\\\','\\midrule']
for _,x in b.iterrows(): lines.append(f"{int(x.n_vars)} & {int(x.codomain_states)} & {int(x.image_nonempty)} & {int(x.exhaustive_checks)} & {x.realizability_ms:.3f} \\\\")
lines+=['\\bottomrule','\\end{tabular}']; write('barrier.tex',lines)

h=pd.read_csv(r/'tables/table_representation_hopping.csv')
sel=h[h.family.isin(patterns)]
for key in ['random3_n10','planted3_n10']:
    sel=pd.concat([sel,h[h.family.str.startswith(key)].head(1)])
lines=['\\begin{tabular}{lrrll}','\\toprule','Family & Clauses & Max width & Route & Certified \\\\','\\midrule']
for _,x in sel.iterrows(): lines.append(f"{esc(x.family)} & {int(x.n_clauses)} & {int(x.max_width)} & {esc(x.selected_route)} & {('Yes' if x.certified_tractable else 'No')} \\\\")
lines+=['\\bottomrule','\\end{tabular}']; write('hopping.tex',lines)

c=pd.read_csv(r/'tables/table_convergence_paths.csv')
lines=['\\begin{tabular}{lll}','\\toprule','Path & Primary semantic object & Normal-form costs \\\\','\\midrule']
for _,x in c.iterrows(): lines.append(f"{esc(x.path)} & {esc(x.primary_object)} & {esc(x.converges_to)} \\\\")
lines+=['\\bottomrule','\\end{tabular}']; write('convergence.tex',lines)

t=pd.read_csv(r/'tables/table_theorem_status.csv')
lines=['\\begin{tabularx}{\\textwidth}{lXl}','\\toprule','Result & Statement & Status \\\\','\\midrule']
for _,x in t.iterrows(): lines.append(f"{esc(x.result)} & {esc(x.statement)} & {esc(x.status)} \\\\")
lines+=['\\bottomrule','\\end{tabularx}']; write('theorem_status.tex',lines)

p=pd.read_csv(r/'tables/table_stage_profiles.csv')
keep=[]
for key in ['cycle_graph_n10','horn_chain_n10','tseitin_cubic_v8_odd']:
    keep.append(p[(p.family==key)&p.stage.isin([0,4,8,10])])
rand=p[p.family.str.startswith('random3_n10')].family.unique()
if len(rand): keep.append(p[(p.family==rand[0])&p.stage.isin([0,4,8,10])])
sel=pd.concat(keep)
lines=['\\begin{tabular}{lrrrrr}','\\toprule','Family & Stage & Classes & SLW & Rank & Boundary frac. \\\\','\\midrule']
for _,x in sel.iterrows(): lines.append(f"{esc(x.family)} & {int(x.stage)} & {int(x.semantic_classes)} & {int(x.slw_bits)} & {int(x.semantic_rank)} & {x.boundary_fraction:.3f} \\\\")
lines+=['\\bottomrule','\\end{tabular}']; write('stage_profiles.tex',lines)

same=pd.read_csv(r/'tables/table_same_image_separation.csv')
lines=['\\begin{tabular}{rlrll}','\\toprule','$n$ & Problem & Codomain & Exact method & Complexity status \\\\','\\midrule']
for _,x in same.iterrows(): lines.append(f"{int(x.n_vars)} & {esc(x.problem)} & {int(x.codomain_states)} & {esc(x.algorithm)} & {esc(x.complexity)} \\\\")
lines+=['\\bottomrule','\\end{tabular}']; write('same_image.tex',lines)

irr=pd.read_csv(r/'tables/table_audit_completeness.csv')
lines=['\\begin{tabularx}{\\textwidth}{lXXl}','\\toprule','Channel & Witness pattern & Hidden work & Status \\\\','\\midrule']
for _,x in irr.iterrows(): lines.append(f"{esc(x.omitted_channel)} & {esc(x.witness_pattern)} & {esc(x.hidden_work)} & {esc(x.status)} \\\\")
lines+=['\\bottomrule','\\end{tabularx}']; write('completeness.tex',lines)

ab=pd.read_csv(r/'tables/table_ablation.csv')
lines=['\\begin{tabularx}{\\textwidth}{llX}','\\toprule','Audit & Channels kept & Failure mode \\\\','\\midrule']
for _,x in ab.iterrows(): lines.append(f"{esc(x.audit)} & {esc(x.channels_kept)} & {esc(x.failure_mode)} \\\\")
lines+=['\\bottomrule','\\end{tabularx}']; write('ablation.tex',lines)

nat=pd.read_csv(r/'tables/table_natural_families.csv').head(12)
lines=['\\begin{tabular}{lrrrr}','\\toprule','Family & $n$ & Max classes & Max SLW & Max rank \\\\','\\midrule']
for _,x in nat.iterrows(): lines.append(f"{esc(x.family)} & {int(x.n_vars)} & {int(x.max_classes)} & {int(x.max_slw)} & {int(x.max_rank)} \\\\")
lines+=['\\bottomrule','\\end{tabular}']; write('natural_families.tex',lines)

print('wrote',len(list(out.glob('*.tex'))),'latex tables')
