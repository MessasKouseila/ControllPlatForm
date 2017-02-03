#!/usr/bin/bash

# free affiche des resultat different celon la distribution utilise
aff()
{	# resultat afficher sur une distribution linux mint 17.3
	teste_name=`free | grep Swap`
	if [ "${#teste_name}" -eq 0 ]; then
		teste_name=`free | grep "Partition d'échange"`;
		swap_total=`echo $teste_name | awk '{print $3}'`
		swap_total=$(($swap_total / (1024*1024) ))
		echo "Mémoire Swap totale (Go) : $swap_total"

		swap_used=`echo $teste_name | awk '{print $4}'`
		swap_used=$(( $swap_used / (1024*1024) ))
		echo "Mémoire Swap utilise : $swap_used Go"

		swap_percent=$(($swap_used*100/$swap_total))
		echo "Mémoire Swap used (%) : $swap_percent"

		swap_free=`echo $teste_name | awk '{print $5}'`
		swap_free=$(($swap_free / (1024*1024) ))
		echo "Mémoire Swap disponible : $swap_free Go"
	else
		# resultat afficher sur une distribution linux ubuntu 16.04 lts avec bureau mint
		# les infos sont extraite celon leur ordre d'affichage et non plus celon leur nom
		# avec cette methode d'extraction, le script est normalement capable d'extraire l'info sur n'importe quel distribution
		# tant que l'ordre d'affichage des informations n'est pas modifier
		swap_total=`echo $teste_name | awk '{print $2}'`
		swap_total=$(($swap_total / (1024*1024) ))
		echo "Mémoire Swap totale (Go) : $swap_total"

		swap_used=`echo $teste_name | awk '{print $3}'`
		swap_used=$(( $swap_used / (1024*1024) ))
		echo "Mémoire Swap utilise : $swap_used Go"

		swap_percent=$(($swap_used*100/$swap_total))
		echo "Mémoire Swap used (%) : $swap_percent"

		swap_free=`echo $teste_name | awk '{print $4}'`
		swap_free=$(($swap_free / (1024*1024) ))
		echo "Mémoire Swap disponible : $swap_free Go"	
	fi
}	