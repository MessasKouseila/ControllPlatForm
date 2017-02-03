#/usr/bin/env python3
import datetime
import os
import sys
import time
import subprocess
import requests
from uuid import getnode as get_mac

def teste_connexion():
	methods = 'connexion_server'
	url = adresse + methods
	r = requests.post(url, data = None)
	return r.status_code < 400

file_rep = os.getcwd()
file_id_admin = file_rep + "/id_admin"

file_configuration = file_rep + "/configuration"
# on recupere l'address sur server depuis le fichier de configuration
fichier = open(file_configuration, "r")
contenu = fichier.read()
contenu = contenu.split("\n")
fichier.close()
# on recupere l'id de l'administrateur
fichier = open(file_id_admin, "r")
contenu_1 = fichier.read()
contenu_1 = contenu_1.split(":")
fichier.close()

id_administrator = contenu_1[0]
adresse = contenu[0]
port = contenu[1]
adresse = 'http://' + adresse + ':' + port + '/'

# ce scripte permet de lancer les sondes, 
# de recupere les donnees collecter par les sondes 
# puis de les envoyer au serveurs pour les inserer dans la badd
try:
	if teste_connexion():
		try:
			print("=======>>> mise en marche des sondes <<<=======")
			# on lance un scripte qui lui meme lance les sondes puis recupere les donnees collecter dans un fichier
			# une fois les donnees recolter sont inserer dans le fichier file_server_, on utilise grep pour extraire uniquement les infos interessantes
			# les donnees interessantes sont a nouveau inserer dans un fichier nome info_sonde
			f1 = "file_temp.sh"
			subprocess.check_output(['bash', f1])
			try:
				# on ouvre le fichier contenant les donnees a inserer
				fichier = open("info_sonde","r")
				ligne = fichier.readlines()
				# on recupere le contenu du fichier
				ligne = ligne[0].split(" ") 
				# variable qui va contenir l'etat du serveur
				# 1 veut dire qu'un point critique est atteint
				# 0 le point critique n'est pas atteint
				check_const = ""
				#debordement cpu
				if float(ligne[1]) > 95:
					check_const = check_const + "1"
				else:
					check_const = check_const + "0"
				#temperature cpu	
				if float(ligne[3]) > 80:
					check_const = check_const + "1"
				else:
					check_const = check_const + "0"	
				#debordement ram
				if float(ligne[7]) > 95:
					check_const = check_const + "1"
				else:
					check_const = check_const + "0"
				#debordement swap	
				if float(ligne[11]) > 80:
					check_const = check_const + "1"
				else:
					check_const = check_const + "0"
				# saturation disk	
				if float(ligne[23]) > 95:
					check_const = check_const + "1"
				else:
					check_const = check_const + "0"	
			except Exception as e:
				print("erreur d'ouverture du fichier")
				raise e
			finally:
				fichier.close()	
			# on recupere le temps actuelle sous un format definie : annee (1990) - mois (1-12) - jour (1-30) heure-minute-seconde
			date_insert = time.strftime("%Y-%m-%d %H:%M:%S")
			# on recupere l'adresse mac de la machine
			mac = get_mac()
			# Insertion dans la base de donnees des informations collecter
			# envoie des donnees via une requete request
			data_to_send = {'mac_address': mac, 'date_insert': date_insert,
							'avg_cpu': ligne[1], 'tmp_cpu': ligne[3],
							'ram_total': ligne[5], 'ram_used': ligne[7],
							'swap_total': ligne[9], 'swap_used': ligne[11],
							'nb_process': ligne[13], 'user_connect': ligne[15],
							'check_const': check_const, 'id_admin' : id_administrator,
							'physical_core': ligne[17], 'logical_core': ligne[19], 'disk_total' : ligne[21],
							'disk_usage' : ligne[23]}
			methods = 'insertion'
			url = adresse + methods
			r = requests.post(url, data = data_to_send)
			print (r.text)
		except Exception as e:
			raise e	
except Exception as e:
	print "Erreur de connexion au server dans le scripte collector"
	raise e

finally:
	sys.exit()