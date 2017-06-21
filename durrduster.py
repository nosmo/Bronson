#!/usr/bin/env python3

import requests

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

    def __init__(self, domain, wordlists, protocol="https"):

        self.domain = domain
        self.protocol = protocol
        self.results = BruteResults()

        self.wordlist = []
        for wordlist_name in wordlists:
            with open(wordlist_name) as wordlist_f:
                self.wordlist += [ i.strip() for i in wordlist_f.read().split("\n") if i ]

    def brute(self, follow_redirects):
        path = "/"
        for word in self.wordlist:
            request_obj = self.check(path, word, follow_redirects)
            result = self.results.add_result(request_obj)
            if result:
                print("Hit for %s" % request_obj.url)


    def check(self, path, word, follow_redirects=False):
        #TODO follow redirects
        get_result = requests.get("{protocol}://{domain}/{path}{word}".format(
            protocol=self.protocol,
            domain=self.domain,
            path=path,
            word=word)
        )

        return get_result

    def get_results(self, output_format="human"):

        for result in self.results:
            if result.ok:
                print(result.url)

def main():
    wordlists = ["test.txt"]
    d = Durrduster("nosmo.me", wordlists)
    d.brute(False)
    #d.get_results()

if __name__ == "__main__":
    main()
