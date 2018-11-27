
FROM alpine:3.7
USER root


# bash utils
RUN apk add curl
RUN apk add sudo
RUN apk add coreutils
ENV PATH="/bin:${PATH}"
RUN apk add bc
RUN echo "export PATH=$PATH" > /etc/environment

# Nodejs and npm
RUN apk add nodejs

# g++ aka c++
RUN apk add g++

# python2 and python3
RUN apk add python
RUN apk add python3

# Java8
RUN apk add openjdk8
ENV PATH="/usr/lib/jvm/java-1.8-openjdk/bin:${PATH}"

# Install Docker
RUN apk add docker



COPY . /app/

# Run install.sh
RUN sh /app/Setup/install.sh

# Run container
CMD sh /app/run.sh
