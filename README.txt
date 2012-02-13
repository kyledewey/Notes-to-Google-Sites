NOTES SYNCHRONIZER

This tool is intended for people who synchronize notes through Google sites.
It's purpose is to automatically parse text notes into HTML, and then upload
them to Google sites.

DEPENDENCIES:
-Python > 2.2 will need to be installed
-gdata Python library
(available from http://code.google.com/p/gdata-python-client/downloads/list).
gdata 2.0.16 was used in the development of this, though any 2.* version should
work.

INSTALLING:
-mkdir ~/.notes_sync
-touch ~/.notes_sync/config.txt # see CONFIGURATION for config details
If you want to run it from other directories, you'll need
to set up your PATH and PYTHONPATH environment variables to point to the
script.

CONFIGURATION:
The config.txt file holds all the configuration information. It's not
neccessary to put anything in this file for proper operation (though the file
must exist for proper operation).  However, you'll be prompted for any 
variables not specified, so this is annoying. The script understands these
options (and the following config file format):

EMAIL : "my.email.address@domain"
PASSWORD : "myPasswordThatProbablyShouldn'tBeStoredHere"
SITE : "google site - not the full domain name, just the site name"
MEETING_MINUTES : "Where to upload notes to the site. Each note will be a
		   subpage under this page. For example, if your site is
		   called 'mysite' and you want to upload under the 'notes'
		   directory that exists at the toplevel, then this should
		   be '/notes'. As an aside, configuration options cannot
		   span multiple lines as shown here."
APPLICATION_NAME : "optional parameter descibing the synchronizer's name.
		    Defaults to 'notes-sync'"
TOKEN_FILE : "optional parameter specifying where authentication tokens are
	      stored. Defaults to ~/.notes_sync/auth_token.txt"

The password can be stored in this file, but it shouldn't be for security
reasons. As with any other parameter, you'll be prompted for it if not provided,
though with passwords the input won't echo (a security feature).

USAGE:
./sync.py myNotes.txt

This will convert myNotes.txt to HTML and attempt to upload it to Google sites,
using all the configuration information provided (either from the config file
or through prompts). The subpage name will be of the form 
'Minutes for Feb 12, 2012', substituting in the appropriate date.  If notes
have already been uploaded for the day, then one will be prompted whether or
not we should overwrite.  If we don't overwrite, then nothing is uploaded.
(A potential future feature is to overwrite or append, but currently it is
 only possible to overwrite.)

HTML CONVERSION:
The conversion is fairly basic.  It only understands headers, line breaks,
bullet points, and free text.  Anything that isn't a header, line break,
or a bullet point is considered free text.

Headers are defined by a line that begins with no whitespace, doesn't begin
with "-", and contains more capital letters than lowercase letters. Headers
use the <h3> HTML tags.

Bullet points are defined by a line that begins with potentially some
whitespace and a "-".  These can be nested to arbitrary levels. Note that
this is whitespace sensitive.  For example:
-outer1
	-inner1
	 -inner2
-outer2

...will be interpreted as:
-outer1
	-inner1
		-inner2
-outer2

...due to the extra space before "-inner2".  For that matter, spaces and
tabs are considered equal for this determination.  For example:
"\t  \t" == "\t\t  " == "    " == ...

The text after the "-" is permitted to wrap multiple lines, as long as the
text is at the same level as the point or if it's nested need.  For example:
-some really1 really2
really3
 really4
  really5
really6 long text

...will get interpreted as:
-some really1 really2 really3 really4 really5 really6 long text

Lists use the HTML <ul> and <li> tags.

Line breaks are simply two newlines next to each other. These use the
HTML <br> tag.

Free text (i.e. everything else) uses the HTML <p> tag.

LACKING FEATURES:
-Cannot change page titles
-Can only overwrite existing notes for a day as opposed to merging

KNOWN ISSUES:
-If the password is given incorrectly, there is no way to try to fix it
 without rerunning the whole script

EMACS INTEGRATION:
The file "notes-mode.el" defines a mode for notes.  At the time of writing, 
it doesn't do anything special for notes other than showing that they
are notes, indicated by the .notes file extension. The important bit
of the file is the sync-notes command, which will attempt to save the
current buffer and sync it up with Google sites.  The behavior is the
same as when the script is invoked separately; it is possible to be
prompted for information, etc. At this time, it is not possible to sync
notes without first saving them to the local disk.

INSTALLING EMACS PLUGIN:
mkdir ~/.emacs.d/notes
cp notes-mode.el ~/.emacs.d/notes

...then add the following lines to your ~/.emacs file:
(add-to-list 'load-path "~/.emacs.d/notes" )
(load "notes-mode")
(require 'notes-mode)

