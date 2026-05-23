import os
from app import create_app
from app.extensions import db, migrate
from flask.cli import FlaskGroup

app = create_app()
cli = FlaskGroup(app)

if __name__ == '__main__':
    cli()