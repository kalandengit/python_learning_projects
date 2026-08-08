# Dependency Verification — Odoo 19 Community

Every claim below was checked against an actual Odoo checkout, not against
documentation or recollection.

**Reference checkout**

| Item | Value |
| --- | --- |
| Repository | `https://github.com/odoo/odoo.git` |
| Branch | `19.0` |
| Commit | `4d7ef1f513155010f709884325b154b862b8c59d` |
| `odoo/release.py` | `version_info = (19, 0, 0, FINAL, 0, '')` |
| Community addons present | 631 |
| Enterprise addons used | none |

## Module dependency closure

`ems_suite` resolves to a closure of **42 modules**, all of them Community.
No Enterprise-only module appears anywhere in the graph.

The only external Python dependency declared by any module in the closure is
`geoip2` (declared by `website`). EMS itself declares no external dependency;
it uses `qrcode`, which ships in Odoo's own `requirements.txt`.

## External IDs referenced by EMS

| External ID | Verified in | Status |
| --- | --- | --- |
| `event.view_event_form` | `addons/event/views/event_event_views.xml:10` | exists |
| `event.group_event_user` | `addons/event/security/event_security.xml:17` | exists |
| `event.group_event_manager` | `addons/event/security/event_security.xml:24` | exists |
| `event.model_event_event` | generated from `event.event` | exists |
| `base.module_category_marketing` | `odoo/addons/base/data/ir_module_category_data.xml:48` | exists |
| `base.group_portal`, `base.group_user` | `odoo/addons/base` | exists |
| `payment.payment_provider_transfer` | `addons/payment/data/payment_provider_data.xml:500` | exists |
| `payment.payment_method_unknown` | `addons/payment/data/payment_method_data.xml:3623` | exists |
| `portal.portal_layout`, `portal.portal_my_home`, `portal.portal_docs_entry`, `portal.portal_table`, `portal.portal_breadcrumbs` | `addons/portal/views/portal_templates.xml` | exists |
| `web.basic_layout`, `website.layout` | `addons/web`, `addons/website` | exists |

## API surface

| Assumption | Verified against | Result |
| --- | --- | --- |
| `type='jsonrpc'` is the Odoo 19 spelling | `odoo/http.py:815-819` | Correct. `type='json'` is a deprecated alias that emits a `DeprecationWarning`. |
| `auth='bearer'` exists | `odoo/http.py:777`, `odoo/addons/base/models/ir_http.py:235` | Exists — **with an important restriction**, see below. |
| `payment.transaction._set_done` signature | `addons/payment/models/payment_transaction.py:949` | `_set_done(self, *, state_message=None, extra_allowed_states=())` — the shipped override matched. |
| `payment.transaction._set_canceled` signature | `addons/payment/models/payment_transaction.py:967` | `_set_canceled(self, state_message=None, extra_allowed_states=())` — the shipped override **did not** match (see GAP-04). |
| `check_access(operation)` | `odoo/orm/models.py:4100` | Correct for 19. |
| `models.Constraint` | `odoo/orm/table_objects.py:79`, re-exported by `odoo/models/__init__.py:25` | Correct; `_sql_constraints` is the superseded form. |
| `<chatter/>` in form views | `addons/event/views/event_event_views.xml:163` | Correct for 19. |
| `ir.cron` with `state='code'` | `odoo/addons/base/models/ir_actions.py` | Correct. |
| `post_init_hook(env)` signature | `addons/delivery/__init__.py:10` and peers | Correct for 19. |
| `mail.template._render_field(field, res_ids, engine=…)` | `addons/mail/models/mail_render_mixin.py:775` | Correct; `body_html` needs `engine='qweb'`. |
| `/web/health` | `addons/web/controllers/home.py:173` | Exists; used for the container healthcheck. |

## Odoo 19 renames that the shipped package had not adopted

These are structural 19.0 changes. Each one broke the package at install or
runtime and is fixed in this repository.

| Odoo ≤18 | Odoo 19 | Verified in |
| --- | --- | --- |
| `res.groups.category_id` (→ `ir.module.category`) | `res.groups.privilege_id` (→ new model `res.groups.privilege`, which itself carries `category_id`) | `odoo/addons/base/models/res_groups.py:37`, `res_groups_privilege.py` |
| `res.users.groups_id` | `res.users.group_ids` | `odoo/addons/base/models/res_users.py:257` |
| `res.partner.mobile` | **removed**; `phone` is the only phone field | absent from `odoo/addons/base/models/res_partner.py` and from every addon |
| `ir.ui.view.groups_id` | `ir.ui.view.group_ids` | `odoo/addons/base/models/ir_ui_view.py:175` |
| group restriction allowed on an inherited view record | **rejected**; must be a `groups=` attribute on the injected node | enforced by `odoo/tools/convert.py` |

Fields that did **not** change, contrary to what a blanket rename would assume:
`ir.rule.groups` is still `groups` (`odoo/addons/base/models/ir_rule.py:25`).

## `auth='bearer'` restriction (affects the scanner PWA)

`ir_http._auth_method_bearer` accepts a request in exactly two ways:

1. an `Authorization: Bearer <api-key>` header; or
2. an existing session **only if** the request also carries
   `Sec-Fetch-Dest: document`, `Sec-Fetch-Mode: navigate`,
   `Sec-Fetch-Site: none|same-origin` and `Sec-Fetch-User: ?1`
   (`odoo/addons/base/models/ir_http.py:228-232`).

Those Sec-headers describe a **top-level document navigation**. A `fetch()`
call from a page sends `Sec-Fetch-Dest: empty` and no `Sec-Fetch-User`, so a
browser-based PWA calling a bearer route with only its session cookie is
rejected with `401 Unauthorized`. This is verified by the regression test
`ems_api/tests/test_api.py::test_bearer_route_rejects_a_plain_session_fetch`.

Consequence for this codebase: the bearer routes under `/ems/api/v1/*` are for
API-key clients, and the PWA uses the `auth='user'` routes under
`/ems/scanner/api/*`. Both families share one authorization implementation.

## Runtime environment used for verification

Python 3.11.15, PostgreSQL 16.13. Odoo 19's `requirements.txt` pins versions
matched to Debian 12 / Ubuntu 24.04 packages; several of those pins have no
wheels for this combination, so verification used unpinned current releases of
the same libraries. This affects the verification host only — it is not a
statement about what the production image should pin.
