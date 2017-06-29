#!/usr/bin/env python3

import itertools

import requests

FOLLOW_REDIRECTS = False

HTTP_METHODS = {
    "GET": requests.get,
    "POST": requests.post,
    "HEAD": requests.head
}


class BruteResults(dict):

    def __init__(self):
        pass

    def __setattr__(self, other_url, other):
        self.__dict__[other_url] = other
        print("added %s" % other_url)

    def add_result(self, requests_obj):
        self.__dict__[requests_obj.url] = requests_obj
        return requests_obj.ok

    def __iter__(self):
        for (key, val) in self.__dict__.iteritems():
            yield (key, val)


class Durrduster(object):

    def __init__(self, domain, protocol="https"):

        self.domain = domain
        self.protocol = protocol
        self.results = BruteResults()

        self.wordlist = {
            "path": ["/"],
            "filename": [],
            "extension": [],
        }

    def add_wordlist(self, list_type, filename):
        if list_type not in self.wordlist.keys():
            raise IndexError("%s is not a valid wordlist type - valid types are %s" % (
                list_type,
                self.wordlist.keys()))

        with open(filename) as wordlist_f:
            self.wordlist[list_type] += [ i.strip() for i in wordlist_f.read().split("\n") if i ]
            self.wordlist[list_type] = list(set(self.wordlist[list_type]))
            print(self.wordlist)

    def brute_section(self, brute_iterator, method, follow_redirects):
        # Brute_iterator could be a list of paths, filenames, mutated paths
        for component in brute_iterator:
            request_obj = self.check(component, method, follow_redirects)
            result = self.results.add_result(request_obj)
            if result:
                print("Hit for %s" % request_obj.url)
                print(request_obj.status_code)

    def brute(self, follow_redirects, method="GET"):
        # lol, overthinking it
        #complete_filelist = [ list(zip(self.wordlist["filename"], i)) \
        #                      for i in itertools.permutations(self.wordlist["extension"]) ]
        complete_filelist = [ "%s.%s" % (pre, post) for pre in self.wordlist["filename"] \
                              for post in self.wordlist["extension"] ]
        print(complete_filelist)

        self.brute_section(self.wordlist["path"], method, follow_redirects)
        self.brute_section(complete_filelist, method, follow_redirects)


    def check(self, component, method, follow_redirects=False):
        #TODO don't follow redirects
        get_result = HTTP_METHODS[method](
            "{protocol}://{domain}/{component}".format(
                protocol=self.protocol,
                domain=self.domain,
                component=component
            ),
            allow_redirects=follow_redirects
        )

        return get_result

    def get_results(self, output_format="human"):

        for result in self.results:
            if result.ok:
                print(result.url)

def main():
    wordlists = ["test.txt"]
    d = Durrduster("nosmo.me")
    d.add_wordlist("path", "test.txt")
    d.add_wordlist("extension", "filetype.txt")
    d.add_wordlist("filename", "filename.txt")

    d.brute(FOLLOW_REDIRECTS)
    #d.get_results()

if __name__ == "__main__":
    main()
