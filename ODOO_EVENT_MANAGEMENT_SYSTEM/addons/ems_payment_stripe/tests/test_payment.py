from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "ems_payment_stripe")
class TestPaymentLinkage(TransactionCase):
    """EMS never talks to Stripe directly.

    Odoo's payment module owns the provider transaction lifecycle; EMS only
    reacts to the state transitions it publishes, which is what these tests
    exercise. No card data is stored or asserted on anywhere.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env.ref("payment.payment_provider_transfer")
        cls.payment_method = cls.env.ref("payment.payment_method_unknown")
        cls.event = cls.env["event.event"].create({
            "name": "Paid Event",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
            # Explicitly off: paid events issue tickets on payment, not on
            # registration, and this test proves the payment path does it.
            "ems_auto_issue_tickets": False,
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Paying Attendee", "email": "payer@example.com",
        })
        cls.registration = cls.env["event.registration"].create({
            "event_id": cls.event.id, "partner_id": cls.partner.id,
        })

    def _transaction(self, reference):
        return self.env["payment.transaction"].create({
            "provider_id": self.provider.id,
            "payment_method_id": self.payment_method.id,
            "reference": reference,
            "amount": 50.0,
            "currency_id": self.env.company.currency_id.id,
            "partner_id": self.partner.id,
        })

    def _link(self, transaction):
        return self.env["ems.payment.link"].create({
            "event_id": self.event.id,
            "registration_id": self.registration.id,
            "transaction_id": transaction.id,
            "amount": 50.0,
            "currency_id": self.env.company.currency_id.id,
            "partner_id": self.partner.id,
        })

    def test_no_ticket_before_payment(self):
        self._link(self._transaction("EMS-TEST-PENDING"))
        self.assertEqual(self.registration.ems_ticket_count, 0)

    def test_done_transaction_marks_link_paid_and_issues_ticket(self):
        transaction = self._transaction("EMS-TEST-DONE")
        link = self._link(transaction)
        transaction._set_done()
        self.assertEqual(transaction.state, "done")
        self.assertEqual(link.state, "paid")
        self.assertEqual(self.registration.ems_ticket_count, 1)
        self.assertEqual(self.registration.ems_ticket_ids.state, "active")

    def test_reconciliation_is_idempotent(self):
        transaction = self._transaction("EMS-TEST-IDEMPOTENT")
        link = self._link(transaction)
        transaction._set_done()
        transaction._ems_reconcile_event_payment()
        transaction._ems_reconcile_event_payment()
        self.assertEqual(link.state, "paid")
        self.assertEqual(self.registration.ems_ticket_count, 1)

    def test_cancelled_transaction_cancels_link(self):
        transaction = self._transaction("EMS-TEST-CANCEL")
        link = self._link(transaction)
        transaction._set_canceled()
        self.assertEqual(link.state, "cancelled")
        self.assertEqual(self.registration.ems_ticket_count, 0)

    def test_set_canceled_accepts_extra_allowed_states(self):
        """The override must keep Odoo 19's full keyword signature."""
        transaction = self._transaction("EMS-TEST-SIGNATURE")
        self._link(transaction)
        transaction._set_done()
        transaction._set_canceled(extra_allowed_states=("done",))
        self.assertEqual(transaction.state, "cancel")

    def test_unlinked_transaction_is_ignored(self):
        transaction = self._transaction("EMS-TEST-UNLINKED")
        transaction._set_done()
        self.assertEqual(
            self.env["ems.payment.link"].search_count([("transaction_id", "=", transaction.id)]),
            0,
        )
        self.assertEqual(self.registration.ems_ticket_count, 0)
