```python
#!/usr/bin/env python3
"""
compara_planif.py
Simulador por tick para FCFS, RR, SPN y FB (3 niveles:D).
"""

from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import List, Dict, Tuple, Optional
import argparse
import random

FB_LEVELS = 2
FB_QUANTA = (1, 2, 4)

@dataclass(frozen=True)
class ProcSpec:
    name: str
    arrival: int
    total: int

@dataclass
class ProcState:
    name: str
    arrival: int
    total: int
    remaining: int
    finish: Optional[int] = None
    level: int = 0

@dataclass
class AlgoResult:
    algo: str
    timeline: str
    per_proc: Dict[str, Dict[str, float]]
    avg_T: float
    avg_E: float
    avg_P: float
    makespan: int

def build_time_rule(makespan: int) -> str:
    if makespan <= 0: return "t: "
    chars = ['.'] * makespan
    for k in range(0, makespan, 5):
        s = str(k)
        for j, ch in enumerate(s):
            if k + j < makespan: chars[k + j] = ch
    return "t: " + ''.join(chars)

def compute_metrics(states: Dict[str, ProcState]) -> Tuple[Dict[str, Dict[str, float]], float, float, float]:
    per, Ts, Es, Ps = {}, [], [], []
    for name in sorted(states.keys()):
        p = states[name]
        a, t, f = p.arrival, p.total, p.finish
        T = f - a
        E = T - t
        P = T / t
        per[name] = {"a": a, "t": t, "f": f, "T": T, "E": E, "P": P}
        Ts.append(T); Es.append(E); Ps.append(P)
    n = len(states)
    return per, sum(Ts)/n, sum(Es)/n, sum(Ps)/n

def init_states(specs: List[ProcSpec]) -> Dict[str, ProcState]:
    return {s.name: ProcState(s.name, s.arrival, s.total, s.total) for s in specs}

def arrivals_at(specs: List[ProcSpec], t: int) -> List[ProcSpec]:
    return [s for s in specs if s.arrival == t]

def all_done(states: Dict[str, ProcState]) -> bool:
    return all(p.finish is not None for p in states.values())

def simulate_fcfs(specs: List[ProcSpec]) -> AlgoResult:
    states, ready, running, timeline, t = init_states(specs), deque(), None, [], 0
    while not all_done(states):
        for s in sorted(arrivals_at(specs, t), key=lambda x: x.name):
            ready.append(s.name)
        if running is None and ready:
            running = ready.popleft()
        if running is None: timeline.append('_')
        else:
            timeline.append(running)
            p = states[running]
            p.remaining -= 1
            if p.remaining == 0:
                p.finish = t + 1
                running = None
        t += 1
    per, aT, aE, aP = compute_metrics(states)
    return AlgoResult("FCFS", ''.join(timeline), per, aT, aE, aP, len(timeline))

def simulate_rr(specs: List[ProcSpec], q: int) -> AlgoResult:
    states, ready, running, qleft, timeline, t = init_states(specs), deque(), None, 0, [], 0
    while not all_done(states):
        for s in sorted(arrivals_at(specs, t), key=lambda x: x.name):
            ready.append(s.name)
        if running is None and ready:
            running = ready.popleft()
            qleft = q
        if running is None: timeline.append('_')
        else:
            timeline.append(running)
            p = states[running]
            p.remaining -= 1
            qleft -= 1
            if p.remaining == 0:
                p.finish = t + 1
                running, qleft = None, 0
            elif qleft == 0:
                ready.append(running)
                running = None
        t += 1
    per, aT, aE, aP = compute_metrics(states)
    return AlgoResult(f"RR{q}", ''.join(timeline), per, aT, aE, aP, len(timeline))

def simulate_spn(specs: List[ProcSpec]) -> AlgoResult:
    states, ready, running, timeline, t = init_states(specs), [], None, [], 0
    while not all_done(states):
        for s in sorted(arrivals_at(specs, t), key=lambda x: x.name):
            ready.append(s.name)
        if running is None and ready:
            ready.sort(key=lambda n: (states[n].total, states[n].arrival, n))
            running = ready.pop(0)
        if running is None: timeline.append('_')
        else:
            timeline.append(running)
            p = states[running]
            p.remaining -= 1
            if p.remaining == 0:
                p.finish = t + 1
                running = None
        t += 1
    per, aT, aE, aP = compute_metrics(states)
    return AlgoResult("SPN", ''.join(timeline), per, aT, aE, aP, len(timeline))

def simulate_fb(specs: List[ProcSpec]) -> AlgoResult:
    states, qs, running, qleft, timeline, t = init_states(specs), [deque() for _ in range(FB_LEVELS)], None, 0, [], 0
    def pick_next():
        for lvl in range(FB_LEVELS):
            if qs[lvl]:
                n = qs[lvl].popleft()
                states[n].level = lvl
                return n
        return None
    while not all_done(states):
        for s in sorted(arrivals_at(specs, t), key=lambda x: x.name):
            states[s.name].level = 0
            qs[0].append(s.name)
        if running is not None and states[running].level > 0 and qs[0]:
            qs[states[running].level].append(running)
            running, qleft = None, 0
        if running is None:
            running = pick_next()
            if running: qleft = FB_QUANTA[states[running].level]
        if running is None: timeline.append('_')
        else:
            timeline.append(running)
            p = states[running]
            p.remaining -= 1
            qleft -= 1
            if p.remaining == 0:
                p.finish = t + 1
                running, qleft = None, 0
            elif qleft == 0:
                p.level = min(p.level + 1, FB_LEVELS - 1)
                qs[p.level].append(p.name)
                running = None
        t += 1
    per, aT, aE, aP = compute_metrics(states)
    return AlgoResult("FB", ''.join(timeline), per, aT, aE, aP, len(timeline))

def print_algo(res: AlgoResult):
    print(f"\n{res.algo}: T={res.avg_T:.2f}, E={res.avg_E:.2f}, P={res.avg_P:.2f}")
    print(build_time_rule(res.makespan))
    print("run: " + res.timeline)
    for name in sorted(res.per_proc.keys()):
        d = res.per_proc[name]
        print(f"{name} a={int(d['a'])} t={int(d['t'])} f={int(d['f'])} T={int(d['T'])} E={int(d['E'])} P={d['P']:.2f}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rondas', type=int, default=5)
    ap.add_argument('--nproc', type=int, default=5)
    ap.add_argument('--seed', type=int, default=123)
    ap.add_argument('--quantums', type=str, default='1,4')
    ap.add_argument('--demo', action='store_true')
    args = ap.parse_args()
    qs = [int(x) for x in args.quantums.split(',')]
    
    if args.demo:
        cases = [("Simultáneos", [ProcSpec('A',0,3), ProcSpec('B',0,2)]), ("Ocioso", [ProcSpec('A',2,2)])]
        for title, specs in cases:
            print(f"\n--- {title} ---")
            for r in [simulate_fcfs(specs), simulate_fb(specs)]: print_algo(r)
        return

    rng = random.Random(args.seed)
    for r in range(1, args.rondas + 1):
        specs = sorted([ProcSpec(chr(65+i), rng.randint(0,12), rng.randint(2,7)) for i in range(args.nproc)], key=lambda x: x.name)
        print(f"\n=== Ronda {r} ===")
        algos = [simulate_fcfs(specs), *[simulate_rr(specs, q) for q in qs], simulate_spn(specs), simulate_fb(specs)]
        for res in algos: print_algo(res)

if __name__ == '__main__':
    main()
