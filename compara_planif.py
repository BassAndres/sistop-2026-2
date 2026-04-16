procesos = [('A', 0, 3), ('B', 1, 2), ('C', 2, 1)]
tiempo_actual = 0

print("Simulación FCFS Básica:")
for nombre, llegada, total in procesos:
    if tiempo_actual < llegada:
        tiempo_actual = llegada  # Avanza el tiempo si hay espera
    print(f"t={tiempo_actual}: Inicia {nombre}")
    tiempo_actual += total
    print(f"t={tiempo_actual}: Termina {nombre}")
