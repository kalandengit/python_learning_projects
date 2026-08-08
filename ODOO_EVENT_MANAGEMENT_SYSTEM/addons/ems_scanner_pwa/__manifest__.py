{
    "name": "EMS Scanner PWA",
    "version": "19.0.2.0.0",
    "category": "Marketing/Events",
    "summary": "Installable check-in scanner with offline queueing",
    "author": "EMS",
    "license": "LGPL-3",
    "depends": ["ems_api","website"],
    "data": ["views/scanner_templates.xml"],
    "assets": {
        "web.assets_frontend": [
            "ems_scanner_pwa/static/src/js/scanner.js",
            "ems_scanner_pwa/static/src/css/scanner.css"
        ]
    },
    "installable": True
}
