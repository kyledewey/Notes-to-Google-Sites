#!/usr/bin/env python

import gdata.sites.client
import gdata.sites.data
import gdata.gauth
import datetime
import sys
import config_reader
import os.path

def parse_notes(lines):
    from notes_parser import Notes2HTML
    return Notes2HTML().convert_contents(lines)

def parse_markdown(lines):
    import markdown
    return markdown.markdown("\n".join(lines))

def parse_html(lines):
    return "\n".join(lines)

# maps file extensions to functions that can parse content of that type
file_extension_parsers = {".htm": parse_html,
                          ".html": parse_html,
                          ".notes": parse_notes,
                          ".md": parse_markdown}

class SitesCommunicator(object):
    def __init__(self):
        self.feed = None
        self.config = config = config_reader.SyncConfig()
        self.APPLICATION_NAME = config['APPLICATION_NAME']
        self.EMAIL = config['EMAIL']
        self.PASSWORD = config['PASSWORD']
        self.SITE = config['SITE']
        self.TOKEN_FILE = os.path.expanduser(config['TOKEN_FILE'])
        self.MEETING_MINUTES = config['MEETING_MINUTES']
        self.client = gdata.sites.client.SitesClient(
            source=self.APPLICATION_NAME,
            site=self.SITE)
        self.client.ssl = True
        self.auth_client()

    def write_token(self, token):
        fh = open(self.TOKEN_FILE, "w")
        fh.write(token.token_string)
        fh.close()

    # to be called when a captcha is encountered
    # handles token-related things
    def handle_captcha_challenge(self, challenge):
        print 'Please visit ' + challenge.captcha_url
        answer = raw_input('Answer to the challenge? ')
        token = self.client.ClientLogin(
            self.EMAIL, self.PASSWORD,
            self.APPLICATION_NAME,
            captcha_token=challenge.captcha_token,
            captcha_response=answer)
        self.write_token(token)
        self.feed = self.client.GetSiteFeed()

    # attempts to authenticate a client with a saved token
    # returns true if authentication was ok
    def auth_client_with_token(self):
        try:
            fh = open(self.TOKEN_FILE, "r")
            token = fh.read()
            fh.close()
            self.client.auth_token = gdata.gauth.ClientLoginToken(token)
            self.feed = self.client.GetSiteFeed()
            return True
        except gdata.client.CaptchaChallenge as challenge:
            self.handle_captcha_challenge(challenge)
        except:
            return False

    def auth_client(self):
        if not self.auth_client_with_token():
            try:
                self.client.ClientLogin(
                    self.EMAIL, self.PASSWORD,
                    self.APPLICATION_NAME)
                self.write_token(self.client.auth_token)
                self.feed = self.client.GetSiteFeed()
            except gdata.client.CaptchaChallenge as challenge:
                self.handle_captcha_challenge(challenge)

    # gets the name of the meeting minute for this date
    def meeting_minute_name(self):
        return "Minutes for {0}".format(
            datetime.datetime.now().strftime("%b %d, %Y"))

    # gets the url that will be generated for today's meeting minute name
    # note that it only returns the last part of the URL
    def meeting_minute_url( self ):
        return "minutes-for-{0}".format(
            datetime.datetime.now().strftime( "%b-%d-%Y" ).lower())

    # Amazingly, this is non-trivial to do.  The API claims there is a way to
    # directly pass a URL, but I gave up on this after trying around 200 combinations
    # of what it could possibly be.
    #
    # Note that the URL is relative to the base site.  I.e. to get:
    # https://sites.google.com/site/mysite/mydirectory/meeting-minutes,
    # specify: "/mydirectory/meeting-minutes
    def content_entry_for_url(self, relative):
        absolute = "{0}?path={1}".format(
            self.client.MakeContentFeedUri(), relative)
        return self.client.GetContentFeed(uri=absolute).entry

    # takes the HTML content
    # assumes that the page doesn't already exist
    def make_meeting_minute_blindly(self, content):
        parent = self.content_entry_for_url(self.MEETING_MINUTES)[0]
        self.client.CreatePage(
            'webpage',
            self.meeting_minute_name(),
            html=content,
            parent=parent)

    # returns the meeting minute page for today, or None if one doesn't
    # already exist
    def get_meeting_minute_page(self):
        content = self.content_entry_for_url("{0}/{1}".format(
                self.MEETING_MINUTES,
                self.meeting_minute_url()))
        return content[0] if content else None

    def yes_no_none(self, response):
        response = response.lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            return None

    def yes_no_prompt(self, text_prompt):
        while True:
            response = self.yes_no_none(
                raw_input("{0} (yes/no)?: ".format(text_prompt)))
            if response is not None:
                return response
            else:
                print "Please answer yes or no"

    def overwrite_existing_page(self, page, content):
        self.client.Delete(page)
        self.make_meeting_minute_blindly(content)
        # According to the docs, the following two lines should work
        # However, it will completely strip out the HTML tags
        #page.content.html = content
        #self.client.Update( page )

    def make_meeting_minute(self, content):
        existing = self.get_meeting_minute_page()
        if (existing and 
            self.yes_no_prompt("Overwrite existing minutes")):
            self.overwrite_existing_page(existing, content)
        elif not existing:
            self.make_meeting_minute_blindly(content)


# given a filename, returns the raw file data
# in a single string
def read_raw_file(filename):
    fh = open(filename, "r")
    content = fh.read()
    fh.close()
    return content

def file_extension(filename):
    _, extension = os.path.splitext(filename)
    return extension

# reads in the given file, making sure it's in HTML format
# assumes that html files end in .html
def read_formatted(filename):
    extension = file_extension(filename)
    if extension in file_extension_parsers:
        contents = read_raw_file(filename).split("\n")
        return file_extension_parsers[extension](contents)
    else:
        raise Exception(
            "Unknown file extension: {0}".format(extension))

# BEGIN MAIN
if __name__ == "__main__":
    if len(sys.argv) == 2:
        content = read_formatted(sys.argv[1])
        sc = SitesCommunicator()
        sc.make_meeting_minute(content)
    else:
        print "Needs the name of a notes file to upload. Files ending in HTML" + \
            " are uploaded as-is, while files ending in either .txt or .notes" + \
            " will first be converted to HTML."
        



