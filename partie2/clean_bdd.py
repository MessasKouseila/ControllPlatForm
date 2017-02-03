#/usr/bin/env python3
import requests
import os



file_address_ = os.getcwd()
file_address = ''

for i in file_address_:
	if i != file_address_[len(file_address_) - 1]:
		file_address = file_address + i

file_address_rep = file_address + '4'
# chemin vers le fichier de configuration pour le nettoyage des tables alerte et sonde
file_config_time = file_address_rep + "/temps"
# chemin du fichier de configuration contenant l'addresse du serveur centrale
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

# on recupere le nombre de jours qu'une informations peut rester dans la table alerte et sonde
# si ce temps est depasse, on supprime l'information
fichier = open(file_config_time, "r")
contenu = fichier.readlines()
contenu_ = contenu[0].split(":")
fichier.close()
data_to_send = {'sonde' : contenu_[0], 'alerte' : contenu_[1]}
methods = 'clean_bdd'
url = adresse + methods
r = requests.post(url, data = data_to_send)
print(r.text)