#!/bin/bash

echo -n \
"export AIMLAC_CC_MACHINE=${AIMLAC_CC_MACHINE}\n\
export AIMLAC_API_KEY=${AIMLAC_API_KEY}\n\
export AIMLACKIES_REPORTER_SECRET_KEY=${AIMLACKIES_REPORTER_SECRET_KEY}\n\
export AIMLACKIES_REPORTER_SECURITY_PASSWORD_SALT=${AIMLACKIES_REPORTER_SECURITY_PASSWORD_SALT}\n\
export AIMLACKIES_REPORTER_DATABASE_URL=mysql+pymysql://user0:secret@localhost/local_reporter\n\
export FLASK_APP=reporter.py\n\
export FLASK_ENV=development" > ~/.bash_profile

. ~/.bash_profile

service mysql start
service cron start
crontab crontab.bak

flask run -h 0.0.0.0 -p 8080