from __future__ import annotations
from dataclasses import dataclass
from itertools import product
import random

Literal = int
Clause = tuple[Literal, ...]

@dataclass(frozen=True)
class CNF:
    n_vars: int
    clauses: tuple[Clause, ...]
    name: str = "cnf"

    def evaluate(self, assignment: tuple[int, ...]) -> bool:
        return all(any((assignment[abs(l)-1] == 1) if l > 0 else (assignment[abs(l)-1] == 0) for l in c) for c in self.clauses)

    def residual_status(self, prefix: tuple[int, ...]) -> int:
        """Return 1 if all completions satisfy, -1 if none satisfy, 0 otherwise."""
        vals=[]
        for suffix in product((0,1), repeat=self.n_vars-len(prefix)):
            vals.append(self.evaluate(prefix+suffix))
            if any(vals) and not all(vals):
                return 0
        return 1 if vals and all(vals) else -1

    def truth_row(self, prefix: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(int(self.evaluate(prefix+s)) for s in product((0,1), repeat=self.n_vars-len(prefix)))


def random_3cnf(n: int, ratio: float = 4.2, seed: int = 0) -> CNF:
    rng=random.Random(seed)
    m=max(1, int(round(ratio*n)))
    clauses=[]
    for _ in range(m):
        vars_=rng.sample(range(1,n+1), k=min(3,n))
        clause=tuple(v if rng.random()<0.5 else -v for v in vars_)
        clauses.append(clause)
    return CNF(n, tuple(clauses), f"random3_n{n}_s{seed}")


def planted_3cnf(n: int, ratio: float = 4.2, seed: int = 0) -> CNF:
    rng=random.Random(seed)
    planted=tuple(rng.randint(0,1) for _ in range(n))
    m=max(1,int(round(ratio*n)))
    clauses=[]
    for _ in range(m):
        vars_=rng.sample(range(1,n+1), k=min(3,n))
        lits=[]
        for v in vars_:
            lits.append(v if rng.random()<0.5 else -v)
        if not any((planted[abs(l)-1]==1 if l>0 else planted[abs(l)-1]==0) for l in lits):
            v=vars_[0]
            lits[0]=v if planted[v-1] else -v
        clauses.append(tuple(lits))
    return CNF(n, tuple(clauses), f"planted3_n{n}_s{seed}")


def cycle_graph_cnf(n: int) -> CNF:
    clauses=[]
    for i in range(1,n+1):
        j=1 if i==n else i+1
        clauses.append((i,j))
    return CNF(n, tuple(clauses), f"cycle_graph_n{n}")


def horn_chain(n: int) -> CNF:
    clauses=[(1,)]
    for i in range(1,n):
        clauses.append((-i,i+1))
    return CNF(n, tuple(clauses), f"horn_chain_n{n}")


def xor_chain_3cnf(n_inputs: int) -> CNF:
    """Encode XOR of input variables into auxiliary chain and force final parity=1."""
    if n_inputs < 2:
        return CNF(1, ((1,),), "xor_chain_n1")
    clauses=[]
    next_var=n_inputs+1
    a=1; b=2; z=next_var; next_var+=1
    def add_xor(x,y,z):
        clauses.extend(((-x,-y,-z),(x,y,-z),(x,-y,z),(-x,y,z)))
    add_xor(a,b,z)
    acc=z
    for x in range(3,n_inputs+1):
        z=next_var; next_var+=1
        add_xor(acc,x,z); acc=z
    clauses.append((acc,))
    return CNF(next_var-1, tuple(clauses), f"xor_chain_inputs{n_inputs}")


def pigeonhole_3cnf(pigeons: int, holes: int) -> CNF:
    """Small CNF encoding; at-least-one clauses are split to width <=3 with Tseitin chain."""
    assert pigeons>holes>=1
    var=lambda p,h: p*holes+h+1
    clauses=[]
    next_var=pigeons*holes+1
    for p in range(pigeons):
        xs=[var(p,h) for h in range(holes)]
        if len(xs)<=3:
            clauses.append(tuple(xs))
        else:
            # equisatisfiable 3-CNF chain for OR(xs)
            y=next_var; next_var+=1
            clauses.append((xs[0],xs[1],y))
            for idx in range(2,len(xs)-2):
                y2=next_var; next_var+=1
                clauses.append((-y,xs[idx],y2)); y=y2
            clauses.append((-y,xs[-2],xs[-1]))
    for h in range(holes):
        for p in range(pigeons):
            for q in range(p+1,pigeons):
                clauses.append((-var(p,h),-var(q,h)))
    return CNF(next_var-1, tuple(clauses), f"php_{pigeons}_{holes}")



def random_2cnf(n: int, ratio: float = 2.0, seed: int = 0) -> CNF:
    """Deterministic seeded random 2-CNF generator for controlled diagnostics."""
    rng=random.Random(seed)
    m=max(1, int(round(ratio*n)))
    clauses=[]
    for _ in range(m):
        vars_=rng.sample(range(1,n+1), k=min(2,n))
        clauses.append(tuple(v if rng.random()<0.5 else -v for v in vars_))
    return CNF(n, tuple(clauses), f"random2_n{n}_s{seed}")


def contradictory_2cnf(n: int) -> CNF:
    """Unsatisfiable 2-CNF with nontrivial extra implications."""
    clauses=[(1,),(-1,)]
    for i in range(1,n):
        clauses.append((-i,i+1))
    return CNF(n, tuple(clauses), f"contradictory2_n{n}")


def contradictory_3cnf(n: int, seed: int = 0) -> CNF:
    """Unsatisfiable width-at-most-3 CNF: an explicit contradiction plus seeded 3-clauses."""
    f=random_3cnf(n, 3.0, seed)
    return CNF(n, ((1,),(-1,))+f.clauses, f"contradictory3_n{n}_s{seed}")


def tseitin_cubic_cnf(n_vertices: int, odd_charge: bool = True) -> CNF:
    """Tseitin parity CNF on a connected cubic graph.

    The graph is a cycle plus an opposite perfect matching (even n>=4). Each edge is a
    Boolean variable. At every vertex, the XOR of its three incident edges equals the
    vertex charge. With an odd total charge the system is inconsistent.
    """
    if n_vertices < 4 or n_vertices % 2:
        raise ValueError('n_vertices must be even and at least 4')
    edges=set()
    for i in range(n_vertices):
        a,b=sorted((i,(i+1)%n_vertices)); edges.add((a,b))
    half=n_vertices//2
    for i in range(half):
        a,b=sorted((i,i+half)); edges.add((a,b))
    edges=sorted(edges)
    edge_var={e:i+1 for i,e in enumerate(edges)}
    inc=[[] for _ in range(n_vertices)]
    for e,v in edge_var.items():
        a,b=e; inc[a].append(v); inc[b].append(v)
    if not all(len(xs)==3 for xs in inc):
        raise AssertionError('construction must be cubic')
    charges=[0]*n_vertices
    if odd_charge: charges[0]=1
    clauses=[]
    for v,xs in enumerate(inc):
        target=charges[v]
        # Exclude assignments whose parity disagrees with target.
        for bits in product((0,1), repeat=3):
            if (sum(bits)&1) != target:
                clauses.append(tuple(var if bit==0 else -var for var,bit in zip(xs,bits)))
    tag='odd' if odd_charge else 'even'
    return CNF(len(edges), tuple(clauses), f"tseitin_cubic_v{n_vertices}_{tag}")


def is_horn(f: CNF) -> bool:
    return all(sum(1 for l in c if l>0)<=1 for c in f.clauses)

def is_2sat(f: CNF) -> bool:
    return all(len(c)<=2 for c in f.clauses)
