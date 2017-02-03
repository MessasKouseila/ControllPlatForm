#!/usr/bin/python3
import psutil

# recupere des informations concernant le processeur
def info_cpu():
	print('Nombre de processeur physique : {0}'.format(psutil.cpu_count(logical=False)))
	print('Nombre de processeur logique : {0}'.format(psutil.cpu_count(logical=True)))
	print('Utilisation moyenne des cpu : {0}'.format(psutil.cpu_percent(interval=1)))
# recupere des informations concernant la ram	
def info_ram():
	info = psutil.virtual_memory()
	ram_total = float(info[0]) / (1024*1024*1024)
	ram_total = round(ram_total, 2)
	print('Quantite de RAM totale (Go): {0}'.format(ram_total))
	print('Quantite de RAM utilise (%): {0}'.format(info[2]))
def info_disk():
	info = psutil.disk_usage('/')
	disk_total = float(info[0]) / (1024*1024*1024)
	disk_total = round(disk_total, 2)
	disk_usage = info[3]	
	print('Capacite partition racine (Go): {0}'.format(disk_total))
	print('Capacite partition racine utilise (%): {0}'.format(info[3]))
# appelle aux fonctions
info_cpu()
info_ram()
info_disk()