{
    "name": "EMS Badges",
    "version": "19.0.2.0.0",
    "category": "Marketing/Events",
    "summary": "Attendee badges with zone authorization and printable QR badges",
    "author": "EMS",
    "license": "LGPL-3",
    "depends": ["ems_ticketing"],
    "data": [
        "security/ir.model.access.csv",
        "security/ems_badge_security.xml",
        "report/badge_report.xml",
        "views/badge_views.xml"
    ],
    "installable": True
}
