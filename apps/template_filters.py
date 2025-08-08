### app/template_filters.py

from flask import Blueprint
from apps.utils.datetime_utils import to_japanese_era


def register_template_filters(app):
    app.jinja_env.filters['wareki'] = to_japanese_era
