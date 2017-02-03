#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from flask import Flask, session, redirect, request, url_for, render_template, jsonify
import sqlite3
import json
import pygal

import os
import sys
import subprocess
import signal

import time
import datetime
from datetime import timedelta

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

# on recupere le repertoir courrant
current_directory = os.getcwd()
# on recupere le chemin absolu du fichier de configuration
file_configuration = current_directory + "/configuration"
# on recupere l'address du server, le mdp du compte uapv, l'address mail uapv sur le fichier de configuration
fichier = open(file_configuration, "r")
contenu = fichier.read()
contenu = contenu.split("\n")
fichier.close()
# adresse du serveur centrale 
serveur_adresse = contenu[0]
# le port a mettre sur ecoute
port = contenu[1]
# mdp du compte uapv
mdp = contenu[2]
# address mail uapv utiliser pour envoyer des mails
mail_uapv = contenu[3]
# address mail du super administrateur
mail_super_admin = contenu[4]
# on recupere le chemun absolu des bases de donnees
fichier = open("bdd_directory", "r")
contenu = fichier.read()
contenu = contenu.split(":")
bdd_name = contenu[0]
bdd_name_backups = contenu[1]
fichier.close()
#########################################################
##########  ON AJOUTE LES SCRIPTS AU CRONTAB ############
project_directory = ""
j = 0
for i in current_directory:
    if j != len(current_directory) - 1:
        project_directory = project_directory + i
        j = j + 1
# les scripts de la artie 2 a automatiser		
script_directory_2 = project_directory + "2"
# les scripts de la artie 3 a automatiser		
script_directory_3 = project_directory + "3"

# script check_alerte qui recuer les 5 dernieres alertes du cert
cmd_2 = "*/2 * * * * " + "cd " + script_directory_2 + " && " + "python " + script_directory_2 + "/" + "check_alerte.py"
# script clean_bdd qui supprime les donnees vielle de nbr jour, nbr est le nombre de jour qu'une donnee peut rester dans la bdd
cmd_3 = "*/2 * * * * " + "cd " + script_directory_2 + " && " + "python " + script_directory_2 + "/" + "clean_bdd.py"
# script mail_alerte qui verifie l'etat des serveur monitorer, et envoie un mail a son administrateur si un point critique et atteint
cmd_4 = "*/2 * * * * " + "cd " + script_directory_3 + " && " + "python " + script_directory_3 + "/" + "mail_alerte.py"

proc = subprocess.Popen(['bash', "cron.sh"])
# on tue le processus au bout d'une seconde 
time.sleep(1)
proc.kill()

# on recupere le chemin absolu des fichier de configuration du crontab, puis on rajoute les scripts a lancer
crontab_file_control = current_directory + "/crontab_control"
fichier = open(crontab_file_control, 'a')
fichier.write(cmd_2 + '\n' + cmd_3 + '\n' + cmd_4 + '\n')
fichier.close()

# proc = subprocess.Popen(['crontab', "crontab_control"])
proc = subprocess.Popen(['crontab', "f"])

# on tue le processus au bout d'une seconde 
time.sleep(1)
proc.kill()
# on cree une appllication flask
app = Flask(__name__)


###### Fonction d'envoie de mail ######
## mail_to : a qui envoye le mail
## Subject_to : le sujet du mail
## Msg_to : le message du mail
def send_mail(mail_to, Subject_to, Msg_to):
    try:
        msg = MIMEMultipart()
        msg['From'] = mail_uapv
        msg['To'] = mail_to
        msg['Subject'] = Subject_to
        message = Msg_to
        msg.attach(MIMEText(message))
        print ("tentative de connexion au smtp")
        mailserver = smtplib.SMTP('smtpz.univ-avignon.fr', 25)
        print ("connexion smtp ok")
        mailserver.starttls()
        mailserver.login(mail_uapv, mdp)
        print ("loggin ok")
        mailserver.sendmail(msg['From'], msg['To'], msg.as_string())
        print ("envoie ok")
        mailserver.quit()
        return True
    except Exception as e:
        raise e
        return False


###################################### END FUNCTION SEND_MAIL ######################################
# fonction qui verifie si le mail donnee en parametre est celui d'un administrateur 
def is_admin(email):
    if email == mail_super_admin:
        return True
    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    email = (email,)
    curseur.execute(
        "SELECT COALESCE(COUNT(id_admin), 0) FROM admin WHERE mail = ?", email)
    existe = curseur.fetchone()[0]
    return existe > 0


################################## PARTIE WEB ######################################################
# on genere la cle de security pour les sessions
app.secret_key = os.urandom(32)
# session de l'admin
admin = {}
admin['email'] = mail_super_admin


@app.before_request
# on definie le temps qu'une session reste valide
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)


# fonction qui permet de se connecter au web service
@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form['email']
        if is_admin(email):
            session['email'] = email
            return redirect(url_for('accueil'))
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')


# fontion qui permet se se deconnecter et de supprimer la session en cour
@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('accueil'))


# fonction qui renvoie la page d'accueil du web service
@app.route('/')
@app.route('/accueil')
def accueil():
    if 'email' in session:
        # on afficher le template de la page d'accuil du web service
        return render_template('accueil.html', sess=session, admin=admin)
    # not logged
    return render_template('login.html')


# methode qui renvoie un template contenant les 5 derniere alertes du cert
@app.route('/alerte')
def alerte():
    if 'email' in session:
        # liste de 5 dictionnaire contenant des inforamtions sur les alertes dans la bdd
        liste_of_alerte = []
        bdd = sqlite3.connect(bdd_name)
        curseur = bdd.cursor()
        # on recupere les 5 dernieres alertes
        curseur.execute(
            "SELECT ref_alerte, date_alerte, url_alerte FROM alerte ORDER BY date_alerte DESC LIMIT 5")
        informations = curseur.fetchall()
        # pour chaque alerte on recupere le detail des infos sur elle
        for info in informations:
            tmp = {'ref': info[0], 'date_alerte': info[1], 'url_alerte': info[2]}
            # on ajoute le dictionnaire a la liste
            liste_of_alerte.append(tmp)
        # on afficher le template avec la liste des alertes et les infos concernant les serveurs lients
        return render_template('alerte.html', dico_1=liste_of_alerte, sess=session, admin=admin)
    # not logged
    return render_template('login.html')


# methode qui renvoie un template contenant les machines monitorer par la platforme
# le super admin voit toutes les machines, les autres ne voie que leur machine 
@app.route('/machine')
def machine():
    if 'email' in session:
        if session['email'] == mail_super_admin:
            # liste de dictionnaire contenant des inforamtions sur les serveur client
            liste_of_server = []
            # dictionnaire contenant les informations pour un serveur client
            infos = {}
            bdd = sqlite3.connect(bdd_name)
            curseur = bdd.cursor()
            # on recupere toutes les adresse mac contenant dans la bdd
            curseur.execute(
                "SELECT DISTINCT mac_address, id_admin FROM sonde")
            mac_et_id = list(curseur)
            # pour chaque adresse mac on recupere les infos concernant la machine qui a cette adresse mac
            for id_mac in mac_et_id:
                infos = {}
                info = {}
                # on recupere le mail de l'administrateur qui se charge de ce serveur client
                id_admin = (id_mac[1],)
                curseur.execute(
                    "SELECT mail FROM admin WHERE id_admin = ?", id_admin)
                infos['mail_admin'] = curseur.fetchone()[0]
                # on recupere les derniere infos concernant le serveur client qui correspond a l'adresse mac
                curseur.execute(
                    "SELECT * FROM sonde WHERE mac_address = '%s' AND id_sonde = (SELECT MAX(id_sonde) FROM sonde WHERE mac_address = '%s')" % (
                    id_mac[0], id_mac[0]))
                info = list(curseur)[0]
                # on ajoute les informations au dictionnaire
                infos['mac_address'] = info[1]
                infos['last'] = info[2]
                infos['logical_core'] = info[16]
                infos['physical_core'] = info[15]
                infos['disk_total'] = info[13]
                infos['ram_total'] = info[5]
                infos['swap_total'] = info[7]
                infos['nb_proc'] = info[9]
                infos['nb_user'] = info[10]
                # on ajoute le dictionnaire a la liste
                liste_of_server.append(infos)
            # on afficher le template avec la liste des alertes et les infos concernant les serveurs lients
            return render_template('machine.html', dico_2=liste_of_server, sess=session, admin=admin)
        # donc ici ce n'est pas le super admin, alors on affiche uniquement les machines monitorer par cet admin
        else:
            # liste de dictionnaire contenant des inforamtions sur les serveur client
            liste_of_server = []
            # dictionnaire contenant les informations pour un serveur client
            infos = {}
            bdd = sqlite3.connect(bdd_name)
            curseur = bdd.cursor()
            # on recupere l'id de l'admin via son email
            t = (session['email'],)
            curseur.execute(
                "SELECT id_admin FROM admin WHERE mail = ?", t)
            id_administrator = curseur.fetchone()[0]
            # on recupere toutes les adresse mac contenant dans la bdd
            t = (id_administrator,)
            curseur.execute(
                "SELECT DISTINCT mac_address FROM sonde WHERE id_admin = ?", t)
            mac_list = list(curseur)
            # pour chaque adresse mac on recupere les infos concernant la machine qui a cette adresse mac
            for mac in mac_list:
                infos = {}
                infos['mail_admin'] = session['email']
                # on recupere les derniere infos concernant le serveur client qui correspond a l'adresse mac
                curseur.execute(
                    "SELECT * FROM sonde WHERE mac_address = '%s' AND id_sonde = (SELECT MAX(id_sonde) FROM sonde WHERE mac_address = '%s')" % (
                    mac[0], mac[0]))
                info = list(curseur)[0]
                # on ajoute les informations au dictionnaire
                infos['mac_address'] = info[1]
                infos['last'] = info[2]
                infos['logical_core'] = info[16]
                infos['physical_core'] = info[15]
                infos['disk_total'] = info[13]
                infos['ram_total'] = info[5]
                infos['swap_total'] = info[7]
                infos['nb_proc'] = info[9]
                infos['nb_user'] = info[10]
                # on ajoute le dictionnaire a la liste
                liste_of_server.append(infos)
            # on afficher le template avec la liste des alertes et les infos concernant les serveurs lients
            return render_template('machine.html', dico_2=liste_of_server, sess=session, admin=admin)
    # non connecte
    return render_template('login.html')


# envoie de mail a n'importe qui depuis le service web
@app.route('/send_mail_to', methods=['GET', 'POST'])
def send_mail_to():
    if 'email' in session:
        if request.method == 'POST':
            mail_to = request.form['email']
            Subject = request.form['Subject']
            message = request.form['message']
            if send_mail(mail_to, Subject, message):
                print("mail envoyer avec success")
                return redirect(url_for('accueil'))
            else:
                print("echec de l'envoie")
                return redirect(url_for('accueil'))
        else:
            return render_template('send_mail.html', sess=session, admin=admin)
    else:
        return render_template("login.html")


# methode permettant de renvoyer un template avec des informations detailler sur la machine
# avec l'adresse mac = mac_adresse donner en parametre)
@app.route('/machine_info/<mac_address>')
def machine_info(mac_address=None):
    if 'email' in session:
        # on recupere le mail de l'admin qui gere le serveur clien
        bdd = sqlite3.connect(bdd_name)
        curseur = bdd.cursor()
        # on recupere l'id de l'amdin de ce serveur client
        curseur.execute(
            "SELECT id_admin FROM sonde WHERE mac_address = '%s'" % mac_address)
        id_admin = curseur.fetchone()[0]
        # on recupere l'address mail de l'admin de ce serveur client
        curseur.execute(
            "SELECT mail FROM admin WHERE id_admin = '%s'" % id_admin)
        mail_client = curseur.fetchone()[0]
        if session['email'] == mail_client or session['email'] == mail_super_admin:
            # dictionnaire qui stocke les information detaille sur le serveur client qui correspond a l'adresse mac donnee en paramettre
            server_info = {}
            # On recupere les informations a afficher dans le graphe
            curseur.execute(
                "SELECT * FROM sonde WHERE mac_address = '%s' ORDER BY date_insert DESC LIMIT 5" % mac_address)
            info = list(curseur)
            # on remplie le dictionnaire a renvoyer
            server_info['mail_admin'] = mail_client
            server_info['date_insert'] = info[0][2]
            server_info['avg_cpu'] = info[0][3]
            server_info['tmp_cpu'] = info[0][4]
            server_info['ram_total'] = info[0][5]
            server_info['ram_used'] = info[0][6]
            server_info['swap_total'] = info[0][7]
            server_info['swap_used'] = info[0][8]
            server_info['nb_process'] = info[0][9]
            server_info['nb_user'] = info[0][10]
            server_info['check_const'] = info[0][11]
            server_info['disk_total'] = info[0][13]
            server_info['disk_usage'] = info[0][14]
            # on ferme la bdd, plus besoin d'y acceder
            bdd.close()
            # si le nombre d'inserstion est inferieure a 5, on n'affiche pas de graphe
            if len(info) >= 5:
                # j est une liste contenant la date des 5 derniers envoie
                j = []
                indexe = info[0][2]
                indexe = datetime.datetime.strptime(indexe, '%Y-%m-%d %H:%M:%S').strftime('%H-%M-%S')
                for i in info:
                    k = i[2]
                    k = datetime.datetime.strptime(k, '%Y-%m-%d %H:%M:%S').strftime('%M')
                    j.append(int(k))
                # Affichage avec le module pygal
                # Affichage en couleur
                # On produit un fichier svg
                line_chart = pygal.Line()
                line_chart.title = 'suivie serveur'
                line_chart.x_labels = [j[4], j[3], j[2], j[1], j[0]]
                line_chart.add('CPU (%)', [float(info[4][3]), float(info[3][3]), float(info[2][3]), float(info[1][3]),
                                           float(info[0][3])])
                line_chart.add('degre (C)', [float(info[4][4]), float(info[3][4]), float(info[2][4]), float(info[1][4]),
                                             float(info[0][4])])
                line_chart.add('disk_usage (%)',
                               [float(info[4][14]), float(info[3][14]), float(info[2][14]), float(info[1][14]),
                                float(info[0][14])])
                line_chart.add('ram_used (%)',
                               [float(info[4][6]), float(info[3][6]), float(info[2][6]), float(info[1][6]),
                                float(info[0][6])])
                line_chart.add('swap_used (%)',
                               [float(info[4][8]), float(info[3][8]), float(info[2][8]), float(info[1][8]),
                                float(info[0][8])])
                line_chart.add('process (X10)', [float(info[4][9]) / 10, float(info[3][9]) / 10, float(info[2][9]) / 10,
                                                 float(info[1][9]) / 10, float(info[0][9]) / 10])
                line_chart.add('user_connect',
                               [float(info[4][10]), float(info[3][10]), float(info[2][10]), float(info[1][10]),
                                float(info[0][10])])

                # on donne le chemun absolu ou sauvegarder les images generer
                lePath = os.getcwd()
                # on supprime toutes les images deja existante avant d'en genrer une nouvelle
                f1 = 'clean.sh'
                proc = subprocess.Popen(['bash', f1])
                # on tue le processus au bout d'une seconde
                time.sleep(1)
                proc.kill()
                # on recupere le chemin absolu de l'image generer
                lePath = lePath + "/static/bar_chart" + indexe + ".svg"
                # on gener l'image avec pygal
                line_chart.render_to_file(lePath)
                file_name = "../static/" + "bar_chart" + indexe + ".svg"

                return render_template('info_machine.html', dico_1=file_name, dico_2=server_info, sess=session,
                                       admin=admin)

            else:
                return render_template('info_machine_error_1.html', sess=session, admin=admin)
    else:
        return render_template('login.html')


# fonction qui renvoie un template pour le super admin uniquement pour voir tous les admins de la platforme de controle
@app.route('/gestion_admin')
def gestion_admin():
    if 'email' in session:
        if session['email'] == mail_super_admin:
            admin_info = {}
            # liste des administrateurs
            liste_of_admin = []
            bdd = sqlite3.connect(bdd_name)
            curseur = bdd.cursor()
            # on recupere les adminstrateurs present dans la table admin
            curseur.execute(
                "SELECT * FROM admin")
            all_admin = curseur.fetchall()
            bdd.close()
            # pour chaque alerte on recupere le detail des infos sur elle
            for one_admin in all_admin:
                admin_info = {'id_admin': one_admin[0], 'mail_admin': one_admin[1], 'contrainte_admin': one_admin[2]}
                # on ajoute le dictionnaire a la liste
                liste_of_admin.append(admin_info)
            # on afficher le template avec la liste des administrateurs
            return render_template('gestion_admin.html', dico_1=liste_of_admin, sess=session, admin=admin)
        # seul le supper admin peut avoir cette option
        else:
            # ouste
            return redirect(url_for('accueil'))
    # vous n'etes pas conecter
    return render_template('login.html')


# fonction qui renvoie la page de configuration de la bdd seulement si c est le super admin qui la demande
@app.route('/gestion_bdd')
def gestion_bdd():
    if 'email' in session:
        if session['email'] == mail_super_admin:
            return render_template('gestion_bdd.html', sess=session, admin=admin)
        else:
            return redirect(url_for('accueil'))
    else:
        return render_template('login.html')


# fonction qui permet de configurer la base de donnees
# le nombre de jour qu'une infos reste dans la bdd
# restaurer la bdd complete
@app.route('/config_clean', methods=['POST'])
def config_clean():
    if 'email' in session:
        if session['email'] == mail_super_admin:
            table = {}
            if request.form['alerte'] is not None and request.form['sonde'] is not None:
                limit_alerte = request.form['alerte']
                limit_sonde = request.form['sonde']
                table['alerte'] = limit_alerte
                table['sonde'] = limit_sonde
                # on modifie le temps que peuvent rester les donnees dans la bdd
                fichier = open("temps", "w")
                fichier.write(str(limit_sonde) + ":" + str(limit_alerte))
                fichier.close()
                return render_template('gestion_bdd.html', dico_1=table, sess=session, admin=admin)
            else:
                print ("2")
                restore()
                return redirect(url_for('accueil'))
        else:
            return redirect(url_for('accueil'))
    else:
        return render_template('login.html')

########################## FIN DE LA PARTIE WEB ##############################################################################################


# fonction qui permet de verifier si le serveur est en ligne ou pas
@app.route('/connexion_server', methods=['POST'])
def connexion_server():
    return 'ok'


# fonction qui permet de restaurer la bdd completement
@app.route('/restore', methods=['POST'])
def restore():
    # on execute un script bash qui permet de deplacer la bdd de sauvegarde et de remplacer la bdd principale par celle si
    j = 1
    tmp = ""
    for i in current_directory:
        if j != len(current_directory):
            tmp = tmp + i
            j = j + 1

    f1 = tmp + '2/' + 'save.sh'
    proc = subprocess.Popen(['bash', f1, bdd_name_backups, bdd_name])
    # on tue le processus au bout d'une seconde
    time.sleep(1)
    proc.kill()
    return redirect(url_for('accueil'))


# fonction qui permet de supprimer les donnees veillent d'une certaine duree
@app.route('/clean_bdd', methods=['POST'])
def clean_bdd():
    alerte_day = request.form['alerte']
    sonde_day = request.form['sonde']
    try:
        bdd = sqlite3.connect(bdd_name)
        curseur = bdd.cursor()
        # suppression des donnees de la table alerte qui ont plus de (alerte_day) jours
        t1 = (alerte_day,)
        # dans le cas de 0 jours, la fonction julianday retourne un resultat negatif si date_alerte = now en terme de jour
        # l'astuce et de supprimer les donnees si le resultat est negatif quand la duree egal 0
        if int(alerte_day) == 0:
            curseur.execute(
                "DELETE FROM alerte WHERE julianday('now') - julianday(date_alerte) <= ? ", t1)
        else:
            curseur.execute(
                "DELETE FROM alerte WHERE julianday('now') - julianday(date_alerte) >= ? ", t1)
        # suppression des donnees de la table sonde qui ont plus de (sonde_day) jours
        t2 = (sonde_day,)
        if int(sonde_day) == 0:
            curseur.execute(
                "DELETE FROM sonde WHERE julianday('now') - julianday(date_insert) <= ?", t2)
        else:
            curseur.execute(
                "DELETE FROM sonde WHERE julianday('now') - julianday(date_insert) >= ?", t2)

        return "suppression effectuer avec succes"
    except Exception as e:
        message = "erreur d'ouverture de la base de donnee"
        bdd.rollback()
        raise e
        return message
    finally:
        bdd.commit()
        bdd.close()


# fonction qui renvoie tous les serveurs monitorer, sous forme json parce que l'information est trop volumineuse pour passer en text
@app.route('/all_server', methods=['POST'])
def all_server():
    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    servers = []
    curseur.execute(
        "SELECT DISTINCT mac_address FROM sonde")
    mac_list = list(curseur)
    for i in mac_list:
        servers.append(i[0])
    return jsonify(results=servers)

# fonction qui renvoie les 5 dernieres infos (5 dernieres insertions )concernant un serveur passe par post
@app.route('/display_five_last', methods=['POST'])
def display_five_last():
    mac_address = request.form['mac_address']
    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    # On recupere les informations a afficher dans le graphe
    curseur.execute(
        "SELECT date_insert,avg_cpu,tmp_cpu,ram_total,ram_used,swap_total,swap_used,nb_process,user_connect, disk_usage FROM sonde WHERE mac_address = '%s' ORDER BY date_insert DESC LIMIT 5" % mac_address)
    five_last_info = list(curseur)
    bdd.close()

    return jsonify(results=five_last_info)


# fonction qui renvoie un dictionaire contenant les infos de la derniere insertion d'un serveur passe en post
@app.route('/display_last', methods=['POST'])
def display_last():
    infos = {}
    mac_address = request.form['mac_address']
    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    curseur.execute(
        "SELECT * FROM sonde WHERE mac_address = '%s' AND id_sonde = (SELECT MAX(id_sonde) FROM sonde GROUP BY '%s')" % (
        mac_address, mac_address))
    info = list(curseur)[0]
    infos['mac_adress'] = info[1]
    infos['date_alerte'] = info[2]
    infos['avg_cpu'] = info[3]
    infos['temp=C'] = info[4]
    infos['RAM'] = info[5]
    infos['RAM_per'] = info[6]
    infos['SWAP'] = info[7]
    infos['SWAP_used'] = info[8]
    infos['nb_proc'] = info[9]
    infos['nb_user'] = info[10]
    infos['disk_total'] = info[13]
    infos['disk_usage'] = info[14]
    infos['physical_core'] = info[15]
    infos['logical_core'] = info[16]
    bdd.close()
    return jsonify(results=infos)


# fonction qui renvoie l'etat des machines monitorer par la platforme de controle
# renvoie une liste de dictionnaire
# chaque dictionnaire represente une machine
@app.route('/check_server', methods=['POST'])
def check_server():
    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    # dictionnaire contenant les info d'un serveur
    server_statuts = {}
    # une liste de dictionnaire de type server_statuts
    liste_server = []
    # on recupere tous les serveurs gere par la platforme de controle
    curseur.execute(
        "SELECT DISTINCT mac_address FROM sonde")
    mac_list = list(curseur)
    if len(mac_list) > 0:
        for mac in mac_list:
            server_statuts = {}
            list_const = []
            # on recupere l'adresse mac du sereur client
            server_statuts['mac_address'] = mac[0]
            # on recupere l'etat du serveur client avec l'adress mac
            curseur.execute(
                "SELECT check_const FROM sonde WHERE mac_address = '%s' AND id_sonde = (SELECT MAX(id_sonde) FROM sonde GROUP BY '%s')" % (
                mac[0], mac[0]))
            info = list(curseur)[0]
            # on recupere l'etat du serveur client
            server_statuts['etat_server'] = info[0]
            # on recupere le mail de l'admin du serveur et les alertes voulu par l'administrateur
            curseur.execute(
                "SELECT id_admin FROM sonde WHERE mac_address = '%s'" % mac[0])
            id_admin = curseur.fetchone()[0]
            curseur.execute(
                "SELECT contrainte, mail FROM admin WHERE id_admin = '%s'" % id_admin)
            info_admin = list(curseur)
            # on recupere les alerte voulu par l'administrateur du sereur client
            server_statuts['const_admin'] = info_admin[0][0]
            # on recupere l'adresse mail de l'administrateur du sereur client
            server_statuts['mail_admin'] = info_admin[0][1]
            liste_server.append(server_statuts)
    bdd.close()
    # on renvoie la liste des dictionnaires contenant les informations sur tous les serveurs client
    return jsonify(results=liste_server)


# fonction qui insert les alerte cert recupere depuis le flux rss et passe en post
# si l'alerte existe deja, il ne l'insert pas de nouveaux
# envoie un mail a tous les admins si une nouvelle alerte est inserer
@app.route('/insert_alerte', methods=['POST'])
def insert_alerte():
    ref_alerte = request.form['ref_alerte']
    title_alerte = request.form['titre_alerte']
    date_alerte = request.form['date_alerte']
    url_alerte = request.form['url_alerte']

    message = ""
    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    # bdd backups
    bdd_backups = sqlite3.connect(bdd_name_backups)
    curseur_backups = bdd_backups.cursor()
    # end bdd backups
    curseur.execute(
        "SELECT COALESCE(MAX(id_alerte), 0) FROM alerte WHERE ref_alerte = '%s'" % ref_alerte)
    occurence = curseur.fetchone()[0]
    if occurence == 0:

        curseur.execute(
            "SELECT COALESCE(MAX(id_alerte), 0) FROM alerte")
        id_alerte = curseur.fetchone()[0] + 1
        curseur.execute(
            "INSERT INTO alerte VALUES (?, ?, ?, ?, ?)", (id_alerte, ref_alerte, title_alerte, date_alerte, url_alerte))
        bdd.commit()
        # envoie des mail pour alerter les administrateurs d'une nouvel faille
        curseur.execute(
            "SELECT DISTINCT mail FROM admin")
        mail_liste = list(curseur)
        bdd.close()
        # construction du mail a envoyer a tout le monde
        Subject = "Nouvelle faille publier sur le site du CERT"
        Msg = "Reference alerte : " + ref_alerte + "\n"
        Msg = Msg + "Date de publication de l'alerte : " + date_alerte + "\n"
        Msg = Msg + "Vous pouvez consulter le billet du cert a l'adresse ci-dessous \n"
        Msg = Msg + url_alerte
        # envoie du message a tous les administrateurs
        for mail in mail_liste:
            print ("Envoie du mail a l'adresse suivante : {0}".format(mail[0]))
            if send_mail(mail[0], Subject, Msg):
                print ("alerte enovyer par mail avec succes a : {0}".format(mail))
            else:
                print ("echec de l'envoie de l'alerte par mail a : {0}".format(mail))
        # bdd backups
        curseur_backups.execute(
            "SELECT COALESCE(MAX(id_alerte), 0) FROM alerte WHERE ref_alerte = '%s'" % ref_alerte)
        occurence_2 = curseur_backups.fetchone()[0]
        if occurence_2 == 0:
            curseur_backups.execute(
                "SELECT COALESCE(MAX(id_alerte), 0) FROM alerte")
            id_alerte = curseur_backups.fetchone()[0] + 1
            curseur_backups.execute(
                "INSERT INTO alerte VALUES (?, ?, ?, ?, ?)",
                (id_alerte, ref_alerte, title_alerte, date_alerte, url_alerte))
            bdd_backups.commit()
        # end bdd backups

        bdd_backups.close()
        message = "insertion reussit"
    else:
        message = "deja presente"
        bdd.close()
        bdd_backups.close()
    return message


# fonction qui insert les informations recu des sondes
# chaque serveur monitorer envoie ses infos au serveur central qui les differencie avec leur address mac
@app.route('/insertion', methods=['POST'])
def insertion():
    mac_address = request.form['mac_address']
    date_insert = request.form['date_insert']
    avg_cpu = request.form['avg_cpu']
    tmp_cpu = request.form['tmp_cpu']
    ram_total = request.form['ram_total']
    ram_used = request.form['ram_used']
    swap_total = request.form['swap_total']
    swap_used = request.form['swap_used']
    nb_process = request.form['nb_process']
    user_connect = request.form['user_connect']
    check_const = request.form['check_const']
    id_admin = request.form['id_admin']
    disk_total = request.form['disk_total']
    disk_usage = request.form['disk_usage']
    logical_core = request.form['logical_core']
    physical_core = request.form['physical_core']
    # insertion des information recu dans la BDD
    try:

        bdd = sqlite3.connect(bdd_name)
        curseur = bdd.cursor()
        # bdd backups
        bdd_backups = sqlite3.connect(bdd_name_backups)
        curseur_backups = bdd_backups.cursor();
        # end bdd backups

        curseur.execute(
            "SELECT COALESCE(MAX(id_sonde), 0) FROM sonde")
        id_sonde = curseur.fetchone()[0] + 1

        curseur.execute(
            "INSERT INTO sonde VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (id_sonde, mac_address, date_insert, avg_cpu, tmp_cpu, ram_total, ram_used,
             swap_total, swap_used, nb_process, user_connect, check_const, id_admin,
             disk_total, disk_usage, physical_core, logical_core))

        # bdd backups
        curseur_backups.execute(
            "SELECT COALESCE(MAX(id_sonde), 0) FROM sonde")
        id_sonde = curseur_backups.fetchone()[0] + 1
        curseur_backups.execute(
            "INSERT INTO sonde VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (id_sonde, mac_address, date_insert, avg_cpu, tmp_cpu, ram_total, ram_used,
             swap_total, swap_used, nb_process, user_connect, check_const, id_admin,
             disk_total, disk_usage, physical_core, logical_core))
        # end bdd backups
        # on recupere le nombre d'insertion qu'il y a dans la bdd
        curseur.execute(
            "SELECT MAX(id_sonde) FROM sonde")
        id_sonde = curseur.fetchone()

        print(id_sonde)
        message = "info recu avec success"

    except Exception as e:
        message = "erreur d'ouverture de la base de donnee"
        # bdd_backups.rollback()
        bdd.rollback()
        raise e
    finally:
        # bdd backups
        bdd_backups.commit()
        bdd_backups.close()
        # end bdd backups
        bdd.commit()
        bdd.close()
        return message


# method appele pour savoir si la machine ayant l'address mac mac_address est dans la bdd ou pas
@app.route('/existe', methods=['POST'])
def existe():
    mac = request.form['mac_address']
    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    mac = (mac,)
    curseur.execute(
        "SELECT COALESCE (COUNT(id_sonde), 0) FROM sonde WHERE mac_address = ?", mac)
    if curseur.fetchone()[0] == 0:
        resultat_1 = "non"
    else:
        resultat_1 = "oui"
    bdd.close()
    return resultat_1


# fonction qui permet d'inserer un nouvel admin dans la bdd
@app.route('/insert_admin', methods=['POST'])
def insert_admin():
    contrainte = request.form['contrainte']
    mail = request.form['mail']
    message = "l'admin existe deja dans la bdd"
    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    # bdd backups
    bdd_backups = sqlite3.connect(bdd_name_backups)
    curseur_backups = bdd_backups.cursor();
    # end bdd backups
    t = (mail,)
    curseur.execute(
        "SELECT COALESCE(MAX(id_admin), 0) FROM admin WHERE mail = ?", t)
    existe = curseur.fetchone()[0]
    if existe == 0:
        curseur.execute(
            "SELECT COALESCE(MAX(id_admin), 0) FROM admin")
        id_admin = curseur.fetchone()[0] + 1

        curseur.execute(
            "INSERT INTO admin VALUES (?, ?, ?)", (id_admin, mail, contrainte))

        # bdd backups
        curseur_backups.execute(
            "SELECT COALESCE(MAX(id_admin), 0) FROM admin")
        id_admin = curseur_backups.fetchone()[0] + 1
        curseur_backups.execute(
            "INSERT INTO admin VALUES (?, ?, ?)", (id_admin, mail, contrainte))
        # end bdd backups
        message = "insertion de l'admin avec succes"
    # bdd backups
    bdd_backups.commit()
    bdd_backups.close()
    # bdd backups
    bdd.commit()
    bdd.close()

    return message


# fonction qui permet de renvoye le mail de l'admin en fonction de l'id envoyer via post
@app.route('/retreive_mail', methods=['POST'])
def retreive_mail():
    id_admin = request.form['id_admin']

    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    id_admin = (id_admin,)
    curseur.execute(
        "SELECT mail FROM admin WHERE id_admin = ?", id_admin)
    mail = curseur.fetchone()[0]
    print mail
    bdd.close()
    return mail


# fonction qui permet de mettre a jour le mail d'un admin
@app.route('/update_mail', methods=['POST'])
def update_mail():
    id_admin = request.form['id_admin']
    mail = request.form['mail']

    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()

    # bdd backups
    bdd_backups = sqlite3.connect(bdd_name_backups)
    curseur_backups = bdd_backups.cursor();
    # end bdd backups
    curseur.execute(
        "UPDATE admin SET mail = '%s' WHERE id_admin = '%s'" % (mail, id_admin))
    # bdd backups
    curseur_backups.execute(
        "UPDATE admin SET mail = '%s' WHERE id_admin = '%s'" % (mail, id_admin))
    # end bdd backups

    # bdd backups
    bdd_backups.commit()
    bdd_backups.close()
    # end bdd backups

    bdd.commit()
    bdd.close()

    return 'mise a jour du mail reussit'


# methode permettant de recupere l'id de l'administrateur via son mail envoyer par post
@app.route('/retreive_id_admin', methods=['POST'])
def retreive_id_admin():
    mail = request.form['mail']
    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    mail = (mail,)
    curseur.execute(
        "SELECT id_admin FROM admin WHERE mail = ?", mail)
    id_admin = curseur.fetchone()[0]
    bdd.close()
    return str(id_admin)


# fonction qui permet de renvoyer le type d'alertes choisie par un admin, via son id envoyer par post
@app.route('/retreive_contrainte', methods=['POST'])
def retreive_contrainte():
    id_admin = request.form['id_admin']
    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()
    id_admin = (id_admin,)
    curseur.execute(
        "SELECT contrainte FROM admin WHERE id_admin = ?", id_admin)
    contrainte = curseur.fetchone()[0]
    bdd.close()

    return contrainte


# fonction qui permet de mettre a jour le type d'alerte choisie par un admin
@app.route('/update_contrainte', methods=['POST'])
def update_contrainte():
    id_admin = request.form['id_admin']
    cont_insert = request.form['contrainte']

    bdd = sqlite3.connect(bdd_name)
    curseur = bdd.cursor()

    # bdd backups
    bdd_backups = sqlite3.connect(bdd_name_backups)
    curseur_backups = bdd_backups.cursor();
    # end bdd backups
    curseur.execute(
        "UPDATE admin SET contrainte = '%s' WHERE id_admin = '%s'" % (cont_insert, id_admin))
    # bdd backups
    curseur_backups.execute(
        "UPDATE admin SET contrainte = '%s' WHERE id_admin = '%s'" % (cont_insert, id_admin))
    # end bdd backups

    bdd.commit()
    bdd.close()

    # bdd backups
    bdd_backups.commit()
    bdd_backups.close()
    # end bdd backups
    return 'mise a jour des contraintes reussit'


if __name__ == "__main__":
    app.run(host=serveur_adresse, port=int(port))
