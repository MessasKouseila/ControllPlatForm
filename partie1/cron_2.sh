#!/usr/bin/bash

crontab -l | egrep -v 'partie1' > crontab_client