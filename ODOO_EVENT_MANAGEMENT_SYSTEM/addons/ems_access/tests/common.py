from odoo.tests.common import TransactionCase


class EmsAccessCommon(TransactionCase):
    """Shared fixtures.

    Tests deliberately act as real, non-superuser users: record rules and ACLs
    are bypassed for the superuser, so asserting them as ``self.env.user``
    would prove nothing.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.ems_user = cls.env["res.users"].create({
            "name": "EMS Gate Operator",
            "login": "ems.gate.operator@example.com",
            "company_id": cls.company.id,
            "company_ids": [(6, 0, [cls.company.id])],
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("ems_core.group_ems_user").id,
            ])],
        })
        cls.ems_manager = cls.env["res.users"].create({
            "name": "EMS Administrator",
            "login": "ems.administrator@example.com",
            "company_id": cls.company.id,
            "company_ids": [(6, 0, [cls.company.id])],
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("ems_core.group_ems_manager").id,
            ])],
        })

        cls.event = cls.env["event.event"].create({
            "name": "Scan Test Event",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
            "ems_checkin_open": True,
            "ems_organizer_id": cls.ems_manager.id,
        })
        cls.attendee = cls.env["res.partner"].create({"name": "Attendee One"})
        cls.ticket = cls.env["ems.ticket"].create({
            "event_id": cls.event.id,
            "partner_id": cls.attendee.id,
        })
        cls.device = cls.env["ems.scanner.device"].create({
            "name": "Main Gate",
            "device_uid": "gate-1",
            "event_ids": [(6, 0, [cls.event.id])],
        })
        cls.other_device = cls.env["ems.scanner.device"].create({
            "name": "Side Gate",
            "device_uid": "gate-2",
            "event_ids": [(6, 0, [cls.event.id])],
        })

    def scan(self, envelope, device_uid, client_scan_uid, user=None):
        env = self.env(user=user or self.ems_user)
        return env["ems.scan.log"].validate_envelope(envelope, device_uid, client_scan_uid)
