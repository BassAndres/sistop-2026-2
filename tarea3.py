from dataclasses import dataclass

@dataclass
class Proc:
    n: str
    llegada: int
    total: int
    rest: int
    fin: int = 0

procs = [Proc('A', 0, 3, 3), Proc('B', 1, 2, 2)]
t, q, q_left = 0, 2, 0
listos, ejec = [], None
terminados = []

while procs or listos or ejec:
    llegadas_hoy = sorted([p for p in procs if p.llegada == t], key=lambda x: x.n)
    for p in llegadas_hoy:
        listos.append(p)
        procs.remove(p)
        
    if ejec is None and listos:
        ejec = listos.pop(0)
        q_left = q  # Reseteo correcto
        
    if ejec:
        print(f"t={t}:{ejec.n}", end=" ")
        ejec.rest -= 1
        q_left -= 1
        if ejec.rest == 0:
            ejec.fin = t + 1
            terminados.append(ejec)
            ejec, q_left = None, 0
        elif q_left == 0:
            listos.append(ejec)
            ejec = None
    t += 1

print("\nMétricas:")
for p in terminados:
    T = p.fin - p.llegada
    print(f"Proc {p.n}: T={T}, E={T - p.total}, P={T/p.total:.2f}")
