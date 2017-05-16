FROM ubuntu:trusty

MAINTAINER Xicheng Chang <mr.xchang@gmail.com>

# nginx and uwsgi plugin
RUN apt-get update && \
    apt-get -y install \
    curl \
    python-dev \
    nginx \
    supervisor \
    uwsgi \
    python-virtualenv

# install mongodb
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6 && \
    echo "deb [ arch=amd64 ] http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list && \
    apt-get update && \
    apt-get install -y mongodb-org
RUN mkdir -p /data/db

# install pip
ENV PYTHON_PIP_VERSION 8.1.2
RUN curl -SL 'https://bootstrap.pypa.io/get-pip.py' | python \
    && pip install --upgrade pip==$PYTHON_PIP_VERSION && \
    pip install uwsgi

# setup venv
RUN mkdir -p /var/www/statusreport && \
    cd /var/www/statusreport && \
    virtualenv venv

# setup nginx
RUN rm /etc/nginx/sites-enabled/default
COPY conf/stack360.conf /etc/nginx/sites-available
RUN ln -s /etc/nginx/sites-available/stack360.conf /etc/nginx/sites-enabled/stack360.conf
COPY conf/statusreport_uwsgi.ini /var/www/statusreport
COPY conf/virtual.conf /etc/nginx/conf.d/
COPY conf/statusreport_nginx.conf /var/www/statusreport
RUN ln -s /var/www/statusreport/statusreport_nginx.conf /etc/nginx/conf.d/
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# setup supervisord
RUN mkdir -p /var/log/supervisor
COPY conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# copy code and install python dependencies
COPY . /var/www/statusreport
RUN cd /var/www/statusreport && \
    . venv/bin/activate && \
    pip install -r requirements.txt

# download stack360
RUN apt-get -y install git && cd /root/ && git clone https://github.com/stack360/docs && \
    cp -rf /root/docs/stack360-web /var/www/stack360

# get credentials
RUN apt-get install -y wget && \
    mkdir -p /var/www/.credentials && \
    cd /var/www/.credentials && \
    wget http://www.stack360.io/my-weekly-status.json && \
    cp -rf /var/www/.credentials ~/.credentials && \
    chmod 755 -R /var/www/.credentials

ENV STATUSREPORT_MODE prod
CMD ["/usr/bin/supervisord"]
