#/usr/bin/env python
import os
import requests
import json
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import smtplib


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

# on recupere le mot de passe du compte mail uapv
fichier = open("code","r")
contenu = fichier.readlines()
mdp_tmp = contenu[0]
mdp = ""
# on utlise la boucle pour ne pas prendre le caractere speciale '\n'
for i in mdp_tmp:
    if i != "\n":
        mdp = mdp + i
fichier.close()


###### Fonction d'envoie de mail ######
## mail_to : a qui envoye le mail
## Subject_to : le sujet du mail
## Msg_to : le message du mail
def send_mail(mail_to, Subject_to, Msg_to):
    
    msg = MIMEMultipart()
    msg['From'] = 'kouseila.messas@alumni.univ-avignon.fr'
    msg['To'] = mail_to
    msg['Subject'] = Subject_to
    message = Msg_to
    msg.attach(MIMEText(message))
    print "tentative de connexion au smtp"
    mailserver = smtplib.SMTP('smtpz.univ-avignon.fr', 25)
    print "connexion smtp ok"
    mailserver.starttls()
    mailserver.login('kouseila.messas@alumni.univ-avignon.fr', mdp)
    print "loggin ok"
    mailserver.sendmail(msg['From'], msg['To'], msg.as_string())
    print "envoie ok"
    mailserver.quit()
    
    return True
########  END FUNCTION SEND_MAIL ######################################

# methode qui renvoie une liste de  dictionnaire contenant pour chaqu'un d'eux
    # l'etat du serveur
    # l'adresse mail de son administrateur
    # les alertes choisie par l'administrateur
methods = 'check_server'
url = adresse + methods
r = requests.post(url, data = None)
resultat = r.json()
list_const = []
# pour chaque machine on verifie si il faut envoyer un email d'alete ou pas 
for machine in resultat['results']:
    list_const = []
    # les types d'alerte voulu par l'administrateur
    const_admin = machine['const_admin']
    # mail de l'administrateur du serveur client 'machine' 
    mail_admin = machine['mail_admin']
    etat_server = machine['etat_server']
    #Verification des points critiques
        # pour declanche l'envoie d'une alerte, 
        # il faut qu'un point critique soit atteint 
        # et que l'administrateur ai envie de recevoir ce type d'alerte
    #debordement cpu
    if etat_server[0] == "1" and const_admin[0] == "1":
        list_const.append("votre cpu arrive bientot a saturation")
    #temperature cpu
    if etat_server[1] == "1" and const_admin[1] == "1":
        list_const.append("votre cpu est en surchauffe")
    #debordement ram
    if etat_server[2] == "1" and const_admin[2] == "1":
        list_const.append("votre RAM arrive a saturation, perte de donnees en l'absense de swap, votre serveur va ralentir")
    #debordement swap
    if etat_server[3] == "1" and const_admin[3] == "1":
        list_const.append("votre swap arrive a saturation, les donnees seront perdu definitivement")
    #debordement disk    
    if etat_server[4] == "1" and const_admin[4] == "1":
        list_const.append("votre partition disk racine ('/') arrive a saturation") 
        
    # Envoyer l'email
    msg_send = ""
    # voir si il y a des alertes a envoyer
    if len(list_const) > 0:
        # Constitution du message
        for i in list_const:
            msg_send = msg_send + "-->  "
            msg_send = msg_send + i
            msg_send = msg_send + "\n"
        # Sujet du mail    
        Subject_to = "detection d'une situation critique sur votre serveur"
        # Appelle de la fonction mail pour envoyer l'email
        send_mail(mail_admin, Subject_to, msg_send)
        print ("Mail d'alerte envoyer concernant la machine : {0}".format(machine['mac_address']))
        # fin de l'envoie
    else:
        print ("Aucun probleme sur la machine {0}".format(machine['mac_address']))
    
