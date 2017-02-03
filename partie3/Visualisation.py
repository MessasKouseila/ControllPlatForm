#/usr/bin/env python3
import requests
import json
import datetime
import pygal
import subprocess
import os

file_address_ = os.getcwd()
file_address = ''

for i in file_address_:
	if i != file_address_[len(file_address_) - 1]:
		file_address = file_address + i

file_address_rep = file_address + '4'
file_configuration = file_address_rep + "/configuration"
# on recupere l'address sur server depuis le fichier de configuration
fichier = open(file_configuration, "r")
contenu = fichier.read()
contenu = contenu.split("\n")
fichier.close()
# adresse du serveur centrale
adresse = contenu[0]
port = contenu[1]
adresse = 'http://' + adresse + ':' + port + '/'



# dictionnaire associant pour chaque adresse mac un indexe, l'indexe indique le numeros de la machine 
dico_mac = {}

def display_serveur(dico_mac):

	# dictionnaire d'envoie d'infos avec requests
	data_to_send = {}
	# on demande au serveur de nous envoyer l'adresse mac de tous les serveurs gerer par la platforme
	methods = 'all_server'
	url = adresse + methods
	r = requests.post(url, data = None)
	resultat = r.json()
	# variable qui represente le numeros de la machine ( indexe )
	j = 0
	print("idexe ||   mac_add   ||       date       || avg_cpu || temp=C || RAM || RAM_per || SWAP || SWAP_used || nb_proc || nb_user || Disk_total || Disk_usage \n")
	# pour chaque adresse mac renvoyer par le serveur centrale on affiche les derniere infos concernant la machine avec cette adresse mac
	for i in resultat['results']:
		j = j +1
		# demande au serveur de lui envoyer les dernieres infos concernant la machine dont l'adresse mac est i
		methods = 'display_last'
		url = adresse + methods
		data_to_send.clear()
		data_to_send = {'mac_address' : i}
		r = requests.post(url, data = data_to_send)
		info = r.json()
		info = info['results']
		# affichge des dernieres infos pour chaque serveur client
		print("{0}   ||   {1} || {2} || {3} || {4} || {5} || {6} ||   {7}   ||   {8}  ||   {9}   ||   {10}   ||   {11}   ||   {12}\n".format(j, info['mac_adress'], info['date_alerte'],
																												   info['avg_cpu'], info['temp=C'], info['RAM'],
																												   info['RAM_per'], info['SWAP'], info['SWAP_used'],
																												   info['nb_proc'], info['nb_user'], info['disk_total'], info['disk_usage']))
		
		# Permet de verifier apres si le serveur saisie existe ou pas,
		# Si il existe on recupere directement sa valeur qui est son mac
		dico_mac[j] = i
		# fin de l'affichage terminal
def display_graph(dico_mac, index):

	# On verfifie si le serveur existe
	if dico_mac.has_key(index):
		# on demande au serveur de nous envoyer les 5 derniere infos corespendant a l'adresse mac du serveur client qu'on veut afficher avec pygal
		mac = dico_mac[index]
		methods = 'display_five_last'
		url = adresse + methods
		data_to_send = {'mac_address' : mac}
		r = requests.post(url, data = data_to_send)
		info = r.json()
		info = info['results']
		# si il y a au moins 5 insertions pour le serveur client
		if len(info) >= 5:
			# j est une liste contenant la date des 5 derniers envoie
			j = []
			for i in info:
				k = i[0]
				# on recupere juste les minutes
				k = datetime.datetime.strptime(k, '%Y-%m-%d %H:%M:%S').strftime('%M')
				j.append(int(k))
			# Affichage avec le module pygal
			# Affichage en couleur
			# On produit un fichier svg qu'on ouvre via un navigateur, ici on utilise firefox 
			line_chart = pygal.Line()
			line_chart.title = 'suivie serveur'
			line_chart.x_labels = [j[4], j[3], j[2], j[1], j[0]]
			line_chart.add('CPU (%)', [float(info[4][1]), float(info[3][1]), float(info[2][1]), float(info[1][1]), float(info[0][1])])
			line_chart.add('degre (^C*10)', [float(info[4][2])/10, float(info[3][2])/10, float(info[2][2])/10, float(info[1][2])/10, float(info[0][2])/10])
			line_chart.add('ram_total (Go)', [float(info[4][3]), float(info[3][3]), float(info[2][3]), float(info[1][3]), float(info[0][3])])
			line_chart.add('ram_used (%)', [float(info[4][4]), float(info[3][4]), float(info[2][4]), float(info[1][4]), float(info[0][4])])
			line_chart.add('swap_total (Go)', [float(info[4][5]), float(info[3][5]), float(info[2][5]), float(info[1][5]), float(info[0][5])])
			line_chart.add('swap_used (%)', [float(info[4][6]), float(info[3][6]), float(info[2][6]), float(info[1][6]), float(info[0][6])])
			line_chart.add('process (*10)', [float(info[4][7])/10, float(info[3][7])/10, float(info[2][7])/10, float(info[1][7])/10, float(info[0][7])/10])
			line_chart.add('user_connect', [float(info[4][8]), float(info[3][8]), float(info[2][8]), float(info[1][8]), float(info[0][8])])
			line_chart.render_to_file('bar_chart.svg')
			# Lancement du navigateur afin d'afficher le graphe
			subprocess.check_output(["firefox", 'bar_chart.svg'])

		# Dans le cas ou le nombre d'envoie ( nombre de fois ou les sondes on envoyer des donnees )	
		else:
			print("Donnees insuffisante pour afficher le graphe")	
	# L'indice donnee ne correspond a aucun serveur gerer par la platforme de controle		
	else:
		print("Serveur introuvable")
choix_menu = 0	
index = 1	
def menu():
	print("1- afficher les serveurs monitorer")
	print("2- faire un graphe sur l'une des machine monitorer ")
	print("3- quitter")
	choix_menu = input("faire un choix :  ")
	return choix_menu
while choix_menu != 3:
	if choix_menu == 1:
		display_serveur(dico_mac)
		choix_menu = menu()
	elif choix_menu == 2:
		index = input("Entrez un indice correspondant a l'index voulu : ")
		display_graph(dico_mac, index)
		choix_menu = menu()
	else:	
		choix_menu = menu()
