option_spec = {
    "OIDCClient": {
        "PROVIDER_URL": {
            "type": "string",
            "default": "http://127.0.0.1:5002/oauth",
            "envvars": ("KALANFA_OIDC_PROVIDER_URL",),
        },
        "CLIENT_URL": {
            "type": "string",
            "default": "http://localhost:8000",
            "envvars": ("KALANFA_OIDC_CLIENT_URL",),
        },
        "AUTHORIZATION_ENDPOINT": {
            "type": "string",
            "default": "",
            "envvars": ("KALANFA_OIDC_AUTHORIZATION_ENDPOINT",),
        },
        "TOKEN_ENDPOINT": {
            "type": "string",
            "default": "",
            "envvars": ("KALANFA_OIDC_TOKEN_ENDPOINT",),
        },
        "USERINFO_ENDPOINT": {
            "type": "string",
            "default": "",
            "envvars": ("KALANFA_OIDC_USERINFO_ENDPOINT",),
        },
        "ENDSESSION_ENDPOINT": {
            "type": "string",
            "default": "",
            "envvars": ("KALANFA_OIDC_ENDSESSION_ENDPOINT",),
        },
        "JWKS_URI": {
            "type": "string",
            "default": "",
            "envvars": ("KALANFA_OIDC_JWKS_URI",),
        },
    }
}
