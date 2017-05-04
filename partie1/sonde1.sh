#!/usr/bin/bash

#nombre de processus en cours d'execution
p1=`ps -aux | wc | awk '{print $1}'`
echo "Nombre de processus en cours : $p1" 

#nombre d'utilisateur connecte
p2=`who -q | wc -l`
echo "Nombre de users connecte : $p2"

#temperature du cpu
temperatur=`sensors |egrep "Core 0:" | awk '{print $3}' | cut -d '.' -f1`

echo "Temperature du cpu (°C) : ${temperatur:1}"