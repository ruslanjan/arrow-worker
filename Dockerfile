############################################################
# Dockerfile to build sandbox for executing user code
############################################################

FROM ubuntu:18.04
# FROM alpine:3.7
USER root

# Update the repository sources list
# RUN echo "deb http://archive.ubuntu.com/ubuntu trusty main universe" > /etc/apt/sources.list
# also install needed deps
RUN apt update -y && apt upgrade -y && \
    apt install -y bash \
                   g++ \ 
                   python \
                   python3 \
                   python3-pip \
                   curl \ 
                   sudo \
                   coreutils \
                   bc \
                   make \
                   libcap-dev

#prepare for Java download
# RUN apt install python-software-properties
# RUN apt install software-properties-common

#grab oracle java (auto accept licence)
# RUN install-apt-repository ppa:webupd8team/java
# RUN apt update
# RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
# RUN apt install openjdk8-jre
#RUN apt install -y openjdk-8-jdk
#ENV PATH="/usr/lib/jvm/java-1.8-openjdk/bin:${PATH}"


# pip3
#RUN apt install -y python3-pip
#RUN apt install -y patchelf
#RUN pip3 install pyinstaller
#RUN pip3 install staticx

ENV PATH="/bin:${PATH}"

RUN useradd -ms /bin/bash dummy
# user for sandbox scripts
COPY isolate /isolate
RUN sh /isolate/install.sh

# RUN echo "mysql ALL = NOPASSWD: /usr/sbin/service mysql start" | cat >> /etc/sudoers
RUN echo "export PATH=$PATH" > /etc/environment

COPY . /app/

# Run install.sh
RUN sh /app/Setup/install.sh

# Run container
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV FLASK_APP=app.py

CMD sh /app/run.sh
