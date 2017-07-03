#!/usr/bin/env python3

import copy
import random

import requests
import yaml

from util import HTTP_METHODS

FOLLOW_REDIRECTS = False
MAX_DEPTH = 3
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; MacOS 7.5.1) You should probably block this UA"

CONFIG_DICT = {
    "domain": "nosmo.me",
    "wordlists": {
        "path": ["path.txt"],
        "extension": ["filetype.txt"],
        "filename": ["filename.txt"]
    },
    "user_agents": ["useragents.txt"],
}

class Wordlist(object):

    def __init__(self):

        self.wordlist = {
            "path": [],
            "filename": [],
            "extension": [],
        }

    def path(self):
        return self.wordlist["path"]

    def filename(self):
        return self.wordlist["filename"]

    def extension(self):
        return self.wordlist["extension"]

    def add_wordlist(self, list_type, filename):
        if list_type not in self.wordlist.keys():
            raise IndexError("%s is not a valid wordlist type - valid types are %s" % (
                list_type,
                self.wordlist.keys()))

        with open(filename) as wordlist_f:
            self.wordlist[list_type] += [ i.strip() for i in wordlist_f.read().split("\n") if i ]
            self.wordlist[list_type] = list(set(self.wordlist[list_type]))
            print(self.wordlist)

    def permute_filenames(self):
        return [ "%s.%s" % (pre, post) for pre in self.wordlist["filename"] \
                 for post in self.wordlist["extension"] ]

class Durrduster(object):

    def __init__(self, domain, method, protocol="https"):

        self.domain = domain
        self.method = method
        self.protocol = protocol
        self.wordlist = Wordlist()
        self.user_agents = []

    def add_user_agent(self, useragent_path):
        """add a file full of user agents to use

         The loading of more than one user agent implies the use of
        random user agents.
        """

        with open(useragent_path) as wordlist_f:
            for useragent in wordlist_f.read().split("\n"):
                if useragent:
                    self.user_agents.append(useragent)

    def brute_section(self, brute_iterator, method, follow_redirects, prefix=None):
        # Brute_iterator could be a list of paths, filenames, mutated paths
        for component in brute_iterator:
            request_path = component
            if prefix and prefix != "/":
                request_path = "%s/%s" % (prefix, component)

            print("request path is %s" % request_path)
            request_obj = self.check(request_path, method, follow_redirects)
            if request_obj.ok:
                print("Hit for %s" % request_obj.url)
                print(request_obj.status_code)

    def brute_dirs(self, dirlist, method, follow_redirects, prefix=None):
        dir_hits = []
        for check_dir in dirlist:
            check_path = check_dir
            if prefix and prefix != "/":
                check_path = "/".join([prefix, check_dir])

            request_obj = self.check(check_path, method, follow_redirects)
            if request_obj.ok:
                print("Hit for %s" % request_obj.url)
                print(request_obj.status_code)
                dir_hits.append(check_path)
        return dir_hits


    def brute(self, follow_redirects, max_depth, method="GET"):

        complete_filelist = self.wordlist.permute_filenames()

        dir_list = self.brute_dirs(
            self.wordlist.path() + ["/"], method, follow_redirects)
        depth = 1
        found_dirs = copy.copy(dir_list)

        while dir_list and depth != max_depth:
            for prefix_dir in dir_list:
                print("Attempting %s" %  prefix_dir)
                dir_list = self.brute_dirs(
                    self.wordlist.path(), method, follow_redirects, prefix=prefix_dir
                )
                found_dirs += dir_list
            depth +=1
        found_dirs = list(set(found_dirs))

        print("Finished scanning directories. Dirlist is %s" % str(found_dirs))

        for found_dir in found_dirs:
            self.brute_section(complete_filelist, method, follow_redirects, prefix=found_dir)


    def check(self, component, method, follow_redirects=False):
        #TODO don't follow redirects

        headers = requests.utils.default_headers()
        user_agent = random.choice(self.user_agents if self.user_agents else [DEFAULT_USER_AGENT])
        print("User agent is %s" % user_agent)

        ua_header = {"User-Agent": user_agent}
        headers.update(ua_header)

        get_result = HTTP_METHODS[method](
            "{protocol}://{domain}/{component}".format(
                protocol=self.protocol,
                domain=self.domain,
                component=component,
            ),
            headers=headers,
            allow_redirects=follow_redirects
        )

        return get_result

    def get_results(self, output_format="human"):
        raise NotImplemented

def main(config):

    d = Durrduster(config["domain"], method="GET")
    for wordlist_type, wordlist_list in config["wordlists"].items():
        for wordlist_f in wordlist_list:
            d.wordlist.add_wordlist(wordlist_type, wordlist_f)

    for useragent_f in config["user_agents"]:
        d.add_user_agent(useragent_f)

    d.brute(FOLLOW_REDIRECTS, max_depth=MAX_DEPTH)
    #d.get_results()

if __name__ == "__main__":
    main(CONFIG_DICT)
