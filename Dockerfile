FROM ubuntu:20.04

WORKDIR /workspace
COPY . .

# install apt packages
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes \
    cron mysql-server libeccodes-dev git \
    python3 python3-dev python3-pip python3-wheel
# install python libraries
RUN pip install -r requirements.txt
# create database and user
RUN service mysql start \
 && mysql -u "root" -e \
    "CREATE USER IF NOT EXISTS 'user0'@'%' IDENTIFIED BY 'secret';\n \
    GRANT ALL PRIVILEGES ON * . * TO 'user0'@'%';\n \
    FLUSH PRIVILEGES;" \
 && mysql -u "root" -e "CREATE DATABASE IF NOT EXISTS local_reporter;"
# write environment variables
RUN echo -n \
"export AIMLAC_CC_MACHINE=34.72.51.59\n\
export AIMLAC_API_KEY=AIMLACkies275001901\n\
export AIMLACKIES_REPORTER_SECRET_KEY=W5Jal+qx9vOh8gjaugNZPg==\n\
export AIMLACKIES_REPORTER_SECURITY_PASSWORD_SALT=288872824872550364092124909785067926279\n\
export AIMLACKIES_REPORTER_DATABASE_URL=mysql+pymysql://user0:secret@localhost/local_reporter\n\
export FLASK_APP=reporter.py\n\
export FLASK_ENV=development" >> ~/.bash_profile
# update flask db
RUN service mysql start \
 && . ~/.bash_profile \
 && export FLASK_APP=reporter.py \
 && export FLASK_ENV=development \
 && flask db upgrade \
 && flask seed

EXPOSE 8080

CMD sh ./start.sh
