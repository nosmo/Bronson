#!/usr/bin/env python3

import copy
import random

import requests
import yaml

from util import HTTP_METHODS, make_session_methods
from wordlist import Wordlist

FOLLOW_REDIRECTS = False
MAX_DEPTH = 3
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; MacOS 7.5.1) You should probably block this UA"

# Session makes use of auth (etc) easier, but also makes detection
# easier if cookies are set
USE_SESSION = True

CONFIG_DICT = {
    "domain": "nosmo.me",
    "wordlists": {
        "path": ["path.txt"],
        "extension": ["filetype.txt"],
        "filename": ["filename.txt"]
    },
    "user_agents": ["useragents.txt"],
}


class Durrduster(object):

    def __init__(self, domain, method, protocol="https"):

        self.domain = domain
        self.method = method
        self.protocol = protocol
        self.wordlist = Wordlist()
        self.user_agents = []

        if USE_SESSION:
            self.session = requests.Session()
            self.methods = make_session_methods(self.session)
        else:
            self.methods = HTTP_METHODS

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

        get_result = self.methods[method](
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
