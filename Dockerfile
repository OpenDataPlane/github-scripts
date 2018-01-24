FROM ubuntu:16.04

RUN apt-get update \
    && apt-get install -yy \
	git \
	nginx \
        fcgiwrap \
        spawn-fcgi \
	python \
	cron \
	vim \
	python-pip python-setuptools python-github python-imaplib2

RUN pip install --upgrade pip
RUN pip install github3.py

RUN git clone https://github.com/muvarov/githubscripts.git /githubscripts \
    && echo "#!/bin/bash \n \
      git clone https://github.com/muvarov/githubscripts.git \n \
      python gh-mail-pr.py \n  \
      sleep 5 \n \
      python gh-mail-pr-dpdk.py \n \
      sleep 5 \n \
      python gh-imap.py \n \
      sleep 5 \n \
      python gh-checkpatch.py \n \
      sleep 5 \n \
      python gh-email-comments.py \n " \
      > cron_job.sh \
    && chmod +x /cron_job.sh

RUN echo "server { \n \
	listen 80 default_server; \n \
	listen [::]:80 default_server; \n \
	root /var/www/html; \n \
	index index.html index.htm; \n \
	server_name _; \n \
	\n \
	location / { \n \
		try_files \$uri \$uri/ =404; \n \
                fastcgi_split_path_info ^(.+\.php)(/.+)$; \n \
                fastcgi_split_path_info ^(.+\.py)(/.+)$; \n \
                fastcgi_pass unix:/var/run/fcgiwrap.socket; \n \
                fastcgi_index index.php; \n \
                include fastcgi_params; \n \
                auth_basic off; \n \
	} \n \
}\n " > /etc/nginx/sites-available/default

RUN ln -s /githubscripts/*.py  /var/www/html/

RUN echo "0 * * * * /cron_job.sh" > /var/spool/cron/crontabs/root

#spawn-fcgi -s /var/run/fcgiwrap.socket /usr/sbin/fcgiwrap && chown www-data:www-data /var/run/fcgiwrap.socket && nginx
