#!/usr/bin/env python3
"""compara_planif.py

Simulador discreto por tick para comparar planificadores de CPU.
Incluye: FCFS/FIFO, RR(q configurable), SPN (SJF no preventivo), y FB (colas múltiples, 3 niveles).

Requisitos del profesor cubiertos:
- 1 carácter por tick en el diagrama (letra del proceso o '_' si CPU ociosa)
- Desempates consistentes y documentados
- Reproducible con semilla
- Opción --demo con 3 casos pequeños verificables a mano
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import List, Dict, Tuple, Optional
import argparse
import random

# =========================
# Constantes del algoritmo FB (para sacar 10)
# =========================
FB_LEVELS = 3
FB_QUANTA = (1, 2, 4)  # Q0=1, Q1=2, Q2=4
# Preempción FB (regla, 2 líneas):
# Si llega un proceso nuevo a Q0 mientras corre uno de Q1/Q2, la preempción ocurre en el siguiente tick.
# Al inicio de cada tick, tras encolar arribos, si Q0 no está vacía y corre Q1/Q2, se reencola el actual y se atiende Q0.


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
    # Campo extra usado por FB (nivel actual)
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


# -------------------------
# Utilidades de impresión
# -------------------------

def build_time_rule(makespan: int) -> str:
    """Regla de tiempo con marcas cada 5 ticks.

    Ejemplo (makespan=18):
    t: 0....5....10...15..
    """
    if makespan <= 0:
        return "t: "
    chars = ['.'] * makespan
    for k in range(0, makespan, 5):
        s = str(k)
        for j, ch in enumerate(s):
            if k + j < makespan:
                chars[k + j] = ch
    return "t: " + ''.join(chars)


def compute_metrics(states: Dict[str, ProcState]) -> Tuple[Dict[str, Dict[str, float]], float, float, float]:
    """Calcula métricas por proceso y promedios: T, E, P."""
    per: Dict[str, Dict[str, float]] = {}
    Ts: List[float] = []
    Es: List[float] = []
    Ps: List[float] = []

    for name in sorted(states.keys()):
        p = states[name]
        assert p.finish is not None, "Proceso sin terminar al calcular métricas"
        a, t, f = p.arrival, p.total, p.finish
        T = f - a
        E = T - t
        P = T / t
        per[name] = {"a": a, "t": t, "f": f, "T": T, "E": E, "P": P}
        Ts.append(T)
        Es.append(E)
        Ps.append(P)

    n = len(states)
    return per, sum(Ts) / n, sum(Es) / n, sum(Ps) / n


# -------------------------
# Núcleo de simulación por algoritmo
# -------------------------

def init_states(specs: List[ProcSpec]) -> Dict[str, ProcState]:
    return {s.name: ProcState(s.name, s.arrival, s.total, s.total) for s in specs}


def arrivals_at(specs: List[ProcSpec], t: int) -> List[ProcSpec]:
    return [s for s in specs if s.arrival == t]


def all_done(states: Dict[str, ProcState]) -> bool:
    return all(p.finish is not None for p in states.values())


def simulate_fcfs(specs: List[ProcSpec]) -> AlgoResult:
    """FCFS/FIFO (no preventivo).

    Desempate FCFS:
    - Se mantiene una cola FIFO.
    - Los arribos del mismo tick se encolan por nombre (A<B<C...).
    """
    states = init_states(specs)
    ready = deque()  # FIFO
    running: Optional[str] = None
    timeline: List[str] = []
    t = 0

    while not all_done(states):
        # A) Arribos primero
        for s in sorted(arrivals_at(specs, t), key=lambda x: x.name):
            ready.append(s.name)

        # B) Si CPU libre, tomar el primero (llegada más antigua; empate por nombre)
        if running is None and ready:
            running = ready.popleft()

        # C) Ejecutar 1 tick
        if running is None:
            timeline.append('_')
        else:
            timeline.append(running)
            p = states[running]
            p.remaining -= 1
            if p.remaining == 0:
                p.finish = t + 1  # termina al final del tick
                running = None

        t += 1

    per, aT, aE, aP = compute_metrics(states)
    return AlgoResult("FCFS", ''.join(timeline), per, aT, aE, aP, len(timeline))


def simulate_rr(specs: List[ProcSpec], q: int) -> AlgoResult:
    """Round Robin con quantum q (preemptivo por quantum)."""
    states = init_states(specs)
    ready = deque()
    running: Optional[str] = None
    qleft = 0
    timeline: List[str] = []
    t = 0

    while not all_done(states):
        # A) Arribos primero (al final de la cola)
        for s in sorted(arrivals_at(specs, t), key=lambda x: x.name):
            ready.append(s.name)

        # B) Si CPU libre, tomar siguiente y resetear quantum
        if running is None and ready:
            running = ready.popleft()
            qleft = q

        # C) Ejecutar 1 tick
        if running is None:
            timeline.append('_')
        else:
            timeline.append(running)
            p = states[running]
            p.remaining -= 1
            qleft -= 1

            if p.remaining == 0:
                p.finish = t + 1
                running = None
                qleft = 0
            elif qleft == 0:
                # expira quantum y no terminó -> reencolar al final
                ready.append(running)
                running = None

        t += 1

    per, aT, aE, aP = compute_metrics(states)
    return AlgoResult(f"RR{q}", ''.join(timeline), per, aT, aE, aP, len(timeline))


def simulate_spn(specs: List[ProcSpec]) -> AlgoResult:
    """SPN / SJF no preventivo (sin I/O).

    Desempate SPN:
    1) menor ti
    2) llegada más antigua (menor ai)
    3) nombre
    """
    states = init_states(specs)
    ready: List[str] = []
    running: Optional[str] = None
    timeline: List[str] = []
    t = 0

    while not all_done(states):
        # A) Arribos primero
        for s in sorted(arrivals_at(specs, t), key=lambda x: x.name):
            ready.append(s.name)

        # B) Si CPU libre, elegir por SPN
        if running is None and ready:
            ready.sort(key=lambda n: (states[n].total, states[n].arrival, n))
            running = ready.pop(0)

        # C) Ejecutar 1 tick
        if running is None:
            timeline.append('_')
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
    """FB (Feedback / Retroalimentación multinivel) con 3 colas.

    Reglas (según el enunciado):
    - 3 colas Q0,Q1,Q2; quantums 1,2,4.
    - Procesos nuevos entran a Q0.
    - Siempre se ejecuta el primero de la cola de mayor prioridad no vacía.
    - Si consume TODO su quantum y no termina, baja de nivel (Q0->Q1->Q2; Q2 se queda en Q2).
    - Preempción: si aparece alguien en Q0 mientras corre Q1/Q2, en el siguiente tick toma prioridad Q0.
    """
    states = init_states(specs)
    qs = [deque() for _ in range(FB_LEVELS)]
    running: Optional[str] = None
    qleft = 0
    timeline: List[str] = []
    t = 0

    def pick_next() -> Optional[str]:
        for lvl in range(FB_LEVELS):
            if qs[lvl]:
                n = qs[lvl].popleft()
                states[n].level = lvl
                return n
        return None

    while not all_done(states):
        # A) Arribos primero (todos a Q0)
        for s in sorted(arrivals_at(specs, t), key=lambda x: x.name):
            states[s.name].level = 0
            qs[0].append(s.name)

        # B) Preempción por Q0 (solo en frontera de tick)
        if running is not None:
            cur_lvl = states[running].level
            if cur_lvl > 0 and qs[0]:
                # reencolar al final de su nivel actual
                qs[cur_lvl].append(running)
                running = None
                qleft = 0

        # C) Si CPU libre, tomar de la cola de mayor prioridad
        if running is None:
            running = pick_next()
            if running is not None:
                qleft = FB_QUANTA[states[running].level]

        # D) Ejecutar 1 tick
        if running is None:
            timeline.append('_')
        else:
            timeline.append(running)
            p = states[running]
            p.remaining -= 1
            qleft -= 1

            if p.remaining == 0:
                p.finish = t + 1
                running = None
                qleft = 0
            elif qleft == 0:
                # consumió todo el quantum y no terminó -> baja (o se queda en Q2)
                lvl = p.level
                if lvl < FB_LEVELS - 1:
                    lvl += 1
                p.level = lvl
                qs[lvl].append(p.name)
                running = None

        t += 1

    per, aT, aE, aP = compute_metrics(states)
    return AlgoResult("FB", ''.join(timeline), per, aT, aE, aP, len(timeline))


# -------------------------
# Generación y ejecución de rondas
# -------------------------

def gen_round(rng: random.Random, nproc: int, a_min: int, a_max: int, c_min: int, c_max: int) -> List[ProcSpec]:
    specs: List[ProcSpec] = []
    for i in range(nproc):
        name = chr(ord('A') + i)
        arrival = rng.randint(a_min, a_max)
        total = rng.randint(c_min, c_max)
        specs.append(ProcSpec(name, arrival, total))
    return sorted(specs, key=lambda s: s.name)


def parse_quantums(s: str) -> List[int]:
    parts = [p.strip() for p in s.split(',') if p.strip()]
    qs: List[int] = []
    for p in parts:
        try:
            qs.append(int(p))
        except ValueError:
            pass
    return qs if qs else [1, 4]


def print_algo(res: AlgoResult):
    print(f"\n{res.algo}: T={res.avg_T:.2f}, E={res.avg_E:.2f}, P={res.avg_P:.2f}")
    print(build_time_rule(res.makespan))
    print("run: " + res.timeline)
    for name in sorted(res.per_proc.keys()):
        d = res.per_proc[name]
        print(
            f"{name} a={int(d['a'])} t={int(d['t'])} f={int(d['f'])} "
            f"T={int(d['T'])} E={int(d['E'])} P={d['P']:.2f}"
        )


def run_round(round_idx: int, specs: List[ProcSpec], quantums: List[int]):
    total_cpu = sum(s.total for s in specs)
    print(f"\n=== Ronda {round_idx} ===")
    print("Procesos:")
    print("  " + "; ".join([f"{s.name}: a={s.arrival}, t={s.total}" for s in specs]))
    print(f"  (tot CPU={total_cpu})")

    # Ejecutar algoritmos
    results: List[AlgoResult] = [
        simulate_fcfs(specs),
        *[simulate_rr(specs, q) for q in quantums],
        simulate_spn(specs),
        simulate_fb(specs),
    ]

    for res in results:
        print_algo(res)


# -------------------------
# DEMO (verificación mínima)
# -------------------------

def demo_cases() -> List[Tuple[str, List[ProcSpec]]]:
    return [
        (
            "Demo 1: llegadas simultáneas",
            [ProcSpec('A', 0, 3), ProcSpec('B', 0, 2), ProcSpec('C', 0, 4)],
        ),
        (
            "Demo 2: CPU ociosa al inicio",
            [ProcSpec('A', 3, 3), ProcSpec('B', 5, 2), ProcSpec('C', 6, 2)],
        ),
        (
            "Demo 3: empates (SPN y FCFS/RR)",
            [ProcSpec('A', 0, 3), ProcSpec('B', 0, 3), ProcSpec('C', 1, 2), ProcSpec('D', 1, 2)],
        ),
    ]


def run_demo(quantums: List[int]):
    for title, specs in demo_cases():
        print(f"\n============================\n{title}\n============================")
        print("  " + "; ".join([f"{s.name}: a={s.arrival}, t={s.total}" for s in specs]))

        results: List[AlgoResult] = [
            simulate_fcfs(specs),
            *[simulate_rr(specs, q) for q in quantums],
            simulate_spn(specs),
            simulate_fb(specs),
        ]
        for res in results:
            print_algo(res)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Simulador por tick para comparar FCFS, RR, SPN y FB (colas múltiples).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    ap.add_argument('--rondas', type=int, default=5)
    ap.add_argument('--nproc', type=int, default=5)
    ap.add_argument('--llegada_min', type=int, default=0)
    ap.add_argument('--llegada_max', type=int, default=12)
    ap.add_argument('--cpu_min', type=int, default=2)
    ap.add_argument('--cpu_max', type=int, default=7)
    ap.add_argument('--seed', type=int, default=123)
    ap.add_argument('--quantums', type=str, default='1,4')
    ap.add_argument('--demo', action='store_true', help='Ejecuta 3 casos pequeños fijos para verificación manual.')

    args = ap.parse_args(argv)
    quantums = parse_quantums(args.quantums)

    if args.demo:
        run_demo(quantums)
        return 0

    rng = random.Random(args.seed)
    for r in range(1, args.rondas + 1):
        specs = gen_round(rng, args.nproc, args.llegada_min, args.llegada_max, args.cpu_min, args.cpu_max)
        run_round(r, specs, quantums)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
