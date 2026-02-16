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

RUN curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh

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

RUN install -d -o django -g django $APP_HOME

ARG ENV_GROUP=prod
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# --------------------
# Python deps
# --------------------
COPY --chown=django:django pyproject.toml uv.lock $APP_HOME/
RUN uv sync --group $ENV_GROUP --frozen

# --------------------
# App code
# --------------------
COPY --chown=django:django ./. $APP_HOME/

# --------------------
# Entrypoints
# -------
COPY --chown=django:django docker/web/webdev_start.sh /usr/local/bin/web_start.sh
#COPY docker/web/webdev_start.sh /usr/local/bin/webdev_start.sh

RUN sed -i 's/\r$//g' /usr/local/bin/*.sh \
 && chmod +x /usr/local/bin/*.sh

## --------------------
## Celery dirs
## --------------------
RUN install -d -o django -g django /var/run/celery /var/log/celery

USER django

# --------------------
# Default entrypoint
# --------------------
ENTRYPOINT ["web_start.sh"]
