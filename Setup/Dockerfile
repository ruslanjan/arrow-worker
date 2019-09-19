############################################################
# Dockerfile to build sandbox for executing user code
############################################################

FROM ubuntu:18.04
# FROM alpine:3.7
USER root

# Update the repository sources list
# RUN echo "deb http://archive.ubuntu.com/ubuntu trusty main universe" > /etc/apt/sources.list
RUN apt update -y
RUN apt upgrade -y
RUN apt install -y bash
#install all the languages/compilers we are supporting.
RUN apt install -y g++
RUN apt install -y python
RUN apt install -y python3

#prepare for Java download
# RUN apt install python-software-properties
# RUN apt install software-properties-common

#grab oracle java (auto accept licence)
# RUN install-apt-repository ppa:webupd8team/java
# RUN apt update
# RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
# RUN apt install openjdk8-jre
RUN apt install -y openjdk-8-jdk
ENV PATH="/usr/lib/jvm/java-1.8-openjdk/bin:${PATH}"

RUN apt install -y curl

RUN apt install -y sudo
RUN apt install -y coreutils
ENV PATH="/bin:${PATH}"
RUN apt install -y bc
RUN apt install -y make
RUN apt install -y libcap-dev

# pip3
#RUN apt install -y python3-pip
#RUN apt install -y patchelf
#RUN pip3 install pyinstaller
#RUN pip3 install staticx


COPY ./isolate /isolate
RUN sh /isolate/install.sh

# RUN echo "mysql ALL = NOPASSWD: /usr/sbin/service mysql start" | cat >> /etc/sudoers
RUN echo "export PATH=$PATH" > /etc/environment
