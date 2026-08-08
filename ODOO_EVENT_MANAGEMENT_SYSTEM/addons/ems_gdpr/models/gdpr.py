import json
from odoo import fields, models
from odoo.exceptions import UserError


class EmsGdprRequest(models.Model):
    _name = "ems.gdpr.request"
    _description = "EMS GDPR Request"
    _inherit = ["mail.thread"]

    partner_id = fields.Many2one("res.partner", required=True, index=True)
    request_type = fields.Selection([("export","Export"),("anonymize","Anonymize")],
                                    required=True, default="export")
    state = fields.Selection([("draft","Draft"),("done","Done"),("rejected","Rejected")],
                             default="draft", required=True, tracking=True)
    result_json = fields.Text(readonly=True)

    def action_export(self):
        self.ensure_one()
        partner = self.partner_id
        tickets = self.env["ems.ticket"].search([("partner_id","=",partner.id)])
        data = {
            "partner": {"id":partner.id,"name":partner.name,"email":partner.email,"phone":partner.phone},
            "tickets": [{
                "name": t.name, "event": t.event_id.name, "state": t.state,
                "created": fields.Datetime.to_string(t.create_date)
            } for t in tickets],
        }
        self.write({"state":"done","result_json":json.dumps(data, ensure_ascii=False, indent=2)})

    def action_anonymize(self):
        self.ensure_one()
        partner = self.partner_id
        if partner.is_company:
            raise UserError("Company contacts require manual review.")
        # Keep referential integrity while scrubbing direct PII.
        partner.write({
            "name": f"Anonymized Partner {partner.id}",
            "email": False, "phone": False, "mobile": False,
            "street": False, "street2": False, "zip": False, "city": False,
        })
        self.write({"state":"done","result_json":"{\"status\":\"anonymized\"}"})
