from unittest import mock

import praw

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


@mock.patch.object(Updater, "_get_story_links", autospec=True)
@mock.patch.object(praw.Reddit, "set_access_credentials", autospec=True)
@mock.patch.object(praw.Reddit, "set_oauth_app_info", autospec=True)
def test_login(mock_set_oauth, mock_set_creds, mock_get_links):
    updater = Updater()
    mock_set_oauth.assert_called_once_with(updater.session,
                                           SETTINGS["client_id"],
                                           SETTINGS["client_secret"],
                                           SETTINGS["redirect_uri"])
    mock_set_creds.assert_called_once_with(updater.session,
                                           SETTINGS["scopes"],
                                           SETTINGS["updater_access_token"],
                                           SETTINGS["updater_refresh_token"])
