from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _ems_reconcile_event_payment(self):
        links = self.env["ems.payment.link"].search([("transaction_id","in",self.ids)])
        for link in links:
            tx = link.transaction_id
            if tx.state == "done" and link.state != "paid":
                link.state = "paid"
                if link.registration_id:
                    link.registration_id.ems_issue_ticket()
            elif tx.state in ("cancel","error") and link.state == "pending":
                link.state = "cancelled"
        return True

    def _set_done(self, *, state_message=None, extra_allowed_states=()):
        result = super()._set_done(state_message=state_message,
                                   extra_allowed_states=extra_allowed_states)
        self._ems_reconcile_event_payment()
        return result

    def _set_canceled(self, state_message=None):
        result = super()._set_canceled(state_message=state_message)
        self._ems_reconcile_event_payment()
        return result
