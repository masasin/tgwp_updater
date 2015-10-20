#!/usr/bin/env python
# (C) 2015  Jean Nassar
# Released under the GNU General Public License, version 3
"""
Updates /r/tgwp with Ryuugi's TGWP

Updates the /r/tgwp subreddit with the latest chapter from Ryuugi's The Games
We Play, from Spacebattles forums.

"""
from collections import namedtuple
import json
import logging
import sys
import time

from bs4 import BeautifulSoup
import praw
import requests


format_string = "%(name)-12s : %(levelname)-8s  %(message)s"
date_format = "%Y-%m-%d %H:%M:%S "

# Log everything to file
logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s " + format_string,
                    datefmt=date_format,
                    filename=".tgwp_updater.log",
                    filemode="a")

# Log important data to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(format_string))
logging.getLogger("").addHandler(console)

# Hide info logs from requests
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("tgwp_updater")

Chapter = namedtuple("Chapter", "title url")

TGWP_INDEX_URL = ("https://forums.spacebattles.com/threads/"
                  "rwby-the-gamer-the-games-we-play-disk-five.341621/")
SUBS = ["TGWP"]
ADMIN = "masasin"
UPLOADERS = ["masasin", "TGWP_Updater"]
TITLE_FORMAT = "{i} - {title}"

with open("settings.json", "r") as settings_file:
    SETTINGS = json.load(settings_file)


class Updater(object):
    """
    Class for the  updater methods.

    Parameters
    ----------
    url : str
        The URL of the main forum post.
    subs : list of str
        Names of the subreddits to submit to.
    formatter : str
        A template for generating consistent post titles.
    settings : dict
        A dict of settings for the updater. Necessary variables are:

        - user_agent
        - client_id
        - client_secret
        - redirect_uri
        - updater_access_token
        - updater_refresh_token
        - scopes

    """
    def __init__(self, url=TGWP_INDEX_URL, subs=SUBS,
                 formatter=TITLE_FORMAT, settings=SETTINGS):
        logger.debug("Initializing updater")
        self.url = url
        self.settings = settings
        self.subs = subs
        self.formatter = formatter
        self.session = self._login()
        self.links = self._get_story_links()

    def loop(self, interval=10):
        """
        Continuously loop through the script.

        Parameters
        ----------
        interval : int
            The time, in minutes, between checks.

        """
        while True:
            self.links = self._get_story_links()
            self.run()
            if interval:
                time.sleep(interval*60)

    def run(self):
        """Update the subreddit if a new post is available."""
        latest_post = self._get_latest_post()
        if latest_post is None:
            return

        chapter_number = int(latest_post.title.partition(" - ")[0])
        new_post_count = len(self.links) - chapter_number

        if new_post_count > 0:
            logger.info("A new chapter!")
            self._update_latest_link(new_post_count)
        else:
            logger.info("No new chapters...")

    def _get_story_links(self):
        """
        Get all chapter links.

        Returns
        -------
        links : list of Chapter
            A list of Chapter namedtuples containing all chapter names and their
            urls.

        Raises
        ------
        RuntimeError
            If the forum page cannot be downloaded properly.

        """
        logger.info("Getting story links")
        logger.debug("Downloading forum page")
        forum_page = requests.get(self.url)
        if forum_page.status_code != 200:
            raise RuntimeError("Cannot access the forum page.")

        post = BeautifulSoup(forum_page.text).html.article
        post_title = post.div.text.splitlines()[1]  # Title of article chapter
        logger.debug("Obtained post")

        logger.debug("Extracting links")
        links = []
        link = post.a
        while link.text != ("On those who live to see old age in a profession "
                             "where most die young."):
            links.append(Chapter(link.text, link.get("href")))

            # If the main post contains a story, and the story is not linked,
            # check to ensure no name collisions, and add self as a link.
            if link.next_sibling.next_sibling.strip():
                if post_title == link.text:
                    post_title += " (Cont.)"
                links.append(Chapter(post_title, TGWP_INDEX_URL))

            link = link.find_next("a")
        logging.debug("Links extracted")
        return links

    def _login(self):
        """
        Login to Reddit using OAUTH2.

        Returns
        -------
        session : praw.Reddit
            A Reddit session

        """
        logger.info("Logging into reddit")
        session = praw.Reddit(user_agent=self.settings["user_agent"])
        session.set_oauth_app_info(self.settings["client_id"],
                                   self.settings["client_secret"],
                                   self.settings["redirect_uri"])
        session.set_access_credentials(self.settings["scopes"],
                                       self.settings["updater_access_token"],
                                       self.settings["updater_refresh_token"])

        return session

    def _get_latest_post(self):
        """
        Get the latest TGWP submission from /r/tgwp.

        If no submission can be found, message `ADMIN` for manual intervention.

        Returns
        -------
        post : praw.objects.Submission

        """
        logger.info("Getting latest reddit post")
        for post in self.session.get_subreddit("tgwp").get_new():
            if post.author.name in UPLOADERS:
                logger.debug("Post found")
                return post
            else:
                continue
        else:
            logger.critical("Latest post was not found! Aborting!")
            self.session.send_message(ADMIN,
                                      "TGWP_Updater problem",
                                      "Cannot get latest post")

    def _submit_post(self, subreddit, title, url):
        """
        Submit a link to a subreddit.

        If another user is submitting, message `ADMIN`.

        Parameters
        ----------
        subreddit : str
            The subreddit to submit to.
        title : str
            The title of the post.
        url : str
            The URL of the link.

        """
        post = self.session.submit(subreddit, title, url=url, resubmit=True)
        if self.session.user.name != ADMIN:
            message = "New post available! {title} at {url}".format(
                title=title, url=post.short_link)
            self.session.send_message(ADMIN, "TGWP Updated", message)

    def _update_latest_link(self, count):
        """
        Submit all links that have not yet been submitted.

        Parameters
        ----------
        count : int
            The number of links to submit.

        """
        if count > 1:
            logger.info("Submitting {n} latest links".format(n=count))
        else:
            logger.info("Submitting latest link")

        new_chapters = self.links[-count:]
        for sub in self.subs:
            for i, link in zip(reversed(range(count)), new_chapters):
                logger.debug("Submitting {title} to {sub}"
                             .format(title=link.title, sub=sub))
                new_title = self.formatter.format(i=len(self.links) - i,
                                                  title=link.title)

                try:
                    self._submit_post(sub, new_title, link.url)

                except praw.errors.RateLimitExceeded:
                    logger.warning("Rate limit exceeded!")
                    logger.debug("Waiting ten minutes to resubmit.")
                    time.sleep(10*60)
                    url = self._get_latest_post().url

                    if url == link.url:
                        logger.debug("Already submitted.")
                    else:
                        logger.debug("Submitting now.")
                        self._submit_post(sub, new_title, link.url)


def main():
    """Main entry point for script."""
    updater = Updater()
    updater.run()


if __name__ == "__main__":
    sys.exit(main())
