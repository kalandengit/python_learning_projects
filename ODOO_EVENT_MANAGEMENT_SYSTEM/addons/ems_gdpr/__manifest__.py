{
    "name": "EMS GDPR",
    "version": "19.0.2.0.0",
    "category": "Marketing/Events",
    "summary": "Subject access export, anonymization, retention policy and legal hold",
    "author": "EMS",
    "license": "LGPL-3",
    "depends": ["ems_ticketing", "ems_access", "ems_badge", "ems_waitlist"],
    "data": [
        "security/ir.model.access.csv",
        "data/cron.xml",
        "views/gdpr_views.xml",
        "views/res_partner_views.xml"
    ],
    "installable": True
}
