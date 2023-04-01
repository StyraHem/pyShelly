FROM --platform=linux/amd64 python:3.8.6-alpine
ADD https://github.com/Yelp/dumb-init/releases/download/v1.2.0/dumb-init_1.2.0_amd64 /usr/local/bin/dumb-init
RUN chmod +x /usr/local/bin/dumb-init
RUN apk add --update --upgrade gcc musl-dev python3-dev libffi-dev openssl-dev cargo make jq curl
RUN pip install --upgrade pip
ADD run.py setup.py requirements.txt /
ADD pyShelly /pyShelly
RUN pip3 install -r ./requirements.txt
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat
ENTRYPOINT ["dumb-init", "/docker-entrypoint.sh"]