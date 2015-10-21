from unittest import mock

import praw
import pytest

from tgwp_updater import (TGWP_INDEX_URL, SUBS, TITLE_FORMAT, SETTINGS,
                          TgwpError, Updater)


def test_settings_file():
    assert "user_agent" in SETTINGS
    assert "client_id" in SETTINGS
    assert "client_secret" in SETTINGS
    assert "redirect_uri" in SETTINGS
    assert "updater_access_token" in SETTINGS
    assert "updater_refresh_token" in SETTINGS
    assert "scopes" in SETTINGS


class TestStartup(object):
    @mock.patch.object(Updater, "_get_story_links", autospec=True)
    @mock.patch.object(Updater, "_login", autospec=True)
    def test_initialization(self, mock_login, mock_get_story_links):
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
    def test_login(self, mock_set_oauth, mock_set_creds, mock_get_links):
        updater = Updater()
        assert updater.session.http.headers["User-Agent"].startswith(
            SETTINGS["user_agent"])
        mock_set_oauth.assert_called_once_with(updater.session,
                                               SETTINGS["client_id"],
                                               SETTINGS["client_secret"],
                                               SETTINGS["redirect_uri"])
        mock_set_creds.assert_called_once_with(
            updater.session,
            SETTINGS["scopes"],
            SETTINGS["updater_access_token"],
            SETTINGS["updater_refresh_token"]
        )

    @mock.patch.object(Updater, "_login", autospec=True)
    @mock.patch("tgwp_updater.requests", autospec=True)
    def test_getting_bad_link(self, mock_requests, mock_login):
        mock_requests.get.return_value.status_code = 404
        with pytest.raises(TgwpError):
            Updater()
