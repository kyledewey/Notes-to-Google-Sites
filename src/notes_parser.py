# This is intended to convert my typical notes to HTML
# My notes often look like this:
#
# PROJECT[:]
#
# -This is a main point
#    -This is a sub point
#    -This is another sub point
#
# This is some other text
# this is bad style but I do it sometimes
#

# the design of this is based on parser combinators
# each parser only understands how to parse one specific element
# each parser parses as much as it can at a time, in a greedy manner
#
from abc import ABCMeta, abstractmethod
from cgi import escape
import string
import sys

class ParseResult( object ):
    def __init__( self, parsed, remaining ):
        self.parsed = parsed
        self.remaining = remaining

    def __eq__( self, other ):
        return self.parsed == other.parsed and \
            self.remaining == other.remaining

# gets the number of whitespace characters before the line begins
def numLeadingWhitespace( line ):
    return len( line ) - len( line.lstrip() )

# determines if a line contains more uppercase letters
# than lowercase letters
def moreCaps( line ):
    uppers = [ c for c in line if c.isupper() ]
    lowers = [ c for c in line if c.islower() ]
    return len( uppers ) > len( lowers )

# chomps the given string off of the end of the given string, if
# the string is long enough and the character is there
# otherwise is doesn't touch the string
def chompString( string, postfix ):
    if string.endswith( postfix ):
        string = string[ : len( string ) - len( postfix ) ]
    return string

class Parser( object ):
    __metaclass__ = ABCMeta

    # returns a ParseResult
    @abstractmethod
    def parse( self, lines ):
        pass

def andParsers( *parsers ):
    if isinstance( parsers[ 0 ], tuple ):
        parsers = parsers[ 0 ]

    if len( parsers ) < 2:
        raise Exception( "Not enough arguments to andParsers" )
    elif len( parsers ) == 2:
        return AndParser( parsers[ 0 ], 
                          parsers[ 1 ] )
    else:
        return AndParser( parsers[ 0 ],
                          andParsers( parsers[ 1: ] ) )

class AndParser( Parser ):
    def __init__( self, p1, p2 ):
        super( AndParser, self ).__init__()
        self.p1 = p1
        self.p2 = p2

    def parse( self, lines ):
        p1Res = self.p1.parse( lines )
        p2Res = self.p2.parse( p1Res.remaining )
        return ParseResult( p1Res.parsed + p2Res.parsed,
                            p2Res.remaining )

class HeaderParser( Parser ):
    def __init__( self ):
        super( HeaderParser, self ).__init__()

    # headers start at the beginning of a line, and are mostly uppercase
    def isHeader( self, line ):
        return len( line ) > 0 and \
            line[ 0 ] != "-" and \
            numLeadingWhitespace( line ) == 0 and \
            moreCaps( line )

    def formatHeader( self, line ):
        return string.capwords( chompString( line, ":" ) )

    def toHeader( self, line ):
        return "<h3>%s</h3>\n" % escape( self.formatHeader( line ) )

    def parse( self, lines ):
        if len( lines ) > 0 and self.isHeader( lines[ 0 ] ):
            return ParseResult( self.toHeader( lines[ 0 ] ),
                                lines[ 1: ] )
        else:
            return ParseResult( "", lines )

class ListHeaderParser( Parser ):
    def __init__( self ):
        super( ListHeaderParser, self ).__init__()

    def parse( self, lines ):
        if len( lines ) == 0:
            return ParseResult( "", [] )

        parsed = ""
        remaining = lines
        line = lines[ 0 ]
        stripped = line.lstrip()
        if len( stripped ) >= 1 and stripped[ 0 ] == "-":
            parsed = "<ul>\n"
            inner = ListParser( len( line ) - len( stripped ) ).parse( lines )
            parsed += inner.parsed + "</ul>\n"
            remaining = inner.remaining

        return ParseResult( parsed, remaining )

class ListElementParser( Parser ):
    # numIn is the number of whitespace we are in
    def __init__( self, numIn = 0 ):
        super( ListElementParser, self ).__init__()
        self.numIn = numIn

    # assumes that it will be initially called on a list element
    def parse( self, lines ):
        parsed = lines[ 0 ].lstrip()[ 1: ] + " "
        lines = lines[ 1: ]
        strippedLine = [ parsed ]

        # python doesn't allow assignment in an expression...
        def stripAndLen( line ):
            strippedLine[ 0 ] = line.lstrip()
            return len( strippedLine[ 0 ] )

        while( len( lines ) > 0 and \
                   numLeadingWhitespace( lines[ 0 ] ) >= self.numIn and \
                   stripAndLen( lines[ 0 ] ) >= 1 and \
                   strippedLine[ 0 ][ 0 ] != "-" ):
            parsed += strippedLine[ 0 ] + " "
            lines = lines[ 1: ]

        return ParseResult( parsed[ :-1 ], lines )

class ListParser( Parser ):
    # numIn is the number of whitespace we are in
    # assumes that the list tag has already been started
    def __init__( self, numIn = 0 ):
        super( ListParser, self ).__init__()
        self.numIn = numIn

    # attempts to parse in a group of lines at the same indent level
    # this may need to be repeatedly called, as with:
    # -outer
    #   -inner
    # -outer
    # returns a ParseResult for the first outer line
    def parseGroup( self, lines ):
        parsed = ""
        leading = [None]
        
        def setAndGetLeading( line ):
            leading[ 0 ] = numLeadingWhitespace( line )
            return leading[ 0 ]

        while len( lines ) > 0 and \
                setAndGetLeading( lines[ 0 ] ) == self.numIn and \
                len( lines[ 0 ] ) > leading[ 0 ] and \
                lines[ 0 ][ leading[ 0 ] ] == "-":
            element = ListElementParser( self.numIn ).parse( lines )
            parsed += "<li>%s</li>\n" % element.parsed
            lines = element.remaining
            
        return ParseResult( parsed, lines )

    def parse( self, lines ):
        parsed = ""
        stripped = [ None ]

        def setAndGetLen( line ):
            stripped[ 0 ] = line.lstrip()
            return len( stripped[ 0 ] )

        while len( lines ) > 0 and \
                setAndGetLen( lines[ 0 ] ) >= 1 and \
                stripped[ 0 ][ 0 ] == "-":
            res = None
            leading = numLeadingWhitespace( lines[ 0 ] )
            if leading == self.numIn:
                res = self.parseGroup( lines )
            elif leading > self.numIn:
                res = ListHeaderParser().parse( lines )
            else: # leading < self.numIn
                break
            
            parsed += res.parsed
            lines = res.remaining

        return ParseResult( parsed, lines )

class BreakParser( Parser ):
    def __init__( self ):
        super( BreakParser, self ).__init__()

    def parse( self, lines ):
        if len( lines ) > 0 and len( lines[ 0 ] ) == numLeadingWhitespace( lines[ 0 ] ):
            return ParseResult( "<br/>\n", lines[ 1: ] )
        else:
            return ParseResult( "", lines )

class NotesParser( Parser ):
    def __init__( self ):
        super( NotesParser, self ).__init__()

    def parse( self, lines ):
        parsed = ""
        openFreeText = False

        while len( lines ) > 0:
            res = andParsers( HeaderParser(),
                              ListHeaderParser(),
                              BreakParser() ).parse( lines )
            if res.parsed == "": # we got nowhere - free text
                assert( res.remaining == lines )
                if openFreeText: # already in open text
                    parsed += escape( lines[ 0 ] )
                else: # not already in open text
                    openFreeText = True
                    parsed += "<p>%s " % escape( lines[ 0 ] )
                lines = lines[ 1: ]
            elif openFreeText: # we got past the free text
                openFreeText = False
                parsed += "</p>\n" + res.parsed
                lines = res.remaining
            else: # parse not involving free text
                parsed += res.parsed
                lines = res.remaining

        if openFreeText:
            parsed += "</p>\n"
            openFreeText = False

        return ParseResult( parsed, [] )

def toLines( string ):
    return string.split( "\n" )

class Notes2HTML( object ):
    def chomp( self, line ):
        if len( line ) > 0 and line[ len( line ) - 1 ] == "\n":
            line = line[ : -1 ]
        return line

    def readLines( self, filename ):
        fh = open( filename, "r" )
        lines = fh.read()
        fh.close()
        return toLines( lines )
    
    def convertContents( self, contents ):
        return "<html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"en\">" + NotesParser().parse( contents ).parsed + "</html>\n"

    def convertFile( self, filename ):
        return self.convertContents( self.readLines( filename ) )

if __name__ == "__main__":
    if len( sys.argv ) == 2:
        print Notes2HTML().convertFile( sys.argv[ 1 ] )
    else:
        print "Needs an input text file."
