#!/bin/sh

#python manage.py migrate
python manage.py collectstatic --no-input --clear

gunicorn -b 0.0.0.0:8000 TransitData.wsgi:application
exec "$@"


#echo "testing email command"
#python3 manage.py vanpool_monthly_email
#
#echo "testing shell file"
#sh /home/PublicTransitDataReportingPortal/vanpool_email/vanpool_email_cron_job.sh
#
##cd /home/PublicTransitDataReportingPortal/web
##chmod +x vanpool_email_cron_job.sh
#
#
##echo "Starting Cron"
##crond -f -L /dev/stdout
#
##echo "Starting scheduled job.."
###echo "*       *       *       *       *       sh /home/PublicTransitDataReportingPortal/vanpool_email/vanpool_email_cron_job.sh" | crontab - #&& crond -f -L /dev/stdout
##echo "*       *       15       *       *       sh /home/PublicTransitDataReportingPortal/vanpool_email/vanpool_email_cron_job.sh" | crontab - #&& crond -f -L /dev/stdout
##crond -f -L /dev/stdout
#
#echo "collecting static files"
#python3 manage.py collectstatic --no-input --clear
#
#gunicorn -b 0.0.0.0:8000 TransitData.wsgi:application
##su PublicTransitDataReportingPortal
#exec "$@"
