import re
import os.path
import getpass

# merges the two dictionaries
# if a key is found that exists in both, then the merger
# function is called with the key from d1 and d2
def merge_dicts(merger, d1, d2):
    retval = {}
    for key, value in d1.iteritems():
        if key in d2:
            retval[key] = merger(value, d2[key])
        else:
            retval[key] = value

    for key, value in d2.iteritems():
        if key not in retval:
            retval[key] = value

    return retval

# reads configuation files of the following form:
# var1: val1
# whitespace between the values is ignored. If the whitespace is significant,
# enclose the value in quotes
class ConfigReader(object):
    VALUE_REGEX_STRING = '\s*"?([^"\s]+)"?\s*'
    VALUE_REGEX = re.compile(VALUE_REGEX_STRING)
    VARIABLE_REGEX_STRING = VALUE_REGEX_STRING
    VARIABLE_REGEX = re.compile(VARIABLE_REGEX_STRING)
    LINE_REGEX_STRING = "{0}:{1}".format(
        VARIABLE_REGEX_STRING,
        VALUE_REGEX_STRING)
    LINE_REGEX = re.compile(LINE_REGEX_STRING)

    def __init__(self, filename):
        self.config = {}
        self.read_file(filename)
        extra = self.get_extra_fields()
        if extra:
            raise Exception(
                "Unknown fields: {0}".format(", ".join(extra)))
        self.fill_in_missing_fields()
        self.add_optional_values()

    # merges in the optional values. Any user-defined values take
    # precedence
    def add_optional_values(self):
        self.config = merge_dicts(lambda x, y: x,
                                  self.config,
                                  self.optional_values())

    # gets fields that shouldn't be echoed in case the user inputs them
    # by default, this is empty
    def sensitive_fields(self):
        return frozenset()

    # gets the required fields.  By default, it returns an
    # empty set
    def required_fields(self):
        return frozenset()

    # gets optional fields, along with thir default
    # values.
    def optional_values(self):
        return dict()

    def parse_file_line(self, line):
        match = self.LINE_REGEX.match(line)
        if not match:
            raise ValueError("Malformed line: " + line)
        else:
            groups = match.groups()
            self.config[groups[0]] = groups[1]

    def parse_user_line(self, variable, line):
        match = self.VALUE_REGEX.match(line)

        if not match:
            raise ValueError("Malformed value: " + line)
        else:
            self.config[variable] = match.groups()[0]

    # given a function that takes user input, it returns an instrumented
    # version that prompts the user for input before asking for input
    def instrument_with_prompt(self, func):
        def instrumented(p):
            print p
            return func()
        return instrumented

    # returns a function that can read in the given variable
    # the function prints a prompt and gets input from the user
    def reader(self, variable):
        if variable in self.sensitive_fields():
            return self.instrument_with_prompt(getpass.getpass)
        else:
            return raw_input

    # prompts the user for the value of a given variable
    def get_user_input(self, variable):
        done = False
        while not done:
            prompt = "Enter value for \"" + variable + "\": "
            try:
                self.parse_user_line(
                    variable, 
                    self.reader(variable)(prompt))
                done = True
            except ValueError:
                print "Malformed value"

    def read_file(self, filename):
        with open(filename, "r") as fh:
            line = fh.readline()
            while line != "":
                self.parse_file_line(line)
                line = fh.readline()
        
    def config_key_set(self):
        return frozenset(self.config.keys())

    def optional_values_key_set(self):
        return frozenset(self.optional_values().keys())

    def get_missing_fields(self):
        return self.required_fields() - self.config_key_set()

    def get_extra_fields(self):
        norm_fields = self.required_fields().union(
            self.optional_values_key_set())
        return self.config_key_set() - norm_fields

    def fill_in_missing_fields(self):
        for field in self.get_missing_fields():
            self.get_user_input(field)

    def __getitem__(self, key):
        return self.config[key]

class SyncConfig(ConfigReader):
    SYNC_DIR = os.path.expanduser("~/.notes_sync")
    CONFIG_LOCATION = SYNC_DIR + "/config.txt"
    REQUIRED_FIELDS = frozenset(
        ["EMAIL", "PASSWORD", "SITE",
         "MEETING_MINUTES"])
    SENSITIVE_FIELDS = frozenset(['PASSWORD'])

    def __init__(self):
        super(SyncConfig, self).__init__(self.CONFIG_LOCATION)


    def required_fields(self):
        return self.REQUIRED_FIELDS

    def optional_values(self):
        token_file = self.SYNC_DIR + "/auth_token.txt"
        return {"APPLICATION_NAME" : "notes-sync",
                "TOKEN_FILE" : token_file}

    def sensitive_fields(self):
        return self.SENSITIVE_FIELDS

if __name__ == "__main__":
    print SyncConfig().config
