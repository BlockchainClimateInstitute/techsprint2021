#FROM python:3.7-slim-buster
FROM tiangolo/uwsgi-nginx-flask:python3.8

# Installing key dependencies
RUN apt-get update \
    && apt-get --yes --no-install-recommends install \
        python3-dev \
        python3-pip python3-venv python3-wheel python3-setuptools \
        build-essential cmake \
        graphviz git openssh-client \
        postgresql-contrib \
        libssl-dev libffi-dev libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

#ENV LISTEN_PORT 5000

#EXPOSE 5000

COPY ./app /app

CMD [ "python", "app/main.py" ]


#CMD ["python3", "-m", "main", "--host=0.0.0.0", "--port=5000"]

#COPY . .  /This had problems

#CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5000"]
#CMD ["uwsgi", "wsgi.ini"]
