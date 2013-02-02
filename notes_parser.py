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

from abc import ABCMeta, abstractmethod
from cgi import escape
import string
import sys
import re

class ParseResult(object):
    def __init__(self, parsed, remaining):
        self.parsed = parsed
        self.remaining = remaining

    def __eq__(self, other):
        return (self.parsed == other.parsed and 
                self.remaining == other.remaining)

def concat_with_space(str1, str2):
    """Given two strings, it will concatenate 
    them so there is exactly one space in between them"""

    return "{0} {1}".format(str1.rstrip(),
                            str2.lstrip())

def num_leading_whitespace(line):
    """Gets the number of whitespace characters before 
    the line begins"""

    return len(line) - len(line.lstrip())

def more_caps(line):
    """Determines if a line contains more uppercase letters
    than lowercase letters"""
    uppers = [c for c in line if c.isupper()]
    lowers = [c for c in line if c.islower()]
    return len(uppers) > len(lowers)

def chomp_string(string, postfix):
    """Chomps the given string off of the end of the given string, if
    the string is long enough and the character is there
    otherwise is doesn't touch the string"""
    if string.endswith(postfix):
        up_to_postfix = len(string) - len(postfix)
        string = string[:up_to_postfix]
    return string

class Parser(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def parse(self, lines):
        """Returns a ParseResult"""
        pass

def and_parsers(*parsers):
    if isinstance(parsers[0], tuple):
        parsers = parsers[0]

    if len(parsers) < 2:
        raise Exception("Not enough arguments to and_parsers")
    elif len(parsers) == 2:
        return AndParser(parsers[0],
                         parsers[1])
    else:
        return AndParser(parsers[0],
                         and_parsers(parsers[1:]))

class AndParser(Parser):
    def __init__(self, p1, p2):
        super(AndParser, self).__init__()
        self.p1 = p1
        self.p2 = p2

    def parse(self, lines):
        p1Res = self.p1.parse(lines)
        p2Res = self.p2.parse(p1Res.remaining)
        return ParseResult(p1Res.parsed + p2Res.parsed,
                           p2Res.remaining)

class HeaderParser(Parser):
    REGEX_STRING = "^[^\-.]+"
    REGEX = re.compile(REGEX_STRING)

    def __init__(self):
        super(HeaderParser, self).__init__()

    def is_header(self, line):
        """Headers start at the beginning of a line,
        and are mostly uppercase"""

        return (self.REGEX.match(line) and 
                more_caps(line))

    @staticmethod
    def format_header(line):
        return string.capwords(chomp_string(line, ":"))

    @staticmethod
    def to_header(line):
        return "<h3>{0}</h3>\n".format(
            escape(HeaderParser.format_header(line)))

    def parse(self, lines):
        if len(lines) > 0 and self.is_header(lines[0]):
            return ParseResult(self.to_header(lines[0]),
                               lines[1:])
        else:
            return ParseResult("", lines)

class ListHeaderParser(Parser):
    REGEX_STRING = "^(\s*)-"
    REGEX = re.compile(REGEX_STRING)

    def __init__(self):
        super(ListHeaderParser, self).__init__()

    def parse(self, lines):
        if len(lines) == 0:
            return ParseResult("", [])
        else:
            parsed = ""
            remaining = lines
            match = self.REGEX.match(lines[0])
            if match:
                leadingSize = len(match.groups()[0])
                parsed = "<ul>\n"
                inner = ListParser(leadingSize).parse(lines)
                parsed += inner.parsed + "</ul>\n"
                remaining = inner.remaining
            return ParseResult(parsed, remaining)
            
            
class ListElementParser(Parser):
    REGEX_STRING_NEXT_LINES_CONTENT = '^([^-].+)'
    REGEX_NEXT_LINES_CONTENT = \
        re.compile(REGEX_STRING_NEXT_LINES_CONTENT)

    def __init__(self, num_in=0):
        """num_in is the number of whitespace we are in"""

        super(ListElementParser, self).__init__()
        self.num_in = num_in
        regex_string_first_line = '^\s{{{0}}}-(.*)'.format(num_in)
        self.regex_first_line = re.compile(regex_string_first_line)
        regex_string_next_lines_whitespace = '^\s{{{0},}}'.format(num_in)
        self.regex_next_lines_whitespace = \
            re.compile(regex_string_next_lines_whitespace)

    def first_line_text(self, line):
        return self.regex_first_line.match(line).groups()[0]

    def rest_lines_text(self, line):
        """Returns the text of the next lines, or None if it's not a valid
        portion of a list element"""
        # note that python lacks an atomic grouping operator or a possessive
        # quantifier, so a regex like:
        # ^\s{%s,}([^-].+) is insufficient in and of itself. It will backtrack
        # itself into accepting.
        if self.regex_next_lines_whitespace.match(line):
            match = self.REGEX_NEXT_LINES_CONTENT.match(line.lstrip())
            if match:
                return match.groups()[0]
        return None
        
    def parse(self, lines):
        """Assumes that it will be initially called on a list element"""

        parsed = self.first_line_text(lines[0])
        lines = lines[1:]
        done = False

        while len(lines) > 0 and not done:
            cur_line = self.rest_lines_text(lines[0])
            if cur_line:
                parsed = concat_with_space(parsed, cur_line)
                lines = lines[1:]
            else:
                done = True

        return ParseResult(parsed, lines)


class ListGroupParser(Parser):
    def __init__(self, num_in=0):
        """num_in is the number of whitespace we are in
        assumes that the list tag has already been started"""
        super(ListGroupParser, self).__init__()
        self.num_in = num_in
        regex_string = '(^\s{{{0}}})-.*'.format(num_in)
        self.regex = re.compile(regex_string)

    def parse(self, lines):
        parsed = ""
        done = False
        while lines and not done:
            match = self.regex.match(lines[0])
            if match:
                element = ListElementParser(self.num_in).parse(lines)
                parsed += "<li>{0}</li>\n".format(element.parsed)
                lines = element.remaining
            else:
                done = True

        return ParseResult(parsed, lines)

class ListParser(Parser):
    REGEX_STRING = '(^\s*)-.*'
    REGEX = re.compile(REGEX_STRING)

    def __init__(self, num_in=0):
        """num_in is the number of whitespace we are in
        assumes that the list tag has already been started"""
        super(ListParser, self).__init__()
        self.num_in = num_in

    def parse(self, lines):
        parsed = ""
        done = False
        while lines and not done:
            match = self.REGEX.match(lines[0])
            if match:
                res = None
                num_whitespace = len(match.groups()[0])
                if num_whitespace == self.num_in:
                    res = ListGroupParser(self.num_in).parse(lines)
                elif num_whitespace > self.num_in:
                    res = ListHeaderParser().parse(lines)
                else: # leading < self.numIn
                    done = True
                
                if res: # if we have something to add
                    parsed += res.parsed
                    lines = res.remaining
            else:
                done = True # if we didn't match

        return ParseResult(parsed, lines)
                    
class BreakParser(Parser):
    REGEX_STRING = "^\s*$"
    REGEX = re.compile(REGEX_STRING)

    def __init__(self):
        super(BreakParser, self).__init__()

    def parse(self, lines):
        if lines and self.REGEX.match(lines[0]):
            return ParseResult("<br/>\n", lines[1:])
        else:
            return ParseResult("", lines)

class NotesParser(Parser):
    COMPOSITE_PARSER = and_parsers(HeaderParser(),
                                   ListHeaderParser(),
                                   BreakParser())
    def __init__( self ):
        super(NotesParser, self).__init__()

    def parse(self, lines):
        parsed = ""
        open_free_text = False

        while len(lines) > 0:
            res = self.COMPOSITE_PARSER.parse(lines)
            if res.parsed == "": # we got nowhere - free text
                assert(res.remaining == lines)
                if open_free_text: # already in open text
                    parsed += escape(lines[0])
                else: # not already in open text
                    open_free_text = True
                    parsed += "<p>{0} ".format(escape(lines[0]))
                lines = lines[ 1: ]
            elif open_free_text: # we got past the free text
                open_free_text = False
                parsed += "</p>\n" + res.parsed
                lines = res.remaining
            else: # parse not involving free text
                parsed += res.parsed
                lines = res.remaining

        # if we ended with free text, then we still need to close it
        if open_free_text:
            parsed += "</p>\n"
            open_free_text = False

        return ParseResult(parsed, [])

def to_lines(string):
    return string.split("\n")

class Notes2HTML(object):
    HTML_HEADER = \
        "<html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"en\">"

    @staticmethod
    def chomp(line):
        return chomp_string(line, "\n")

    @staticmethod
    def read_lines(filename):
        with open(filename, "r") as fh:
            return to_lines(fh.read())

    def convert_contents(self, contents):
        return "{0}{1}</html>\n".format(
            self.HTML_HEADER,
            NotesParser().parse(contents).parsed)

    def convert_file(self, filename):
        return self.convert_contents(
            self.read_lines(filename))

if __name__ == "__main__":
    if len(sys.argv) == 2:
        print Notes2HTML().convert_file(sys.argv[1])
    else:
        print "Needs an input text file."
