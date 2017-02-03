#!/usr/bin/bash

# si les script sont deja presents, on les supprimes
crontab -l | egrep -v 'partie2' | egrep -v 'partie3' > crontab_control