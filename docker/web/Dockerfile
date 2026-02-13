FROM python:3.13-slim

# --------------------
# Environment
# --------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/home/django/medna-metadata \
    HOME=/home/django

# --------------------
# System deps
# --------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# --------------------
# User
# --------------------
RUN useradd -m django

# --------------------
# App dirs
# --------------------
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# --------------------
# Python deps
# --------------------
COPY docker/web/requirements/ $APP_HOME/requirements/
RUN pip install --upgrade pip "setuptools<65" wheel \
 && pip install --no-cache --no-build-isolation -r requirements/prod.txt

# --------------------
# App code
# --------------------
COPY ./. $APP_HOME/

# --------------------
# Entrypoints
# -------
COPY docker/web/webdev_start.sh /usr/local/bin/web_start.sh
#COPY docker/web/webdev_start.sh /usr/local/bin/webdev_start.sh

RUN sed -i 's/\r$//g' /usr/local/bin/*.sh \
 && chmod +x /usr/local/bin/*.sh

## --------------------
## Celery dirs
## --------------------
RUN mkdir -p /var/run/celery /var/log/celery \
 && chown -R django:django /var/run/celery /var/log/celery \
 && chown -R django:django /home/django

USER django

# --------------------
# Default entrypoint
# --------------------
ENTRYPOINT ["web_start.sh"]
