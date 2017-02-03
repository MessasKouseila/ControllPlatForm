#/usr/bin/env python3
import os
import datetime
import requests
import re
import feedparser
import BeautifulSoup
from urllib2 import urlopen


file_address_ = os.getcwd()
file_address = ''

for i in file_address_:
	if i != file_address_[len(file_address_) - 1]:
		file_address = file_address + i

file_address_rep = file_address + '4'
file_configuration = file_address_rep + "/configuration"
# on recupere l'address du server depuis le fichier de configuration
fichier = open(file_configuration, "r")
contenu = fichier.read()
contenu = contenu.split("\n")
fichier.close()




# scripte qui recupere les 5 dernieres alertes du cert

# on recupere le flux rss
myParser = feedparser.parse('http://www.cert.ssi.gouv.fr/site/cert-fr.rss')
# adresse du serveur centrale 
adresse = contenu[0]
port = contenu[1]
adresse = 'http://' + adresse + ':' + port + '/'

# compteur du nombre d'alerte recupere
nb_alerte = 0
i = 0
# on recupere le nombre d'alerte disponible
all_alerte = len(myParser['entries'])
# dictionnaire contenant les informations sur les alertes recupere a envoyer au serveur centrale
data_to_send = {}
# tant qu'on a pas recpere 5 alerte de type 'AVI', on boucle
# si on parcour toutes alertes on arrete de boucler aussi
while i < all_alerte and nb_alerte < 5:
	# on recupere le type de l'alerte: AVI ou ACT, les act sont des bulletin d'info,
	# alors que les AVI sont des avis concernant des failles pouvant etre dangereuse pour les serveurs
	alerte = myParser['entries'][i]['title_detail']['value']
	# on recupere l'url de l'alerte
	url = myParser['entries'][i]['link']
	# l'alerte doit corespondre a un AVI
	alerte_type = r".*AVI.*"
	exp_alerte = re.compile(alerte_type)
	# si l'alerte est un avi
	if exp_alerte.search(alerte) is not None:
		# Alerte a recupere
		# utilisation de beautiful soup pour extraire des infos depuis la page html qui contient des detailles sur l'alerte
		html = urlopen(url).read()
		soup = BeautifulSoup.BeautifulSoup(html)
		# on va recupere des infos a partir d'un tableau dans la page html de l'alerte
		table = soup.findAll('table')[2]
		# reference de l'alerte
		ref = (table.findAll('td')[2]).text
		# titre de l'alerte
		titre = (table.findAll('td')[4]).text
		# date de publication de l'alerte
		date_alerte = myParser['feed']['updated']
		# on redefinie le format de la date pour pouvoir l'utiliser plus facilement
		date_alerte = datetime.datetime.strptime(date_alerte, '%a, %d %b %Y %H:%M:%S CEST').strftime('%Y-%m-%d %H:%M:%S')
		data_to_send = {'ref_alerte': ref, 'titre_alerte': titre, 'date_alerte': date_alerte, 'url_alerte': url}
		# on insert dans la table alerte la nouvelle alerte, 
		# et envoie un mail a tous les administrateur pour leur indiquer qu'une nouvelle faille a ete publie. 
		methods = 'insert_alerte'
		url = adresse + methods
		r = requests.post(url, data = data_to_send)
		print(r.text)	
		nb_alerte = nb_alerte + 1
	i = i + 1

print('fin du scritpe')	