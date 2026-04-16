class Proceso:
    def __init__(self, n, l, t):
        self.n, self.l, self.r = n, l, t

procesos = [Proceso('A', 0, 3), Proceso('B', 1, 2)]
t = 0
listos = []
ejecutando = None
quantum = 2
q_restante = 0

while procesos or listos or ejecutando:
    for p in procesos[:]:
        if p.l == t:
            listos.append(p)
            procesos.remove(p)
            
    if ejecutando is None and listos:
        ejecutando = listos.pop(0)
        q_restante = quantum 
        
    if ejecutando:
        print(f"t={t}: {ejecutando.n}")
        ejecutando.r -= 1
        q_restante -= 1
        if ejecutando.r == 0:
            ejecutando = None
        elif q_restante == 0:
            listos.append(ejecutando)
            ejecutando = None
    t += 1
