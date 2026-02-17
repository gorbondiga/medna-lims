# MeDNA-LIMS

## Installation

- **Read the Docs**: https://medna-metadata.readthedocs.io/en/latest/

## 1. Prerequisites

- Docker and Docker Compose installed
- Git must be installed with version >= 2.0.0
- (Optional) Nginx installed for reverse proxy
- (Optional) Certbot for SSL certificates

## 2. Installation Options

### Option A: Standard Docker Deployment (No Serverless, No SSL)


1. Copy only the `docker` folder from this repository to your deployment server. You can do this using one of the following methods:

    **A. Using git sparse-checkout (recommended):**
    ```
    git clone --filter=blob:none --no-checkout https://github.com/your-org/medna-lims.git
    cd medna-lims
    git sparse-checkout init --cone
    git sparse-checkout set docker
    cd docker
    ```

    **B. Manual copy (if you already have the repo):**
    ```
    cp -r docker /path/to/your/deployment/
    cd /path/to/your/deployment/docker
    ```

2. Edit environment files in the `docker/` folder as needed.

    **medna.env.db**
    ```
    POSTGRES_USER=<USERNAME>
    POSTGRES_PASSWORD=<PASSWORD>
    POSTGRES_DB=<DB_NAME>
    ```

    **django.env**
    django.env file credentials are used in order to connect the application to the DB. These credentials must match the Postgres User, Password and DB name defined above.
    ```
    DJANGO_DATABASE_NAME=
    DJANGO_DATABASE_USERNAME=
    DJANGO_DATABASE_PASSWORD=
    DJANGO_DATABASE_HOST=medna_metadata_pgdb
    DJANGO_DATABASE_PORT=5432
    ```

    Second part of django.env credentials define the admin username, email and password. As well as django secret key.
    ```
    DJANGO_SUPERUSER_PASSWORD=
    DJANGO_SUPERUSER_USERNAME=
    DJANGO_SUPERUSER_EMAIL=
    DJANGO_SECRET_KEY=
    ```

    **medna.env**
    medna.env contains general installation variables. For fresh installation all should be set to `on`.
    ```
    DJANGO_MANAGEPY_MIGRATE=on
    DJANGO_DATABASE_FLUSH=on
    DJANGO_SUPERUSER_CREATE=on
    DJANGO_DEFAULT_GROUPS_CREATE=on
    DJANGO_DEFAULT_USERS_CREATE=on
    ```

3. Start the application:

    Remember that for the No Serverless, No SSL installation docker-compose.dev.yml is used.

    ```
    docker compose -f docker-compose.dev.yml up -d
    ```

4. Access the application at `http://localhost:8000` (or your configured port).

---

## 3. Additional Notes

- For production, review `CSRF_TRUSTED_ORIGINS = ['http://localhost:8000']` as the name of the host should be added to the list, if it is https or http should be defined.
- For custom deployments (e.g., with serverless or cloud), refer to the [Read the Docs](https://medna-metadata.readthedocs.io/en/latest/).


## Reference work

Kimble, M., Allers, S., Campbell, K., Chen, C., Jackson, L. M., King, B. L., Silverbrand, S., York, G., & Beard, K. (2022).
**medna-metadata: An open-source data management system for tracking environmental DNA samples and metadata.** *Bioinformatics*, btac556.
https://doi.org/10.1093/bioinformatics/btac556

This repository was built from the medna-metadata [repository](https://github.com/melkimble/medna-metadata).
