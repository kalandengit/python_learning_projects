from kalanfa.core.content.apps import KalanfaContentConfig


class ContentSchemaConfig(KalanfaContentConfig):
    name = "kalanfa.core.content.contentschema"

    def ready(self):
        pass
