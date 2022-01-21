#!/bin/sh

# check root user
if [ $(id -u) -ne 0 ]
    then echo "Please execute this script as root"
    exit
fi

# install packages
apt-get update
apt-get install -y -qq \
    cron mysql-server \
    python3 python3-dev python3-pip python3-venv python3-wheel \

python3 -m venv venv
. ./venv/bin/activate
pip install wheel
pip install -r requirements.txt

# create users & databases
service mysql start
mysql -u "root" -e \
    "CREATE USER IF NOT EXISTS 'user0'@'%' IDENTIFIED BY 'secret';"`
    `"GRANT ALL PRIVILEGES ON * . * TO 'user0'@'%';"`
    `"FLUSH PRIVILEGES;"
mysql -u "root" -e "CREATE DATABASE IF NOT EXISTS local_reporter;"

cat >> ~/.bash_profile << END
export AIMLAC_CC_MACHINE=34.72.51.59
export AIMLAC_API_KEY=AIMLACkies275001901
export AIMLACKIES_REPORTER_SECRET_KEY=W5Jal+qx9vOh8gjaugNZPg==
export AIMLACKIES_REPORTER_SECURITY_PASSWORD_SALT=288872824872550364092124909785067926279
export AIMLACKIES_REPORTER_DATABASE_URL=mysql+pymysql://user0:secret@localhost/local_reporter
export FLASK_APP=reporter.py
export FLASK_ENV=development
END

service mysql start

. ./venv/bin/activate
. ~/.bash_profile

export FLASK_APP=reporter.py
export FLASK_ENV=development

flask db upgrade
flask seed