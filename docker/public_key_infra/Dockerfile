FROM alpine:latest

LABEL maintainer="Tommy Béland <blnd.tommy@gmail.com>"

RUN apk update && \
    apk upgrade && \
    apk add bash openssl vim file && \
    NEWUSER='crypto' && \
    adduser -D -u 1500 -s /bin/bash -h /home/$NEWUSER $NEWUSER $NEWUSER && \
    cd /home/$NEWUSER && \
    mkdir certs crl newcerts private intermediate && \
    chmod 700 private && \
    touch /home/$NEWUSER/index.txt && \
    echo 1000 > /home/$NEWUSER/serial && \
    cd /home/$NEWUSER/intermediate && \
    mkdir certs crl csr newcerts private && \
    chmod 700 /home/$NEWUSER/intermediate/private && \
    touch /home/$NEWUSER/intermediate/index.txt && \
    echo 1000 > serial && \
    echo 1000 > /home/$NEWUSER/intermediate/crlnumber

COPY ./pki /usr/local/bin

COPY --chown=1500:1500 ./root-openssl.cnf /home/crypto

COPY --chown=1500:1500 ./intermediate-openssl.cnf /home/crypto/intermediate

RUN chmod a+x /usr/local/bin/* && \
    chown -R crypto:crypto /home/crypto

USER crypto

WORKDIR /home/crypto
