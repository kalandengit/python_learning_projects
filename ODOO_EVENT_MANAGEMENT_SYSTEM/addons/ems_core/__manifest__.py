{
    "name": "EMS Core",
    "version": "19.0.2.0.0",
    "summary": "Core EMS objects: event extensions, venue zones, groups",
    "author": "EMS",
    "category": "Marketing/Events",
    "license": "LGPL-3",
    "depends": ["event", "mail", "contacts"],
    "data": [
        "security/ems_security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/event_event_views.xml",
        "views/venue_zone_views.xml",
        "views/menus.xml"
    ],
    "application": True,
    "installable": True
}
