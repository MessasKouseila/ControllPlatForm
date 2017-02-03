#!/usr/bin/env python3
# coding : utf8
import sqlite3
import subprocess
import os
import signal 
import sys
import time

# on sauvegarde le chemun absolu pour acceder a la base de donnees
directory_bdd = os.getcwd()
directory_bdd = directory_bdd + "/Moteur_stockage.db"

# on sauvegarde le chemun absolu pour acceder a la base de donnees de restauration
directory_bdd_backup = os.getcwd() + "/backups" + "/Moteur_stockage_backups.db"

file_address_ = os.getcwd()
file_address = ''

for i in file_address_:
	if i != file_address_[len(file_address_) - 1]:
		file_address = file_address + i
# on sauvegarde les chemuns dans un fichier de la partie 4, pour que le serveur y accede facilement
file_address = file_address + '4'
file_config = file_address + "/bdd_directory"

fichier = open(file_config, 'w')
fichier.write(directory_bdd + ':' + directory_bdd_backup + ':')
fichier.close()

try:
	bdd = sqlite3.connect(directory_bdd)
	curseur = bdd.cursor()
	# TAble qui permet de sauvegarder les administrateurs des serveurs distants
	curseur.execute("""
	CREATE TABLE IF NOT EXISTS admin(
		id_admin INTEGER PRIMARY KEY, 
	    mail VARCHAR(255),
	    contrainte VARCHAR(8)
	)
	""")
	# TAble qui permet de sauvegarder les alerte du (http://www.cert.ssi.gouv.fr/)
	curseur.execute("""
	CREATE TABLE IF NOT EXISTS alerte(
		id_alerte INTEGER,
	    ref_alerte VARCHAR(255) PRIMARY KEY,
	    title_alerte VARCHAR(255),
		date_alerte DATE,
	    url_alerte TEXT
	)
	""")
	# Table qui sauvegarder les informations concernant les serveurs distants
	curseur.execute("""
	CREATE TABLE IF NOT EXISTS sonde(
		id_sonde INTEGER PRIMARY KEY, 
		mac_address VARCHAR(255),
		date_insert DATE,
		avg_cpu REAL,
		tmp_cpu REAL,
		ram_total REAL,
		ram_used REAL,
		swap_total REAL,
		swap_used REAL,
		nb_process REAL,
		user_connect REAL,
		check_const VARCHAR(10),
		id_admin INTEGER,
		disk_total REAL,
		disk_usage REAL,
		physical_core INTEGER,
		logical_core INTEGER
	)
	""")
	bdd.commit()
######################### CREATTION D'UNE BASE DE DONNEES POUR LA RESTAURATION #########################
	f1 = "save.sh"
	proc = subprocess.Popen(['bash', f1, directory_bdd, directory_bdd_backup])
	# on tue le processus au bout d'une seconde 
	time.sleep(1)
	proc.kill()	
except Exception as e:
    # Roll back si il y a des erreurs
    bdd.rollback()
    raise e
finally:
    # fermer la bdd
    bdd.close()