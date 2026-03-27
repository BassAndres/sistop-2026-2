# Santa Claus
# Gonzalez Falcon Luis & Lopez Morales Fernando

import threading
import time
import random

NUM_ELFOS = 5
NUM_RENOS = 9
NUM_BARRERA_ELFOS = 3 #Se ocupa para definir la barrera para los elfos



# tenemos que crear n elfos y 9 renos
#cada elfo tiene un hilo y cada reno tiene un hilo
#usamos una barrera para los elfos y una barrera para los renos

#Contadores para abrir cada barrera
cuentaBarreraElfos = 0
cuentaBarreraRenoss = 0

#Mutex de cada barrera
mutexElfo = threading.Semaphore(1)
mutexReno = threading.Semaphore(1)
mutexSanta = threading.Semaphore(1)

#Barrera de elfos y renos
barreraElfos = threading.Semaphore(0)
barreraRenos = threading.Semaphore(0)  

santaSemaforo = threading.Semaphore(0)




def accionReno(num):
    print(f"Soy el reno {num} y estoy vacacionando :D")


def trabajoElfo(num):
    while True:
        print(f"Soy el elfo {num} y estoy trabajando...")
        numRandom = random.randint(1,100)
        while(numRandom != 10):
            numRandom = random.randint(1,10)
        print(f"Elfo {num} encontre un problema")
        llamadaProblema(num)


#Funcion donde se gestiona la barrera de elfo
def llamadaProblema(num):
    global cuentaBarreraElfos
    mutexElfo.acquire()
    if cuentaBarreraElfos < NUM_BARRERA_ELFOS:
        cuentaBarreraElfos += 1
        print(f"[{num}] me formo para pedir ayuda a santa: {cuentaBarreraElfos} esperando")
        if cuentaBarreraElfos == NUM_BARRERA_ELFOS:
            print("Hablando a Santa porque somos 3")
            santaSemaforo.release()
        mutexElfo.release()
        barreraElfos.acquire()
        print("Los elfos se ponen a trabajar de nuevo")
    else: # Cuando hay 3 elfos, se ponen a trabajar de nuevo
        print("Ya hay 3 elfos actualmente, regresare a trabajar")
        mutexElfo.release()
        time.sleep(0.2)


def santaAyudando():
    global cuentaBarreraElfos
    while True:
        santaSemaforo.acquire() # Se duemre hasta que los elfos lo despierten con santaSemaforo.release
        print("---------------DESPERTE Y Y VOY A AYUDAR-------------")
        barreraElfos.release()
        barreraElfos.release()
        barreraElfos.release()
        time.sleep(0.1)

        #Se resetea
        mutexElfo.acquire()
        cuentaBarreraElfos = 0
        print("---------------VOLVERE A DORMIR --------------------")
        mutexElfo.release()

#Creando hilo Santa Claus
threading.Thread(target=santaAyudando, args=()).start() 

#creando hilos ELFOS
for i in range(NUM_ELFOS):
    threading.Thread(target= trabajoElfo, args=[i]).start()

#Creando hilos renos
for i in range(NUM_RENOS):
    threading.Thread(target= accionReno, args=[i]).start()
    


#creando 
