#!/usr/bin/env python3

import threading as th
import random
import time

numero_sillas = 10



class Alumno(th.Thread):
	def __init__(self, id, sillas, turno):
		super().__init__()
		self.id = id
		self.silla = sillas
		self.mutex = mutex
		self.numero_dudas = random.randint(1, 10)

	def run(self):
		with self.silla:

			print(f"El alumno {self.id} entró al cubiculo")

			self.resolver_dudas()

		print(f"El alumno {self.id} salió del cubiculo")

	def resolver_dudas(self):
		while self.numero_dudas != 0:
			
			with self.turno:
				
				print(f"El alumno {self.id} está relaizando resolviendo una duda")

				self.numero_dudas -= 1
							
			time.sleep(1)

		print(f"El alumno {self.id} resolvio todas sus dudas") 

class Profesor(th.Thread):
	def __init__(self, condicion):
		super().__init__()
		self.condicion = condicion

	def run(self):
		print("s")		
			
