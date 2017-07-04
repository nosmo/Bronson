#!/usr/bin/env python3
"""A class for storing and managing wordlists"""

class Wordlist(object):

    def __init__(self):

        self.wordlist = {
            "path": [],
            "filename": [],
            "extension": [],
        }

    def path(self):
        """Get all paths stored"""
        return self.wordlist["path"]

    def filename(self):
        """Get all filenames stored"""
        return self.wordlist["filename"]

    def extension(self):
        """Get all extensions stored"""
        return self.wordlist["extension"]

    def add_wordlist(self, list_type, filename):
        """Add a wordlist.

        list_type: a string indicating the list type
        filename: the name of the file to load
        """

        if list_type not in self.wordlist.keys():
            raise KeyError(
                "%s is not a valid wordlist type - valid types are %s" % (
                    list_type,
                    self.wordlist.keys()
                )
            )

        with open(filename) as wordlist_f:

            self.wordlist[list_type] += [ i.strip() for i in wordlist_f.read().split("\n") if i.strip() ]
            self.wordlist[list_type] = list(set(self.wordlist[list_type]))

    def permute_filenames(self):
        """Generate a complete list of filenames using the basenames and extensions."""
        return [ "%s.%s" % (pre, post) for pre in self.wordlist["filename"] \
                 for post in self.wordlist["extension"] ]
