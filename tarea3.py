procesos = [{'id': 'A', 'llegada': 2, 'rafaga': 3}, {'id': 'B', 'llegada': 4, 'rafaga': 2}]
t = 0
listos = []
ejecutando = None
while procesos or listos or ejecutando:
    # Llegan procesos
    for p in procesos[:]:
        if p['llegada'] == t:
            listos.append(p)
            procesos.remove(p)
            
    if ejecutando is None and listos:
        ejecutando = listos.pop(0)
        
    if ejecutando is None:
        print(f"t={t}: [Ocioso]")
    else:
        print(f"t={t}: Ejecuta {ejecutando['id']}")
        ejecutando['rafaga'] -= 1
        if ejecutando['rafaga'] == 0:
            ejecutando = None
    t += 1
