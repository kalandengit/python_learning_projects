{
    "name": "EMS Ticketing",
    "version": "19.0.2.0.0",
    "category": "Marketing/Events",
    "summary": "Secure, auditable event tickets with signed QR access credentials",
    "author": "EMS",
    "license": "LGPL-3",
    "depends": ["ems_core"],
    "data": [
        "security/ir.model.access.csv",
        "security/ems_ticketing_security.xml",
        "data/sequence.xml",
        "views/ticket_views.xml"
    ],
    "post_init_hook": "post_init_hook",
    "installable": True
}
