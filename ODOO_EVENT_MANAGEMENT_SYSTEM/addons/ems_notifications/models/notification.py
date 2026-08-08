import logging
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
MAX_BACKOFF_MINUTES = 60
BATCH_SIZE = 100


class EmsNotification(models.Model):
    _name = "ems.notification"
    _description = "EMS Notification"
    _order = "create_date"

    channel = fields.Selection([("email", "Email"), ("sms", "SMS"), ("push", "Push")],
                               required=True, default="email")
    recipient = fields.Char(required=True)
    subject = fields.Char()
    body = fields.Text(required=True)
    state = fields.Selection([("pending", "Pending"), ("sent", "Sent"), ("failed", "Failed")],
                             required=True, default="pending", index=True)
    attempt_count = fields.Integer(default=0, readonly=True)
    next_attempt_at = fields.Datetime(index=True, readonly=True)
    last_error = fields.Text(readonly=True)
    sent_at = fields.Datetime(readonly=True)
    res_model = fields.Char(index=True)
    res_id = fields.Integer(index=True)

    # ------------------------------------------------------------------
    # Enqueueing
    # ------------------------------------------------------------------
    @api.model
    def ems_enqueue(self, channel, recipient, body, subject=None, record=None):
        """Queue one notification. Delivery happens in the cron, never inline."""
        vals = {
            "channel": channel,
            "recipient": recipient,
            "subject": subject,
            "body": body,
        }
        if record is not None and record:
            vals.update({"res_model": record._name, "res_id": record.id})
        return self.create(vals)

    @api.model
    def ems_enqueue_template(self, template_xmlid, record, recipient=None):
        """Render an Odoo mail.template and queue the result as an email."""
        template = self.env.ref(template_xmlid)
        # body_html is a QWeb template; subject is an inline template.
        rendered = template._render_field(
            "body_html", record.ids, engine="qweb", compute_lang=True
        )[record.id]
        subject = template._render_field("subject", record.ids, compute_lang=True)[record.id]
        target = recipient or record.partner_id.email
        if not target:
            _logger.info("Skipping %s for %s: no email address", template_xmlid, record)
            return self.browse()
        return self.ems_enqueue("email", target, rendered, subject=subject, record=record)

    # ------------------------------------------------------------------
    # Providers
    # ------------------------------------------------------------------
    def _provider_is_configured(self, channel):
        params = self.env["ir.config_parameter"].sudo()
        if channel == "email":
            return True  # Odoo's own outgoing mail server handles email.
        return bool(params.get_param(f"ems.notifications.{channel}_endpoint"))

    def _send_one(self):
        """Dispatch one notification through its channel provider."""
        self.ensure_one()
        if self.channel == "email":
            self.env["mail.mail"].sudo().create({
                "subject": self.subject or "",
                "body_html": self.body,
                "email_to": self.recipient,
                "auto_delete": True,
            }).send(raise_exception=True)
            return True
        # SMS/push providers are deployment-specific. Nothing is sent until an
        # endpoint is configured, and unconfigured channels fail fast instead of
        # burning the retry budget.
        raise UserWarning(
            f"No provider configured for the '{self.channel}' channel "
            f"(set ems.notifications.{self.channel}_endpoint)."
        )

    # ------------------------------------------------------------------
    # Automation
    # ------------------------------------------------------------------
    @api.model
    def _cron_process(self):
        now = fields.Datetime.now()
        items = self.search([
            ("state", "=", "pending"),
            "|", ("next_attempt_at", "=", False), ("next_attempt_at", "<=", now),
        ], limit=BATCH_SIZE)

        sent = failed = 0
        for rec in items:
            if not rec._provider_is_configured(rec.channel):
                rec.write({
                    "state": "failed",
                    "last_error": f"No provider configured for channel '{rec.channel}'.",
                })
                failed += 1
                continue
            try:
                # Each delivery gets its own savepoint: one bad recipient must
                # not roll back the notifications already sent in this batch.
                with self.env.cr.savepoint():
                    rec._send_one()
                rec.write({"state": "sent", "last_error": False, "sent_at": fields.Datetime.now()})
                sent += 1
            except Exception as exc:  # noqa: BLE001 - provider errors are arbitrary
                attempts = rec.attempt_count + 1
                give_up = attempts >= MAX_ATTEMPTS
                rec.write({
                    "attempt_count": attempts,
                    "state": "failed" if give_up else "pending",
                    "next_attempt_at": now + timedelta(
                        minutes=min(MAX_BACKOFF_MINUTES, 2 ** attempts)
                    ),
                    "last_error": str(exc)[:1000],
                })
                failed += give_up
        if sent or failed:
            _logger.info("EMS notifications: %s sent, %s permanently failed", sent, failed)
        return sent

    def action_retry(self):
        """Put a permanently failed notification back in the queue."""
        self.filtered(lambda n: n.state == "failed").write({
            "state": "pending", "attempt_count": 0, "next_attempt_at": False,
        })
        return True
