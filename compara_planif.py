procesos = [('A', 2, 3), ('B', 4, 2)] # Nota: Nadie llega n t=0
t = 0
listos = []

while procesos or listos:
    
    for p in procesos[:]:
        if p[1] == t:
            listos.append(p)
            procesos.remove(p)
    
    if listos:
        actual = listos[0]
        print(f"t={t}: Ejecutando {actual[0]}")
        

        break 
