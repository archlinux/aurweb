from aurweb import aur_logging

logger = aur_logging.get_logger(__name__)


def test_logging(caplog):
    logger.info("Test log.")

    # Test that we logged once.
    assert len(caplog.records) == 1

    # Test that our log record was of INFO level.
    assert caplog.records[0].levelname == "INFO"

    # Test that our message got logged.
    assert "Test log." in caplog.text
