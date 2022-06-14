SETTINGS_SCHEMA = {
    # Widget bundles jsoneditor 9.1.9
    # https://github.com/josdejong/jsoneditor/blob/v9.1.9/package.json
    # which is built with ajv 6.12.6
    # https://github.com/ajv-validator/ajv/tree/v6.12.6
    # which only support draft-07
    # "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://okfn.de/software/filingcabinet.portal.schema.json",
    "title": "Portal Settings",
    "description": "Settings of a filingcabinet portal",
    "type": "object",
    "properties": {
        "preferences": {
            "description": "list of UI preferences",
            "type": "object",
            "properties": {
                "showSearch": {"type": "boolean"},
                "allowToggleSearch": {"type": "boolean"},
            },
        },
        "filters": {
            "description": "list of filters",
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "pattern": "choice|daterange"},
                    "key": {"type": "string"},
                    "facet": {"type": "boolean"},
                    "facet_config": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "interval": {"type": "string"},
                            "format": {"type": "string"},
                        },
                    },
                    "label": {
                        "type": "object",
                        "minProperties": 1,
                        "propertyNames": {"pattern": "^[a-z]{2}$"},
                        "patternProperties": {"^[a-z]{2}$": {"type": "string"}},
                    },
                    "datatype": {"type": "string"},
                    "choices": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "value": {"type": ["number", "string"]},
                                "label": {
                                    "type": "object",
                                    "minProperties": 1,
                                    "propertyNames": {"pattern": "^[a-z]{2}$"},
                                    "patternProperties": {
                                        "^[a-z]{2}$": {"type": "string"}
                                    },
                                },
                            },
                            "required": ["value"],
                        },
                    },
                },
                "required": ["id", "key", "type", "label"],
            },
        },
    },
}
