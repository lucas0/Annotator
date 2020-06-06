# Veritas Annotator 

Annotator used to construct the Veritas Dataset

Served on [veritas-annotator.datascienceinstitute.ie](veritas-annotator.datascienceinstitute.ie "Veritas Annotator")

Instructions for annotating can be found under [Guidelines](veritas-annotator.datascienceinstitute.ie/guidelines "Annotator Guidelines")

# Instructions for setting up the Annotator service

## Start service in port 5000

python3 manage.py runserver <ip:port>

python3 manage.py runserver 0.0.0.0:5000

## Reset user database

Using ```python manage.py flush```


## Nginx + uWSGI configuration files for virtual server proxy

nginx log: /var/log/nginx

nginx configuration file: /etc/nginx/sites-available/annotator

uWSGI conf file: /etc/uwsgi/sites/annotator.ini

uWSGI service file: /etc/systemd/system/uwsgi.service

if needed to log, change "ExecStart=" line on service file to include --logto <path_to_logfile>

uWSGI socket file: /var/www/Annotator/annotator.sock

## If you use this code, please cite the following publication:

    @inproceedings{azevedo2019veritas,
      title={Veritas annotator: Discovering the origin of a rumour},
      author={Azevedo, Lucas and Moustafa, Mohamed},
      booktitle={Proceedings of the Second Workshop on Fact Extraction and VERification (FEVER)},
      year={2019},
      organization={Association for Computational Linguistics (ACL)}
    }
