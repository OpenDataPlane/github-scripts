FROM ubuntu:16.04

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
	git \
	git-email \
	nginx \
        fcgiwrap \
        spawn-fcgi \
	python \
	cron \
	vim \
	openssh-server \
	python-pip python-setuptools python-github python-imaplib2 \
	procmail

RUN git config --global user.email odpbot@yandex.ru
RUN git config --global user.name "Github ODP bot"

RUN pip install --upgrade pip
RUN pip install github3.py
RUN pip install python-bugzilla

RUN git clone https://github.com/muvarov/githubscripts.git /githubscripts \
    && echo "#!/bin/bash \n \
      git clone https://github.com/muvarov/githubscripts.git \n \
      cd githubscripts \n \
      git pull \n  \
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

RUN mkdir ~/.ssh && mkdir -p /var/run/sshd
RUN echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDPZDbZna+kTmX+M4NABTfUDu3RYPYe9adfUdwCnZhv+dJsKSNG0udzkHQo4BvXDVjeQLeN3lRLUjRTe/sZ76lWkXk32fRZBXUL8N1mKaVU9hCURCnGvM+n0BDRtagMU8dpl/BOgHY+D5XAyqoY2VoAZHqS94RPnEXlEDJMFtCzYQPjqftLA+Z3N2h6kJ9ftjHEaMmLLz9/vIugqRsMvBPLfACSDLuU6qo5fyDqgumyFssKsu8T8OMMf2pzkNdBTh8Fnh8+2Cn5ON1WHK03rhj17FKP8fpIA1wS6n+tBYZY6IcNyMyu0gbiySwiCUZZBbOYEXcIMc61gZMH0KrdHpZT muvarov@maxim-desktop >> ~/.ssh/authorized_keys

CMD spawn-fcgi -s /var/run/fcgiwrap.socket /usr/sbin/fcgiwrap && chown www-data:www-data /var/run/fcgiwrap.socket && cron && nginx && /usr/sbin/sshd -D
