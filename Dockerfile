###########
# BUILDER #
###########
# Build Docker image
#
# 1. From windows command line change directory to directory with this file
# 2. Run docker build: docker build -t  wsdotdev.azurecr.io/ptd_report:latest . OR  docker build -t wsdotprod.azurecr.io/ptd_report:latest .
# 3. Run docker image: docker run -p 8000:8000 [image id]  Image id comand: docker image ls
#
# PUSH to Auzure CR
#
# 1. Log in to azure: az login
# 2. Log into Azure container registry: az acr login --name wsdotdev  OR  az acr login --name wsdotprod
# 3. Push image: docker push wsdotdev.azurecr.io/ptd_report:latest OR docker push wsdotprod.azurecr.io/ptd_report:latest
#
# Run Image on Azure
#
# 1. Got to Azure app services portal page
# 2. Stop and restart app
###########

# pull official base image
FROM alpine:3.10 as builder

# set work directory
WORKDIR /usr/src/PublicTransitDataReportingPortal

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.10/main' >> /etc/apk/repositories
RUN apk update
RUN apk add gcc musl-dev g++ unixodbc-dev python3-dev jpeg-dev zlib-dev libffi-dev cairo-dev pango-dev gdk-pixbuf-dev libxslt-dev

#RUN apk add gcc python3-dev musl-dev

# lint
RUN pip3 install --upgrade pip
RUN pip3 install cython
RUN pip3 install --upgrade cython

# RUN pip install flake8
COPY . /usr/src/PublicTransitDataReportingPortal/
# RUN flake8 --ignore=E501,F401 .

# install dependencies
COPY ./requirements.txt .
RUN pip3 install wheel
RUN pip3 wheel --no-cache-dir --no-deps --wheel-dir /usr/src/PublicTransitDataReportingPortal/wheels -r requirements.txt


#########
# FINAL #
#########

# pull official base image
FROM alpine:3.10

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
RUN echo 'http://dl-cdn.alpinelinux.org/alpine/v3.10/main' >> /etc/apk/repositories
RUN apk add openssl-dev zlib-dev jpeg-dev
RUN apk add gcc musl-dev libffi-dev xmlsec g++ py-pip unixodbc-dev gnupg curl python3-dev jpeg-dev zlib-dev libffi-dev cairo-dev pango-dev gdk-pixbuf-dev libxslt-dev
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -U pip
RUN pip3 install cryptography==2.8 wheel
#RUN pip install django_saml2_auth
#RUN apk del openssl-dev
RUN apk --no-cache add msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f

RUN curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.5.2.2-1_amd64.apk
#RUN curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/mssql-tools_17.5.2.2-1_amd64.apk

RUN apk add --allow-untrusted msodbcsql17_17.5.2.2-1_amd64.apk
#RUN apk add --allow-untrusted mssql-tools_17.5.2.2-1_amd64.apk

COPY --from=builder /usr/src/PublicTransitDataReportingPortal/wheels /wheels
COPY --from=builder /usr/src/PublicTransitDataReportingPortal/requirements.txt .
#RUN pip3 install --upgrade pip
RUN pip3 install --no-cache /wheels/*
RUN pip3 install django-rest-auth


# copy entrypoint-prod.sh
COPY ./entrypoint.prod.sh $APP_HOME

#Copy SAML keys and metadata
COPY ./mycert.pem /usr/bin
COPY ./mykey.pem /usr/bin
COPY ./sawidp_WaTech_metadata_TEST.xml /usr/bin
COPY ./sawidp_WaTech_metadata_PROD.xml /usr/bin

#Copy vanpool email task files
#RUN mkdir -p /home/PublicTransitDataReportingPortal/vanpool_email
#COPY ./vanpool_email_cron_job.sh /home/PublicTransitDataReportingPortal/vanpool_email
#RUN chmod +x /home/PublicTransitDataReportingPortal/vanpool_email

# Create the log file to be able to run tail
#RUN touch /var/log/cron.log

#RUN crond -f -l 8

#TODO move files up one level so they dont get copied to project.
# copy project
COPY . $APP_HOME

# chown all the files to the app user
#RUN chown -R PublicTransitDataReportingPortal:PublicTransitDataReportingPortal $APP_HOME
#RUN chown -R PublicTransitDataReportingPortal:PublicTransitDataReportingPortal /home/PublicTransitDataReportingPortal/vanpool_email

## grant user cron permissions
#RUN touch /etc/cron.allow

#USER PublicTransitDataReportingPortal

EXPOSE 8000

# run entrypoint.prod.sh
ENTRYPOINT ["/home/PublicTransitDataReportingPortal/web/entrypoint.prod.sh"]