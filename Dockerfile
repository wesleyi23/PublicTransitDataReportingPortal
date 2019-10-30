# pull official base image
FROM python:3.8.0-alpine

# set work directory
WORKDIR /usr/src/PublicTransitDataReportingPortal

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/PublicTransitDataReportingPortal/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/PublicTransitDataReportingPortal/

# run entrypoint.sh
ENTRYPOINT ["/usr/src/PublicTransitDataReportingPortal/entrypoint.sh"]