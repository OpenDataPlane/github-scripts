FROM linaroodpcheckv2:linaroodpcheck_v2

RUN apt-get update

RUN apt-get install -yy \
	git \
	nginx \
	python \
	cron \
	vim \
	python-pip python-setuptools python-github python-imaplib2

RUN pip install --upgrade pip
RUN pip install github3.py

RUN echo "#!/bin/bash \n \
	git clone https://github.com/muvarov/githubscripts.git \n \
	cd githubscripts \n \
	python gh-mail-pr.py \n  \
	sleep 5 \n \
	python gh-mail-pr-dpdk.py \n \
	sleep 5 \n \
	python gh-imap.py \n \
	sleep 5 \n \
	python gh-checkpatch.py \n \
	sleep 5 \n \
	python gh-email-comments.py \n " \
	> cron_job.sh

RUN chmod +x /cron_job.sh

RUN ln -s /githubscripts/gh-hook-bugzilla.py  /usr/share/nginx/html/gh-hook-bugzilla.py
RUN ln -s /githubscripts/gh-hook-mr.py  /usr/share/nginx/html/gh-hook-mr.py

RUN echo "0 * * * * /cron_job.sh" > /var/spool/cron/crontabs/root
