FROM ubuntu:16.04

RUN apt-get update --fix-missing

RUN apt-get install -yy --no-install-recommends \
	git \
	git-email \
	nginx \
        fcgiwrap \
        spawn-fcgi \
	python3 \
	cron \
	vim \
	openssh-server \
	python3-pip \
	python3-setuptools \
	python3-github \
	python3-imaplib2 \
	procmail

RUN git config --global user.email ofp.foundation@gmail.com
RUN git config --global user.name "Github ODP bot"

RUN pip3 install --upgrade pip
RUN pip3 install github3.py
RUN pip3 install python-bugzilla

RUN git clone https://github.com/OpenDataPlane/github-scripts.git /githubscripts \
    && echo "#!/bin/bash \n \
      git clone https://github.com/OpenDataPlane/github-scripts.git \n \
      cd githubscripts \n \
      git pull \n  \
      python3 gh-mail-pr.py \n  \
      sleep 5 \n \
      python3 gh-mail-pr-dpdk.py \n \
      sleep 5 \n \
      python3 gh-imap.py \n \
      sleep 5 \n \
      python3 gh-checkpatch.py \n \
      sleep 5 \n \
      python3 gh-email-comments.py \n " \
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
	location /html { \n \
		try_files \$uri \$uri/ =404; \n \
                auth_basic off; \n \
	} \n \
}\n " > /etc/nginx/sites-available/default

RUN mkdir -p  /var/www/html/html
ADD gscripts_config.py /var/www/html/
RUN ln -s /githubscripts/*.py  /var/www/html/
RUN ln -s /githubscripts/html/*.html  /var/www/html/html/


RUN echo "0 * * * * /cron_job.sh" > /var/spool/cron/crontabs/root

CMD spawn-fcgi -s /var/run/fcgiwrap.socket /usr/sbin/fcgiwrap && chown www-data:www-data /var/run/fcgiwrap.socket && cron && nginx
