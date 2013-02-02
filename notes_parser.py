#!/usr/bin/env python

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
import re

class ParseResult( object ):
    def __init__( self, parsed, remaining ):
        self.parsed = parsed
        self.remaining = remaining

    def __eq__( self, other ):
        return self.parsed == other.parsed and \
            self.remaining == other.remaining

# given two strings, it will concatenate them so there is exactly
# one space in between them
def concatWithSpace( str1, str2 ):
    return str1.rstrip() + " " + str2.lstrip()

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
    REGEX_STRING = "^[^\-.]+"
    REGEX = re.compile( REGEX_STRING )

    def __init__( self ):
        super( HeaderParser, self ).__init__()

    # headers start at the beginning of a line, and are mostly uppercase
    def isHeader( self, line ):
        return self.REGEX.match( line ) and \
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
    REGEX_STRING = "^(\s*)-"
    REGEX = re.compile( REGEX_STRING )
    def __init__( self ):
        super( ListHeaderParser, self ).__init__()

    def parse( self, lines ):
        if len( lines ) == 0:
            return ParseResult( "", [] )
        else:
            parsed = ""
            remaining = lines
            match = self.REGEX.match( lines[ 0 ] )
            if match:
                leadingSize = len( match.groups()[ 0 ] )
                parsed = "<ul>\n"
                inner = ListParser( leadingSize ).parse( lines )
                parsed += inner.parsed + "</ul>\n"
                remaining = inner.remaining
            return ParseResult( parsed, remaining )

class ListElementParser( Parser ):
    # numIn is the number of whitespace we are in
    def __init__( self, numIn = 0 ):
        super( ListElementParser, self ).__init__()
        self.numIn = numIn
        self.regexStringFirstLine = '^\s{%s}-(.*)' % (numIn)
        self.regexFirstLine = re.compile( self.regexStringFirstLine )
        self.regexStringNextLinesWhitespace = '^\s{%s,}' % (numIn)
        self.regexNextLinesWhitespace = \
            re.compile( self.regexStringNextLinesWhitespace )
        self.regexStringNextLinesContent = '^([^-].+)'
        self.regexNextLinesContent = \
            re.compile( self.regexStringNextLinesContent )

    def firstLineText( self, line ):
        return self.regexFirstLine.match( line ).groups()[ 0 ]

    # returns the text of the next lines, or None if it's not a valid
    # portion of a list element
    def restLinesText( self, line ):
        # note that python lacks an atomic grouping operator or a possessive
        # quantifier, so a regex like:
        # ^\s{%s,}([^-].+) is insufficient in and of itself.  it will backtrack
        # itself into accepting.
        if self.regexNextLinesWhitespace.match( line ):
            match = self.regexNextLinesContent.match( line.lstrip() )
            if match:
                return match.groups()[ 0 ]
        return None
        
    # assumes that it will be initially called on a list element
    def parse( self, lines ):
        parsed = self.firstLineText( lines[ 0 ] )
        lines = lines[ 1: ]
        done = False

        while len( lines ) > 0 and not done:
            curLine = self.restLinesText( lines[ 0 ] )
            if curLine:
                parsed = concatWithSpace( parsed, curLine )
                lines = lines[ 1: ]
            else:
                done = True

        return ParseResult( parsed, lines )

class ListGroupParser( Parser ):
    # numIn is the number of whitespace we are in
    # assumes that the list tag has already been started
    def __init__( self, numIn = 0 ):
        super( ListGroupParser, self ).__init__()
        self.numIn = numIn
        self.regexString = '(^\s{%s})-.*' % (numIn)
        self.regex = re.compile( self.regexString )

    def parse( self, lines ):
        parsed = ""
        done = False
        while lines and not done:
            match = self.regex.match( lines[ 0 ] )
            if match:
                element = ListElementParser( self.numIn ).parse( lines )
                parsed += "<li>%s</li>\n" % element.parsed
                lines = element.remaining
            else:
                done = True

        return ParseResult( parsed, lines )

class ListParser( Parser ):
    # numIn is the number of whitespace we are in
    # assumes that the list tag has already been started
    def __init__( self, numIn = 0 ):
        super( ListParser, self ).__init__()
        self.numIn = numIn
        self.regexString = '(^\s*)-.*'
        self.regex = re.compile( self.regexString )

    def parse( self, lines ):
        parsed = ""
        done = False
        while lines and not done:
            match = self.regex.match( lines[ 0 ] )
            if match:
                res = None
                numWhitespace = len( match.groups()[ 0 ] )
                if numWhitespace == self.numIn:
                    res = ListGroupParser( self.numIn ).parse( lines )
                elif numWhitespace > self.numIn:
                    res = ListHeaderParser().parse( lines )
                else: # leading < self.numIn
                    done = True
                
                if res: # if we have something to add
                    parsed += res.parsed
                    lines = res.remaining
            else:
                done = True # if we didn't match

        return ParseResult( parsed, lines )
                    
class BreakParser( Parser ):
    REGEX_STRING = "^\s*$"
    REGEX = re.compile( REGEX_STRING )

    def __init__( self ):
        super( BreakParser, self ).__init__()

    def parse( self, lines ):
        if lines and self.REGEX.match( lines[ 0 ] ):
            return ParseResult( "<br/>\n", lines[ 1: ] )
        else:
            return ParseResult( "", lines )

class NotesParser( Parser ):
    COMPOSITE_PARSER = andParsers( HeaderParser(),
                                   ListHeaderParser(),
                                   BreakParser() )
    def __init__( self ):
        super( NotesParser, self ).__init__()

    def parse( self, lines ):
        parsed = ""
        openFreeText = False

        while len( lines ) > 0:
            res = self.COMPOSITE_PARSER.parse( lines )
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

        # if we ended with free text, then we still need to close it
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
