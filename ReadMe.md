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


---

Please cite the published articles related to this work:

Azevedo, Lucas, et al. "LUX (Linguistic aspects Under eXamination): Discourse Analysis for Automatic Fake News Classification." Findings of the Association for Computational Linguistics: ACL-IJCNLP 2021. 2021.

    @inproceedings{azevedo2021lux,
      title={LUX (Linguistic aspects Under eXamination): Discourse Analysis for Automatic Fake News Classification},
      author={Azevedo, Lucas and d’Aquin, Mathieu and Davis, Brian and Zarrouk, Manel},
      booktitle={Findings of the Association for Computational Linguistics: ACL-IJCNLP 2021},
      pages={41--56},
      year={2021}
    }

Azevedo, Lucas, and Mohamed Moustafa. "Veritas annotator: Discovering the origin of a rumour." Proceedings of the Second Workshop on Fact Extraction and VERification (FEVER). 2019.

    @inproceedings{azevedo2019veritas,
      title={Veritas annotator: Discovering the origin of a rumour},
      author={Azevedo, Lucas and Moustafa, Mohamed},
      booktitle={Proceedings of the Second Workshop on Fact Extraction and VERification (FEVER)},
      pages={90--98},
      year={2019}
    }

Azevedo, Lucas. "Truth or lie: Automatically fact checking news." Companion Proceedings of the The Web Conference 2018. 2018.

    @inproceedings{azevedo2018truth,
      title={Truth or lie: Automatically fact checking news},
      author={Azevedo, Lucas},
      booktitle={Companion Proceedings of the The Web Conference 2018},
      pages={807--811},
      year={2018}
    }
