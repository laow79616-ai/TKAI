from marketplace.installer import ReferenceInstallerService
from tests.marketplace.installer.test_core import request


def test_transaction_events_statistics_and_rollback():
    service = ReferenceInstallerService()
    result = service.install(request())
    snapshot = service.snapshot()
    assert (
        snapshot.transactions[0].state.value == "committed"
        and snapshot.statistics.succeeded == 1
    )
    assert [event.sequence for event in snapshot.events] == list(
        range(1, len(snapshot.events) + 1)
    )
    assert service.rollback(result.session.installation_id).state.value == "completed"
    assert not service.snapshot().installed_records
