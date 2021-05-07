from django.core.exceptions import ValidationError

from jsonschema import validate
from jsonschema.exceptions import ValidationError as JSValidationError

from .schema import SETTINGS_SCHEMA


def validate_settings_schema(val):
    try:
        validate(val, SETTINGS_SCHEMA)
    except JSValidationError as e:
        raise ValidationError(str(e))
