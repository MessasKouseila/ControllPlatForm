#/usr/bin/bash
# Execution des sondes afin de recupere les informations utiles dans un fichier
bash sonde1.sh > info_sonde
python sonde2.py >> info_sonde
python sonde3.py >> info_sonde
# Recuperation des donnée utile à inserer dans la base de donnée
avg_cpu=`grep "Utilisation moyenne des cpu" info_sonde | cut -d ':' -f2`
tmp_cpu=`grep "Temperature du cpu (°C)" info_sonde | cut -d ':' -f2`
ram_total=`grep "Quantite de RAM totale (Go)" info_sonde | cut -d ':' -f2`
ram_used=`grep "Quantite de RAM utilise (%)" info_sonde | cut -d ':' -f2`
swap_total=`grep "Mémoire Swap totale (Go)" info_sonde | cut -d ':' -f2`
swap_used=`grep "Mémoire Swap used (%)" info_sonde | cut -d ':' -f2`
nb_process=`grep "Nombre de processus en cours" info_sonde | cut -d ':' -f2`
user_connect=`grep "Nombre de users connecte" info_sonde | cut -d ':' -f2`
physical_core=`grep "Nombre de processeur physique" info_sonde | cut -d ':' -f2`
logical_core=`grep "Nombre de processeur logique" info_sonde | cut -d ':' -f2`
disk_total=`grep "Capacite partition racine (Go)" info_sonde | cut -d ':' -f2`
disk_usage=`grep "Capacite partition racine utilise (%)" info_sonde | cut -d ':' -f2`
# Insertion d'une ligne dans le fichier qui sauvegarde les données des sondes

echo "$avg_cpu $tmp_cpu $ram_total $ram_used $swap_total $swap_used $nb_process $user_connect $physical_core $logical_core $disk_total $disk_usage" > info_sonde