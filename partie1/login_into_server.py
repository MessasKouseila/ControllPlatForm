#/usr/bin/env python3
import requests
import subprocess
import datetime
import os
import sys
import time
import re
from uuid import getnode as get_mac

# fonction qui teste si le serveur est disponible
def teste_connexion():
	methods = 'connexion_server'
	url = adresse + methods
	r = requests.post(url, data = None)
	return r.status_code < 400

file_rep = os.getcwd()

file_id_admin = file_rep + "/id_admin"
file_configuration = file_rep + "/configuration"
# on recupere l'address du server depuis le fichier de configuration
fichier = open(file_configuration, "r")
contenu = fichier.read()
contenu = contenu.split("\n")
fichier.close()

id_administrator = 0
mac = get_mac()
adresse = contenu[0]
port = contenu[1]
adresse = 'http://' + adresse + ':' + port + '/'

# try pour tout le teste de connexion
try:
	if teste_connexion():
		# try pour l'envoie de donnees au serveur
		try:
			data_to_send = {'mac_address': mac}
			# on verifie si la machine existe deja dans la bdd
			methods = 'existe'
			url = adresse + methods
			r = requests.post(url, data = data_to_send)
			existe = r.text
			# si elle n'existe pas dans la bdd, donc c est la 1er fois qu'elle se connecte		
			if existe == "non":
				#administrateur inexistant
				print("Vous vous connecter pour la 1er fois")
				# on demande les infos a l'administrateur du serveur client
				mail = raw_input("Entrez votre mail pour etre alerte des problemes de votre serveur : ")
				# Teste du mail sisie 
				# expression reguliere que l'email doit respecter
				chn_mail = r"^[a-z0-9._-]+@[a-z0-9._-]{2,}\.[a-z]{2,4}$"
				exp_mdp = re.compile(chn_mail)
				# tant que l'email n'est pas valide en boucle 
				while exp_mdp.search(mail) is None:
					mail = raw_input("Tapez votre mail : ")

				#inserer l'administrateur dans la table
				# par default les contrainte de l'admin sont initialiser a "non"
				defaut_value = "non"
				data_to_send.clear
				# envoie au serveur des info concernant l'administrateur 
				data_to_send = {'mail': mail, 'contrainte': defaut_value}
				methods = 'insert_admin'
				url = adresse + methods	
				r = requests.post(url, data = data_to_send)
				# on place l'id de l'adim dans le fichier
				data_to_send.clear()
				data_to_send = {'mail': mail}
				methods = 'retreive_id_admin'
				url = adresse + methods	
				r = requests.post(url, data = data_to_send)
				id_administrator = int(r.text)
				# on ecrit dans le fichier l'id de l'administrateur, pour pouvoir l'utiliser apres
				fichier = open(file_id_admin, 'w')
				fichier.write(str(id_administrator) + ':')
				fichier.close()
			else:
				fichier = open(file_id_admin, "r")
				contenu = fichier.read()
				contenu = contenu.split(":")
				fichier.close()
				id_administrator = contenu[0]
				# donc la machine est deja presente sur le serveur, on demande a l'administrateur si il veut modifier ces infos
				print("voulez vous modifier votre adresse mail : ")
				choix = raw_input("oui/non : ")
				if choix == "oui":
					# il veut modifier son email
					data_to_send.clear
					data_to_send = {'id_admin': id_administrator}
					# on recupere l'ancien mail
					methods = 'retreive_mail'
					url = adresse + methods	
					r = requests.post(url, data = data_to_send)
					mail = r.text
					# on lui demande de rentrer l'ancien mail 
					chek_mail = raw_input("Saisir l'ancien mail : ")
					# teste si le mail est valide
					# tant qu'il ne saisie pas l'ancien email il ne sort pas de la boucle
					while mail != chek_mail:
						print("mail invalide")
						chek_mail = raw_input("Saisir l'ancien mail : ")
					# il a saisie l'ancien email
					# il peut saisir maintenant son nouveau mail	
					mail = raw_input("Entrez votre nouveau mail : ")
					# on teste toujours la validite du mail
					chn_mail = r"^[a-z0-9._-]+@[a-z0-9._-]{2,}\.[a-z]{2,4}$"
					exp_mdp = re.compile(chn_mail)
					# tant que le mail saisie n'est pas valide il boucle
					while exp_mdp.search(mail) is None:
						mail = raw_input("Tapez votre mail : ")
					# le nouveau mail est saisie, on met a jout la bdd	
					data_to_send.clear
					data_to_send = {'id_admin': id_administrator, 'mail': mail}
					methods = 'update_mail'
					url = adresse + methods		
					r = requests.post(url, data = data_to_send)
					# on confirme la mise a jour du mail
					print(r.text)
					
			fichier = open(file_id_admin, "r")
			contenu = fichier.read()
			contenu = contenu.split(":")
			fichier.close()
			id_administrator = contenu[0]		
			# on passe maintenant au type d'alerte
			# on recupere les alerte qu'il faut recevoir 		
			data_to_send.clear
			data_to_send = {'id_admin': int(id_administrator)}
			methods = 'retreive_contrainte'
			url = adresse + methods	
			r = requests.post(url, data = data_to_send)	
			# const contient le type d'alerte que l'administrateur veut recevoir
			const = r.text
			cont_insert = ""
			# choix_1 nous servira pour savoir si il faut mettre a jour le type d'alerte ou pas 
			choix_1 = "oui"
			# les type d'alerte que l'administrateur peut recevoir
			constraint = ["debordement cpu", "chauffe du cpu","debordement RAM","debordement SWAP","debordement disk"]	
			# l'administrateur n'as jamais saisie ces choix concernant le type d'alerte
			# il doit obligatoirement le faire donc
			if const == "non":
				print("choisir les alertes a recevoir par mail : (oui pour accepte sinon autre chose) \n")
				for c in constraint:
					choix = raw_input("voulez vous etre alerte de  {} : \n".format(c))
					if choix == "oui":
						cont_insert = cont_insert + "1"
					else:
						cont_insert = cont_insert + "0"
			else:
				# l'administrateur a deja saisie les types d'alertes a recevoir, on lui demande si il veut les modifier
				choix_1 = raw_input("voulez vous modifier les alertes (oui pour modifier sinon autre chose) : \n")
				# si il dit oui 
				if choix_1 == "oui":
					# il refait sont choix concernant le type d'alerte a recevoir
					print("choisir les alertes a recevoir par mail : (oui pour accepte sinon autre chose) \n")
					for c in constraint:
						choix = raw_input("voulez vous etre alerte de  {} : ".format(c))
						if choix == "oui":
							cont_insert = cont_insert + "1"
						else:
							cont_insert = cont_insert + "0"
			# on teste si il a choisie de modifier le type d'alerte ou si c est pour la 1er fois qu'il les saisie				
			if choix_1 == "oui":
				data_to_send.clear()
				data_to_send = {'id_admin': id_administrator, 'contrainte': cont_insert}
				methods = 'update_contrainte'
				url = adresse + methods	
				r = requests.post(url, data = data_to_send)
				print(r.text)					
			# ajout au crontab du scripte collector pour envoyer toute les 5 minutes les infos des sondes au serveur
		except Exception as e:
			raise e
		# ajout du script collector au crontab du serveur client
		print "ajout du script collector au crontab"
		# on recupere le crontab actuel
		proc = subprocess.Popen(['bash', "cron_2.sh"])
		# on tue le processus au bout d'une seconde 
		time.sleep(2)
		proc.kill()

		cmd = "*/1 * * * * " + "cd " + file_rep + " && " + "python " + file_rep + "/" + "collector.py"
		crontab_file = file_rep + "/crontab_client"
		fichier = open(crontab_file, 'a')
		fichier.write(cmd + '\n')
		fichier.close()
		proc = subprocess.Popen(['crontab', "crontab_client"])
		# on tue le processus au bout d'une seconde 
		time.sleep(1)
		proc.kill()	
except Exception as e:
	print "erreur de connexion au server dans le scripte login"
	raise e
finally:
	sys.exit()