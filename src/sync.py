#!/usr/bin/env python

import gdata.sites.client
import gdata.sites.data
import gdata.gauth
import datetime
import sys
import notes_parser
import config_reader
import os.path
import markdown

# maps file extensions to functions that can parse content of that type
file_extension_parsers = \
    { ".htm": lambda id: "\n".join( id ),
      ".html": lambda id: "\n".join( id ),
      ".notes": lambda n: notes_parser.Notes2HTML().convertContents( n ),
      ".md": lambda m: markdown.markdown( "\n".join( m ) ) }

class SitesCommunicator( object ):
    def __init__( self ):
        self.feed = None
        self.config = config = config_reader.SyncConfig()
        self.APPLICATION_NAME = config[ 'APPLICATION_NAME' ]
        self.EMAIL = config[ 'EMAIL' ]
        self.PASSWORD = config[ 'PASSWORD' ]
        self.SITE = config[ 'SITE' ]
        self.TOKEN_FILE = os.path.expanduser( config[ 'TOKEN_FILE' ] )
        self.MEETING_MINUTES = config[ 'MEETING_MINUTES' ]
        self.client = gdata.sites.client.SitesClient( source = self.APPLICATION_NAME,
                                                      site = self.SITE )
        self.client.ssl = True
        self.authClient()

    def writeToken( self, token ):
        fh = open( self.TOKEN_FILE, "w" )
        fh.write( token.token_string )
        fh.close()

    # to be called when a captcha is encountered
    # handles token-related things
    def handleCaptchaChallenge( self, challenge ):
        print 'Please visit ' + challenge.captcha_url
        answer = raw_input( 'Answer to the challenge? ' )
        token = self.client.ClientLogin( self.EMAIL, self.PASSWORD, 
                                         self.APPLICATION_NAME,
                                         captcha_token = challenge.captcha_token,
                                         captcha_response = answer )
        self.writeToken( token )
        self.feed = self.client.GetSiteFeed()

    # attempts to authenticate a client with a saved token
    # returns true if authentication was ok
    def authClientWithToken( self ):
        try:
            fh = open( self.TOKEN_FILE, "r" )
            token = fh.read()
            fh.close()
            self.client.auth_token = gdata.gauth.ClientLoginToken( token )
            self.feed = self.client.GetSiteFeed()
            return True
        except gdata.client.CaptchaChallenge as challenge:
            self.handleCaptchaChallenge( challenge )
        except:
            return False

    def authClient( self ):
        if not self.authClientWithToken():
            try:
                self.client.ClientLogin( self.EMAIL, self.PASSWORD,
                                         self.APPLICATION_NAME )
                self.writeToken( self.client.auth_token )
                self.feed = self.client.GetSiteFeed()
            except gdata.client.CaptchaChallenge as challenge:
                self.handleCaptchaChallenge( challenge )

    # gets the name of the meeting minute for this dat
    def meetingMinuteName( self ):
        return "Minutes for " + datetime.datetime.now().strftime( "%b %d, %Y" )

    # gets the url that will be generated for today's meeting minute name
    # note that it only returns the last part of the URL
    def meetingMinuteURL( self ):
        date = datetime.datetime.now().strftime( "%b-%d-%Y" ).lower()
        return "minutes-for-" + date

    # Amazingly, this is non-trivial to do.  The API claims there is a way to
    # directly pass a URL, but I gave up on this after trying around 200 combinations
    # of what it could possibly be.
    #
    # Note that the URL is relative to the base site.  I.e. to get:
    # https://sites.google.com/site/mysite/mydirectory/meeting-minutes,
    # specify: "/mydirectory/meeting-minutes
    def contentEntryForURL( self, relative ):
        absolute = '%s?path=%s' % ( self.client.MakeContentFeedUri(), relative )
        return self.client.GetContentFeed( uri = absolute ).entry

    # takes the HTML content
    # assumes that the page doesn't already exist
    def makeMeetingMinuteBlindly( self, content ):
        self.client.CreatePage( 'webpage',
                                self.meetingMinuteName(),
                                html = content,
                                parent = self.contentEntryForURL( self.MEETING_MINUTES )[ 0 ] )

    # returns the meeting minute page for today, or None if one doesn't
    # already exist
    def getMeetingMinutePage( self ):
        content = self.contentEntryForURL( self.MEETING_MINUTES + "/" + self.meetingMinuteURL() )
        if not content: # empty list - the page doesn't exist
            return None
        else:
            return content[ 0 ]

    def yesNoNone( self, response ):
        response = response.lower()
        if response in [ "y", "yes" ]:
            return True
        elif response in [ "n", "no" ]:
            return False
        else:
            return None

    def yesNoPrompt( self, textPrompt ):
        response = [ None ]
        def prompt():
            response[ 0 ] = self.yesNoNone( raw_input( textPrompt + " (yes/no)?: " ) )
            return response[ 0 ]

        while prompt() is None:
            print "Please answer yes or no"

        return response[ 0 ]

    def overwriteExistingPage( self, page, content ):
        self.client.Delete( page )
        self.makeMeetingMinuteBlindly( content )
        # According to the docs, the following two lines should work
        # However, it will completely strip out the HTML tags
        #page.content.html = content
        #self.client.Update( page )

    def makeMeetingMinute( self, content ):
        existing = self.getMeetingMinutePage()
        if existing and \
                self.yesNoPrompt( "Overwrite existing minutes" ):
            self.overwriteExistingPage( existing, content )
        elif not existing:
            self.makeMeetingMinuteBlindly( content )


# given a filename, returns the raw file data
# in a single string
def readRawFile( filename ):
    fh = open( filename, "r" )
    content = fh.read()
    fh.close()
    return content

def fileExtension( filename ):
    name, extension = os.path.splitext( filename )
    return extension

# reads in the given file, making sure it's in HTML format
# assumes that html files end in .html
def readFormatted( filename ):
    extension = fileExtension( filename )
    if extension in file_extension_parsers:
        contents = readRawFile( filename ).split( "\n" )
        return file_extension_parsers[ extension ]( contents )
    else:
        raise Exception( "Unknown file extension: {0}".format( extension ) )

# BEGIN MAIN
if __name__ == "__main__":
    if len( sys.argv ) == 2:
        content = readFormatted( sys.argv[ 1 ] )
        sc = SitesCommunicator()
        sc.makeMeetingMinute( content )
    else:
        print "Needs the name of a notes file to upload. Files ending in HTML" + \
            " are uploaded as-is, while files ending in either .txt or .notes" + \
            " will first be converted to HTML."
        



