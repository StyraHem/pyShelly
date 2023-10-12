FROM python:3.8.6-alpine
RUN apk add --update --upgrade gcc musl-dev make g++ libffi-dev file dumb-init
RUN pip install --upgrade pip
ADD run.py setup.py requirements.txt /
ADD pyShelly /pyShelly
RUN pip3 install -r ./requirements.txt
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat
ENTRYPOINT ["dumb-init", "/docker-entrypoint.sh"]