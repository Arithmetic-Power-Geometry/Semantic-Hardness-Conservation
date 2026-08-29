import os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','src'))
from semantic_hardness.cnf import *
from semantic_hardness.analysis import *


def test_cycle_sat(): assert exhaustive_sat(cycle_graph_cnf(4))[0]
def test_horn_detect(): assert is_horn(horn_chain(6))
def test_cycle_2sat(): assert is_2sat(cycle_graph_cnf(6))
def test_random_2sat_width(): assert all(len(c)<=2 for c in random_2cnf(8).clauses)
def test_random_width(): assert all(len(c)<=3 for c in random_3cnf(8).clauses)
def test_planted_sat(): assert exhaustive_sat(planted_3cnf(7,3.5,3))[0]
def test_xor_encoding_sat(): assert exhaustive_sat(xor_chain_3cnf(4))[0]
def test_php_unsat(): assert not exhaustive_sat(pigeonhole_3cnf(3,2))[0]
def test_tseitin_odd_unsat(): assert not exhaustive_sat(tseitin_cubic_cnf(4,True))[0]
def test_tseitin_even_sat(): assert exhaustive_sat(tseitin_cubic_cnf(4,False))[0]
def test_profile_stage_zero():
    d=exact_profile(horn_chain(4)); assert int(d.iloc[0].prefixes)==1
def test_slw_nonnegative(): assert (exact_profile(cycle_graph_cnf(4)).slw_bits>=0).all()
def test_rank_bound():
    d=exact_profile(random_3cnf(5,3,1)); assert (d.semantic_rank>=d.slw_bits).all()
def test_boundary_partition():
    d=exact_profile(random_3cnf(5,3,2)); assert ((d.accept_prefixes+d.reject_prefixes+d.boundary_prefixes)==d.prefixes).all()
def test_constant_image(): assert constant_image_barrier(horn_chain(4))['codomain_states']==1
def test_route_horn(): assert representation_hop(horn_chain(5))['certified_tractable']==1
def test_route_generic(): assert representation_hop(random_3cnf(6,4.2,9))['selected_route'] in {'Generic-CNF','Horn','2-SAT'}
def test_two_sat_solver_unsat(): assert not two_sat_scc(contradictory_2cnf(8))[0]
def test_two_sat_solver_matches_exhaustive():
    f=random_2cnf(7,2.1,99); assert two_sat_scc(f)[0] == exhaustive_sat(f)[0]
def test_stage_cost_identity():
    d=stage_cost_bound(3,4,5,6,7,8,9); assert d['stage_cost']==3+4*5+6*7+8 and d['total_bound']==9*d['stage_cost']
def test_same_image_diagnostic():
    d=same_image_realizability_diagnostic((6,)); assert set(d.codomain_states)=={1} and set(d.problem)=={'2-CNF','3-CNF'}
def test_audit_completeness_rows(): assert set(audit_completeness_table().omitted_channel)=={'E','R','S','T'}
def test_ablation_rows(): assert len(channel_ablation_table())==5
def test_normalization_paths(): assert {'TSI','SLW','RHSR','Boundary'} <= set(path_normalization_table().strategy)
