FROM ethereum/client-go

USER root
ADD . /usr/src/app
WORKDIR /usr/src/app

ENV LANG C.UTF-8
RUN apk add --no-cache ca-certificates python3 python3-dev gcc linux-headers libc-dev bash
RUN pip3 install --upgrade pip
RUN pip3 install -U setuptools

RUN pip3 install -r requirements.txt

USER geth

ENTRYPOINT ["bash", "-c", "gunicorn app:app --daemon && geth $@"]