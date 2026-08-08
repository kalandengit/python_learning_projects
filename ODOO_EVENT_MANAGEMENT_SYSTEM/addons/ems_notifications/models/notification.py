from datetime import timedelta
from odoo import api, fields, models


class EmsNotification(models.Model):
    _name = "ems.notification"
    _description = "EMS Notification"
    _order = "create_date"

    channel = fields.Selection([("email","Email"),("sms","SMS"),("push","Push")],
                               required=True, default="email")
    recipient = fields.Char(required=True)
    subject = fields.Char()
    body = fields.Text(required=True)
    state = fields.Selection([("pending","Pending"),("sent","Sent"),("failed","Failed")],
                             required=True, default="pending", index=True)
    attempt_count = fields.Integer(default=0)
    next_attempt_at = fields.Datetime(index=True)
    last_error = fields.Text(readonly=True)

    def _send_one(self):
        self.ensure_one()
        if self.channel == "email":
            self.env["mail.mail"].create({
                "subject": self.subject or "",
                "body_html": self.body,
                "email_to": self.recipient,
            }).send()
            return
        raise NotImplementedError(f"Provider adapter not configured for {self.channel}")

    @api.model
    def _cron_process(self):
        now = fields.Datetime.now()
        items = self.search([
            ("state","=","pending"),
            "|",("next_attempt_at","=",False),("next_attempt_at","<=",now)
        ], limit=100)
        for rec in items:
            try:
                rec._send_one()
                rec.write({"state":"sent","last_error":False})
            except Exception as exc:
                attempts = rec.attempt_count + 1
                rec.write({
                    "attempt_count": attempts,
                    "state": "failed" if attempts >= 5 else "pending",
                    "next_attempt_at": now + timedelta(minutes=min(60, 2 ** attempts)),
                    "last_error": str(exc)[:1000],
                })
