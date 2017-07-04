#!/usr/bin/env python3


import argparse
import copy
import random

from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession
import requests
import yaml

from util import HTTP_METHODS, make_session_methods
from wordlist import Wordlist

FOLLOW_REDIRECTS = False
MAX_DEPTH = 3
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; MacOS 7.5.1) You should probably block this UA"
MAX_CONCURRENT = 10

# Session makes use of auth (etc) easier, but also makes detection
# easier if cookies are set
USE_SESSION = True


class Bronson(object):

    def __init__(self, domain, method, protocol="https"):

        self.domain = domain
        self.method = method
        self.protocol = protocol
        self.wordlist = Wordlist()
        self.user_agents = []

        if USE_SESSION:
            self.session = FuturesSession(
                executor=ThreadPoolExecutor(max_workers=MAX_CONCURRENT))
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
        # TODO deduplicate between this function and brute_dirs -
        # there's so much overlap and this is only still here because
        # I'm so so lazy.
        brute_futures = []

        # Brute_iterator could be a list of paths, filenames, mutated paths
        for component in brute_iterator:
            request_path = component
            if prefix and prefix != "/":
                request_path = "%s/%s" % (prefix, component)

            future_obj = self.check(request_path, method, follow_redirects)
            brute_futures.append(future_obj)
        return brute_futures

    def brute_dirs(self, dirlist, method, follow_redirects, prefix=None):
        dir_futures = []
        for check_dir in dirlist:
            check_path = check_dir
            if prefix and prefix != "/":
                check_path = "/".join([prefix, check_dir])

            request_obj = self.check(check_path, method, follow_redirects)
            dir_futures.append(request_obj)
        return dir_futures


    def brute(self, follow_redirects, max_depth, method="GET"):
        """Run a full attack on the domain with which we have been
        configured.

         Brute force a directory and file structure based on the
         wordlists with which we have been configured.

        follow_redirects: A boolean to indicate whether we should follow redirects
        max_depth: an int. how many layers of directory from the root should be scanned
        method: the HTTP method to use when scanning
        """

        """TODO option to make max_depth be obeyed relative to the
        last
        successful dir?

        ie: with max_depth 3, example.com/fail/fail/fail fails out but
        once we hit example.com/fail/success/, keep going until we hit
        example.com/fail/success/fail/fail/fail/. Currently we only
        allow an ABSOLUTE max depth of 3

        """

        complete_filelist = self.wordlist.permute_filenames()

        dir_futures = self.brute_dirs(
            self.wordlist.path() + ["/"], method, follow_redirects
        )

        dir_list = []
        for dir_future in dir_futures:
            dir_request = dir_future.result()
            if dir_request.ok:
                print("Hit for %s" % dir_request.url)
                path = dir_request.url.partition(self.domain)[2]
                dir_list.append(path)

        depth = 1
        found_dirs = copy.copy(dir_list)


        dir_list = []
        while dir_list and depth != max_depth:
            dir_futures = self.brute_dirs(
                self.wordlist.path(), method, follow_redirects, prefix=prefix_dir
            )
            for dir_future in dir_futures:
                dir_request = dir_future.result()
                if dir_request.ok:
                    path = dir_request.url.partition(self.domain)[2]
                    print("Hit for %s" % dir_request.url)
                    dir_list.append(path)
            found_dirs += dir_list
            depth += 1
        found_dirs = list(set(found_dirs))

        print("Finished scanning directories. Dirlist is %s" % str(found_dirs))

        brute_futures = []
        for found_dir in found_dirs:
            brute_futures += self.brute_section(
                complete_filelist, method, follow_redirects, prefix=found_dir)
        for brute_future in brute_futures:
            brute_result = brute_future.result()
            if brute_result.ok:
                print("Hit for %s" % brute_result.url)

    def check(self, component, method, follow_redirects=False):
        #TODO don't follow redirects

        headers = requests.utils.default_headers()
        user_agent = random.choice(self.user_agents if self.user_agents else [DEFAULT_USER_AGENT])
        print("User agent is %s" % user_agent)
        print("Path is %s" % component)

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
        raise NotImplementedError

def main(config):

    d = Bronson(config["domain"], method="GET")
    for wordlist_type, wordlist_list in config["wordlists"].items():
        for wordlist_f in wordlist_list:
            d.wordlist.add_wordlist(wordlist_type, wordlist_f)

    for useragent_f in config["user_agents"]:
        d.add_user_agent(useragent_f)

    d.brute(FOLLOW_REDIRECTS, max_depth=MAX_DEPTH)
    #d.get_results()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Brute force scanning for HTTP objects on a domain')

    parser.add_argument("config", type=str, help="YAML config file defining attack parameters")
    args = parser.parse_args()
    with open(args.config) as config_f:
        config = yaml.load(config_f)

    main(config)
