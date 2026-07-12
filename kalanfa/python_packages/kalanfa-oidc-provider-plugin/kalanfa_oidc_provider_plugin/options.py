option_spec = {
    "OIDCProvider": {
        "REQUIRE_CONSENT": {
            "type": "boolean",
            "default": True,
            "envvars": ("KALANFA_OIDC_PROVIDER_REQUEST_CONSENT",),
        }
    }
}
