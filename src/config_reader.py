import re
import os.path
import getpass

# merges the two dictionaries
# if a key is found that exists in both, then the merger
# function is called with the key from d1 and d2
def mergeDicts( merger, d1, d2 ):
    retval = {}
    for ( key, value ) in d1.iteritems():
        if key in d2:
            retval[ key ] = merger( value, d2[ key ] )
        else:
            retval[ key ] = value

    for ( key, value ) in d2.iteritems():
        if key not in retval:
            retval[ key ] = value

    return retval

# reads configuation files of the following form:
# var1: val1
# whitespace between the values is ignored. If the whitespace is significant,
# enclose the value in quotes
class ConfigReader( object ):
    VALUE_REGEX = '\s*"?([^"\s]+)"?\s*'
    VARIABLE_REGEX = VALUE_REGEX
    LINE_REGEX = VARIABLE_REGEX + ":" + VALUE_REGEX

    def __init__( self, filename ):
        self.config = {}
        self.readFile( filename )
        extra = self.getExtraFields()
        if extra:
            raise Exception( "Unknown fields: " + ", ".join( extra ) )
        self.fillInMissingFields()
        self.addOptionalValues()

    # merges in the optional values. Any user-defined values take
    # precedence
    def addOptionalValues( self ):
        self.config = mergeDicts( lambda x, y: x,
                                  self.config,
                                  self.optionalValues() )

    # gets fields that shouldn't be echoed in case the user inputs them
    # by default, this is empty
    def sensitiveFields( self ):
        return set()
    # gets the required fields.  By default, it returns an
    # empty set
    def requiredFields( self ):
        return set()

    # gets optional fields, along with thir default
    # values.
    def optionalValues( self ):
        return dict()

    def parseFileLine( self, line ):
        groups = re.match( self.LINE_REGEX, line ).groups()

        if not groups:
            raise ValueError( "Malformed line: " + line )
        else:
            self.config[ groups[ 0 ] ] = groups[ 1 ]

    def parseUserLine( self, variable, line ):
        groups = re.match( self.VALUE_REGEX, line ).groups()

        if not groups:
            raise ValueError( "Malformed value: " + line )
        else:
            self.config[ variable ] = groups[ 0 ]

    # given a function that takes user input, it returns an instrumented
    # version that prompts the user for input before asking for input
    def instrumentWithPrompt( self, func ):
        def instrumented( p ):
            print p
            return func()
        return instrumented

    # returns a function that can read in the given variable
    # the function prints a prompt and gets input from the user
    def reader( self, variable ):
        if variable in self.sensitiveFields():
            return self.instrumentWithPrompt( getpass.getpass )
        else:
            return raw_input

    # prompts the user for the value of a given variable
    def getUserInput( self, variable ):
        done = False
        while not done:
            "Enter value for \"" + variable + "\": ",
            try:
                r = self.reader( variable )
                self.parseUserLine( variable, 
                                    r( "Enter value for \"" + \
                                           variable + "\": " ) )
                done = True
            except ValueError:
                print "Malformed value"
                
    def readFile( self, filename ):
        fh = open( filename, "r" )
        try:
            line = fh.readline()
            while line != "":
                self.parseFileLine( line )
                line = fh.readline()
        finally:
            fh.close()
        
    def keySet( self ):
        return set( self.config.keys() )

    def getMissingFields( self ):
        return self.requiredFields() - self.keySet()

    def getExtraFields( self ):
        return self.keySet() - \
            self.requiredFields().union( set( self.optionalValues().keys() ) ) 

    def fillInMissingFields( self ):
        for field in self.getMissingFields():
            self.getUserInput( field )

    def __getitem__( self, key ):
        return self.config[ key ]

class SyncConfig( ConfigReader ):
    SYNC_DIR = os.path.expanduser( "~/.notes_sync" )
    CONFIG_LOCATION = SYNC_DIR + "/config.txt"
    def __init__( self ):
        super( SyncConfig, self ).__init__( self.CONFIG_LOCATION )

    def requiredFields( self ):
        return set( [ "EMAIL", "PASSWORD", "SITE",
                      "MEETING_MINUTES" ] )

    def optionalValues( self ):
        token_file = self.SYNC_DIR + "/auth_token.txt"
        return { "APPLICATION_NAME" : "notes-sync",
                 "TOKEN_FILE" : token_file }

    def sensitiveFields( self ):
        return set( [ 'PASSWORD' ] )

if __name__ == "__main__":
    print SyncConfig().config
