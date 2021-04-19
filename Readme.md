# Formularium backend
The django backend for formularium.

## Development

### Prerequisites
Make sure you have the following tools installed:

* git
* python (3.8.*) and pip
* pipenv
* sqlite3


### Django Setup

#### Setup on the local machine


##### Install requirements
- create a virtualenv (pls. use pipenv)
- install requirements ``pipenv install``
- ``pipenv run pre-commit install``


##### Setup Database
- setup database `./manage.py migrate`
- setup superuser `./manage.py createsuperuser`
- run application ^^ `./manage.py runserver` (this will start a webserver on port 8000)

#### Alternatively: Setup using Docker Compose

**TODO**

#### Usage
- login to the [admin panel](http://127.0.0.1:8000/admin/)
- configure [oauth credentials](http://127.0.0.1:8000/oauth/applications/)  for the frontend
- add them to the frontend
- add users via the admin panel
- build forms! 