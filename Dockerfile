###########
# BUILDER #
###########
# Build Docker image
#
# 1. From windows command line change directory to directory with this file
# 2. Run docker build: docker build -t  wsdotdev.azurecr.io/ptd_report:latest .
# 3. Run docker image: docker run -p 8000:8000 [image id]
#
# PUSH to Auzure CR
#
# 1. Log into Azure container registry: az acr login --name wsdotdev
# 2. Push image: docker push wsdotdev.azurecr.io/ptd_report:latest
#
# Run Image on Azure
#
# 1. Got to app services portal page
# 2. Stop and restart app
###########

# pull official base image
FROM python:3.7.0-alpine as builder

# set work directory
WORKDIR /usr/src/PublicTransitDataReportingPortal

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apk update
RUN apk add gcc python-dev musl-dev

#RUN apk add gcc python3-dev musl-dev

# lint
RUN pip install --upgrade pip
RUN pip install cython
RUN pip install --upgrade cython

# RUN pip install flake8
COPY . /usr/src/PublicTransitDataReportingPortal/
# RUN flake8 --ignore=E501,F401 .

# install dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/PublicTransitDataReportingPortal/wheels -r requirements.txt


#########
# FINAL #
#########

# pull official base image
FROM python:3.7.0-alpine

# create directory for the PublicTransitDataReportingPortal user
RUN mkdir -p /home/PublicTransitDataReportingPortal

# create the app user
RUN addgroup -S PublicTransitDataReportingPortal && adduser -S PublicTransitDataReportingPortal -G PublicTransitDataReportingPortal

# create the appropriate directories
ENV HOME=/home/PublicTransitDataReportingPortal
ENV APP_HOME=/home/PublicTransitDataReportingPortal/web
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
WORKDIR $APP_HOME

# install dependencies
RUN apk update && apk add libpq
RUN apk add openssl-dev
RUN apk add gcc python-dev musl-dev libffi-dev xmlsec
RUN pip install --no-cache-dir -U pip
RUN pip install cryptography==2.8
#RUN pip install django_saml2_auth
#RUN apk del openssl-dev


COPY --from=builder /usr/src/PublicTransitDataReportingPortal/wheels /wheels
COPY --from=builder /usr/src/PublicTransitDataReportingPortal/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*
RUN pip install django-rest-auth


# copy entrypoint-prod.sh
COPY ./entrypoint.prod.sh $APP_HOME

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R PublicTransitDataReportingPortal:PublicTransitDataReportingPortal $APP_HOME

# change to the app user
USER PublicTransitDataReportingPortal

EXPOSE 8000

# run entrypoint.prod.sh
ENTRYPOINT ["/home/PublicTransitDataReportingPortal/web/entrypoint.prod.sh"]