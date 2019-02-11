FROM ubuntu:16.04

ENV LISTENING_PORT=80

RUN apt-get update && apt-get install -yy --no-install-recommends \
	git \
	nano \
	nginx \
        fcgiwrap \
        spawn-fcgi \
	python3 \
	python3-pip \
	python3-setuptools \
	python3-github \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global user.email ofp.foundation@gmail.com
RUN git config --global user.name "Github ODP bot"

RUN pip3 install --upgrade pip
RUN pip3 install github3.py
RUN pip3 install python-dotenv

RUN printf "server { \n \
	listen ${LISTENING_PORT} default_server; \n \
	listen [::]:${LISTENING_PORT} default_server; \n \
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

ADD .env /root/

RUN mkdir -p  /var/www/html/html
ADD gh-hook-mr.py /var/www/html/
ADD gh-hook-mr-dpdk.py /var/www/html/

CMD spawn-fcgi -s /var/run/fcgiwrap.socket /usr/sbin/fcgiwrap && chown www-data:www-data /var/run/fcgiwrap.socket && nginx -g 'daemon off;'