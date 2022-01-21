FROM ubuntu:20.04

WORKDIR /workspace
COPY . .

RUN chmod +x install.sh start.sh
RUN ./install.sh

EXPOSE 8080

CMD ./start.sh