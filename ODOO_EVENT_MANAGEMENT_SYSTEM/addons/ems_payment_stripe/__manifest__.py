{
    "name": "EMS Stripe Integration",
    "version": "19.0.2.0.0",
    "category": "Marketing/Events",
    "summary": "Links Odoo payment transactions to EMS event objects",
    "author": "EMS",
    "license": "LGPL-3",
    "depends": ["ems_ticketing","payment","payment_stripe"],
    "data": ["security/ir.model.access.csv","views/payment_link_views.xml"],
    "installable": True
}
