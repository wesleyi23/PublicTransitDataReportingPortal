###########
# BUILDER #
###########

# pull official base image
FROM python:3.8.0-alpine as builder

# set work directory
WORKDIR /usr/src/PublicTransitDataReportingPortal

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install psycopg2 dependencies
RUN apk update \
    && apk add gcc python3-dev musl-dev

# lint
RUN pip install --upgrade pip
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
FROM python:3.8.0-alpine

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
COPY --from=builder /usr/src/PublicTransitDataReportingPortal/wheels /wheels
COPY --from=builder /usr/src/PublicTransitDataReportingPortal/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

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