### app/template_filters.py

from flask import Blueprint
from apps.shared.wareki import iso_str_to_wareki


def register_template_filters(app):
    app.jinja_env.filters['wareki'] = iso_str_to_wareki
