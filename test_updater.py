from unittest import mock

from tgwp_updater import (TGWP_INDEX_URL, SUBS, TITLE_FORMAT, SETTINGS, Updater)


def test_settings_file():
    assert "user_agent" in SETTINGS
    assert "client_id" in SETTINGS
    assert "client_secret" in SETTINGS
    assert "redirect_uri" in SETTINGS
    assert "updater_access_token" in SETTINGS
    assert "updater_refresh_token" in SETTINGS
    assert "scopes" in SETTINGS


@mock.patch.object(Updater, "_get_story_links", autospec=True)
@mock.patch.object(Updater, "_login", autospec=True)
def test_initialization(mock_login, mock_get_story_links):
    updater = Updater()
    assert updater.url == TGWP_INDEX_URL
    assert updater.settings == SETTINGS
    assert updater.subs == SUBS
    assert updater.formatter == TITLE_FORMAT
    mock_login.assert_called_once_with(updater)
    mock_get_story_links.assert_called_once_with(updater)
