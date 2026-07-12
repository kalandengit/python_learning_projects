from django.db.models import Model

from kalanfa.core.content import base_models

for model in base_models.__dict__.values():
    if (
        isinstance(model, type)
        and issubclass(model, Model)
        and model.__module__ == "kalanfa.core.content.base_models"
    ):
        type(model.__name__, (model,), {"__module__": __name__})
