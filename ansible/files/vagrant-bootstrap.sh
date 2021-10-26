#!/usr/bin/env bash

useradd -u 5500 -m -s /bin/bash devops
echo -e 'devops\tALL=(ALL)\tNOPASSWD:\tALL' > /etc/sudoers.d/devops
