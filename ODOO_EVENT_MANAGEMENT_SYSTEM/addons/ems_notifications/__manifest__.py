{
    "name": "EMS Notifications",
    "version": "19.0.2.0.0",
    "category": "Marketing/Events",
    "summary": "Queued attendee notifications with retry, backoff and templates",
    "author": "EMS",
    "license": "LGPL-3",
    "depends": ["ems_core", "ems_ticketing", "ems_waitlist", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "data/cron.xml",
        "views/notification_views.xml"
    ],
    "installable": True
}
