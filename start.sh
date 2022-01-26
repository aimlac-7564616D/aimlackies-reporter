#!/bin/bash
. ~/.bash_profile
export FLASK_APP=reporter.py
export FLASK_ENV=development

service mysql start
service cron start
crontab crontab.bak

flask co2_for_time
flask run -h 0.0.0.0 -p 8080