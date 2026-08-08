{
    "name": "EMS Access Control",
    "version": "19.0.2.0.0",
    "category": "Marketing/Events",
    "summary": "Scanner device enrollment, check-in validation and offline sync",
    "author": "EMS",
    "license": "LGPL-3",
    "depends": ["ems_ticketing", "ems_badge"],
    "data": [
        "security/ir.model.access.csv",
        "security/ems_access_security.xml",
        "views/access_views.xml"
    ],
    "installable": True
}
