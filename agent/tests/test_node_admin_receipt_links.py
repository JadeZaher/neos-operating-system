"""Support receipt navigation retains explicit inspection and local-only targets."""
from neos_agent.api.chat import _record_reference
from neos_agent.db import models  # Register the support catalog models.


def test_support_receipt_uses_catalog_filtered_admin_record_link():
    record = "20000000-0000-4000-8000-000000000004"
    org = "20000000-0000-4000-8000-000000000003"
    link = f"/admin?resource=proposals&record={record}&organization_id={org}"
    assert _record_reference({"link": link, "title": "Support draft"}) == (link, "Support draft")
    for invalid in (
        "https://external.test" + link, "/" + link, link + "&redirect=https://external.test",
        link + "&record=" + record, link.replace("resource=proposals", "resource=node_admin_actions"),
        link.replace("record=" + record, "record=not-a-uuid"),
        link.replace("organization_id=" + org, "organization_id=not-a-uuid"), link + "#inspect",
    ):
        assert _record_reference({"link": invalid}) is None
