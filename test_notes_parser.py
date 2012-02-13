from notes_parser import *
import unittest

class TestParsers( unittest.TestCase ):
    def test_numLeadingWhitespace1( self ):
        self.assertEqual( numLeadingWhitespace( "   something   " ), 3 )

    def test_numLeadingWhitespace2( self ):
        self.assertEqual( numLeadingWhitespace( "something   " ), 0 )

    def test_moreCaps1( self ):
        self.assertFalse( moreCaps( "AaBbCc" ) )
        
    def test_moreCaps2( self ):
        self.assertTrue( moreCaps( "AaBbCcC" ) )

    def test_chomp1( self ):
        self.assertEqual( chompString( "something", ":" ), "something" )

    def test_chomp1( self ):
        self.assertEqual( chompString( "something:", ":" ), "something" )

    def test_header1( self ):
        self.assertEqual( HeaderParser().parse( ["FOO:"] ).parsed,
                          "<h3>Foo</h3>\n" )
    
    def test_header2( self ):
        res = HeaderParser().parse( toLines( "FOO\nBAR" ) )
        self.assertEqual( res.parsed, "<h3>Foo</h3>\n" )
        self.assertEqual( res.remaining, [ "BAR" ] )
        
    def test_header3( self ):
        self.assertEqual( HeaderParser().parse( ["-FOO:"] ).parsed,
                          "" )

    def test_listelement1( self ):
        self.assertEqual( ListElementParser().parse( toLines( \
                    "-moocow" ) ).parsed,
                          "moocow" )

    def test_tolines( self ):
        self.assertEqual( toLines( "-something\nor other\n\n" ),
                          [ '-something', 'or other', '', '' ] )

    def test_listelement2( self ):
        self.assertEqual( ListElementParser().parse( toLines( \
                    "-something\nor other\n\n-foo" ) ).parsed,
                          "something or other" )

    def test_listelement3( self ):
        self.assertEqual( ListElementParser().parse( toLines( \
                    "-some really1 really2\n" +
                    "really3\n" +
                    " really4\n" +
                    "  really5\n" +
                    "really6 long text" ) ).parsed,
                          "some really1 really2 really3 really4 really5 really6 long text" )
                                                         
    def test_listp_group( self ):
        self.assertEqual( ListParser().parseGroup( toLines( \
                    "-outer1\n-outer2" ) ).parsed,
                          "<li>outer1</li>\n<li>outer2</li>\n" )

    def test_list_header( self ):
        self.assertEqual( ListHeaderParser().parse( toLines( \
                    "-outer1\n-outer2" ) ).parsed,
                          "<ul>\n<li>outer1</li>\n<li>outer2</li>\n</ul>\n" )

    def test_list_header2( self ):
        self.assertEqual( ListHeaderParser().parse( toLines( \
                    "-outer1\n -inner\n-outer2" ) ).parsed,
                          "<ul>\n<li>outer1</li>\n<ul>\n<li>inner</li>\n</ul>\n<li>outer2</li>\n</ul>\n" )

    def test_break1( self ):
        self.assertEqual( BreakParser().parse( toLines( \
                    " \nsomething" ) ).parsed,
                          "<br/>\n" )

    def test_break2( self ):
        self.assertEqual( BreakParser().parse( toLines( \
                    "" ) ).parsed,
                          "<br/>\n" )

    def test_text( self ):
        self.assertEqual( NotesParser().parse( toLines( \
                    "something\nsomething else" ) ).parsed,
                          "<p>something something else</p>\n" )

    def test_multiline_noindents( self ):
        self.assertEqual( NotesParser().parse( toLines( \
                    "-something\nor\nother\n" ) ).parsed,
                          "<ul>\n" + \
                              "<li>something or other</li>\n" + \
                              "</ul>\n" + \
                              "<br/>\n" )

    def test_combo( self ):
        self.assertEqual( NotesParser().parse( toLines( \
                    "HEADER:\n\n-outer1\n -inner1\n -inner2\n-outer2\n\nsome free text\n" ) ).parsed,
                          "<h3>Header</h3>\n" + \
                              "<br/>\n" + \
                              "<ul>\n" + \
                              "<li>outer1</li>\n" + \
                              "<ul>\n" + \
                              "<li>inner1</li>\n" + \
                              "<li>inner2</li>\n" + \
                              "</ul>\n" + \
                              "<li>outer2</li>\n" + \
                              "</ul>\n" + \
                              "<br/>\n" + \
                              "<p>some free text </p>\n" + \
                              "<br/>\n" )
                                               

if __name__ == "__main__":
    unittest.main()

