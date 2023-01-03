from .base_admin import DocumentBaseAdmin  # noqa

try:
    from fcdocs_annotate.annotation.admin import predict_feature
except ImportError:
    predict_feature = None


if predict_feature:
    DocumentBaseAdmin.predict_feature = predict_feature
    DocumentBaseAdmin.actions += ["predict_feature"]
