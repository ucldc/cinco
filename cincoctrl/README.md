# cincoctrl

Cinco Control: finding aids imports for OAC5

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: BSD

## Project details

### Project generation options

- project_name: Cinco Control
- project_slug: cincoctrl
- description:
- author_name: CDL
- email:
- username_type: email
- domain_name: oac5.cdlib.org (fake should be updated)
- version:
- open_source_license: BSD
- timezone: US/Pacific
- windows: n
- editor: VS Code
- use_docker: y
- postgresql_version: 16
- cloud_provider: AWS
- mail_service: Amazon SES
- use_async: n
- use_drf: n
- frontend_pipeline: None
- use_celery: n
- use_mailpit: n
- use_sentry: y
- use_whitenoise: n
- use_heroku: n
- ci_tool: Github Actions
- keep_local_envs_in_vcs: n
- debug: n

### Environment variables

A list of [all  possible settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html) is part of the cookiecutter documentation.  All the variables listed in the first two tables apply to this project plus `DJANGO_AWS_*` and `SENTRY_*`.

### Dependencies

- Django 5.0.9
- Postgres 16
- Allauth - consider removing, not sure if it's really doing anything for us
- Gunicorn
- Sentry (logging)

## Basic Setup

### Get the code

```
git clone
cd cinco/cincoctrl
```

### Virtualenv
Even if you are planning to primarily use the docker container for development it's probably a good idea to setup a virtual environment for the cincoctrl (or maybe for the entire cinco project) to contain additional tools

- (Install pyenv)[https://github.com/pyenv/pyenv]
- (Install pyenv-virtualenv)[https://github.com/pyenv/pyenv-virtualenv]

```
pyenv install 3.12.6
pyenv virtualenv 3.12.6 cincoctrl-env
pyenv local cincoctrl-env
```

### Prerequisites
    - Docker: [installation instructions](https://docs.docker.com/install/#supported-platforms)
    - Docker Compose: [installation instructions](https://docs.docker.com/compose/install/)
    - Pre-commit: [installation instructions](https://pre-commit.com/#install

```
pre-commit install
```

### Docker Development

The development environment can be setup using docker.

Run the development environment:

```
docker compose -f docker-compose.local.yml up
```

Run the production environment:

```
docker compose -f docker-compose.production.yml
```


https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally-docker.html

The commands below can be run like:

```
docker compose -f docker-compose.local.yml run --rm django <cmd>
```

### Local development

Cookiecutter django also allows development without using docker.  After initializing the virtualenv as above you can continue with the instructions at 4:

[Local development instructions](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html)

### Test ARK minting

If you need to test ark minting for finding aids, set `DISABLE_ARK_MINTING` to False in config/settings/local.py

Also set the following env vars:

```
CDL_ARK_NAAN=99999              # testing naan
CDL_ARK_SHOULDER=fk4            # testing shoulder
EZID_ENDPOINT=https://ezid.cdlib.org
EZID_USERNAME=                  # ask for username
EZID_PASSWORD=                  # ask for password
```

# Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy cincoctrl

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

By default tests are run with the `--reuse-db` option this can sometimes cause some problems if your db migrations have changed you can run with the `--create-db` option to override.

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

The following details how to deploy this application.

### Docker

See detailed [cookiecutter-django Docker documentation](https://cookiecutter-django.readthedocs.io/en/latest/3-deployment/deployment-with-docker.html).

### Management commands

`import_repositories <filepath>` -  Imports repositories from an OAC4 export:
```
python ./manage.py dumpdata oac --natural-foreign --indent=4 > /tmp/repositories.json
```
`import_ead <url> (--docurl)` - Imports and EAD file from the given url. `--docurl` can be used to change the location that the command uses to download documents linked in the EAD (default: "https://cdn.calisphere.org").
`import_record_express <filepath>` - Imports express records from an OAC4 export:
```
python ./manage.py dumpdata oac.institution collection_record --indent=4 > /tmp/record_express.json
```
`import_dublincore <filepath>` - Imports Creator and Subject terms to express records.
```
python ./manage.py dumpdata dublincore --indent=4 > /tmp/dublincore.json
```

`import_repositories` should be run before any of the other imports.
`import_record_express` should be run before `import_dublincore`.
