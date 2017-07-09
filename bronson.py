#!/usr/bin/env python3


import argparse
import copy
import json
import random

from concurrent.futures import ThreadPoolExecutor
from requests_futures.sessions import FuturesSession
import requests
import yaml

from const import OUTPUT_TYPES, DEFAULT_USER_AGENT
from util import HTTP_METHODS, make_session_methods
from wordlist import Wordlist

FOLLOW_REDIRECTS = False
MAX_CONCURRENT = 10

# TODO move this to a custom logger
DEBUG = False


class Bronson(object):

    def __init__(self, domain, method, protocol="https"):

        #lol too many attributes
        self.domain = domain
        self.method = method
        self.protocol = protocol
        self.wordlist = Wordlist()
        self.user_agents = []

        #TODO add function to scrub session data
        self.session = FuturesSession(
            executor=ThreadPoolExecutor(max_workers=MAX_CONCURRENT))
        self.methods = make_session_methods(self.session)

        self.results = []
        self.proxies = {"http": [], "https": []}
        self.blacklist = []
        # Used only for tracking cookies - will be removed in future
        self.cookies = {}

    def add_user_agent(self, useragent_path):
        """add a file full of user agents to use

         The loading of more than one user agent implies the use of
        random user agents.
        """

        with open(useragent_path) as wordlist_f:
            for useragent in wordlist_f.read().split("\n"):
                useragent = useragent.strip()
                if useragent:
                    self.user_agents.append(useragent)

    def add_proxy_config(self, proxy_dict):
        for proxyname, proxydetails in proxy_dict.items():
            if proxydetails["type"] in self.proxies.keys():
                self.proxies[proxydetails["type"]].append(proxydetails["connect"])
            elif proxydetails["type"] == "any":
                self.proxies["http"].append(proxydetails["connect"])
                self.proxies["https"].append(proxydetails["connect"])

        print("Proxies configured %s" % str(self.proxies))

    def add_cookie(self, cookie_tuple):
        """Set a cookie when scanning.

        cookie_tuple: a tuple of the format (key, value)
        """
        self.cookies[cookie_tuple[0]] = cookie_tuple[1]
        self.session.cookies.set(cookie_tuple[0], cookie_tuple[1])

    def add_blacklist(self, blacklist):
        self.blacklist = blacklist

    def brute_section(self, brute_iterator, follow_redirects, prefix=None):
        brute_futures = []

        # Brute_iterator could be a list of paths, filenames, mutated paths
        for component in brute_iterator:
            request_path = component
            if prefix:
                format_string = "%s%s"
                if not prefix.endswith("/") and component != "/":
                    format_string = "%s/%s"
                request_path = format_string % (prefix, component)

                if request_path in self.blacklist:
                    if DEBUG:
                        print("Skipping %s due to blacklist" % request_path)
                    continue

            future_obj = self.check(request_path, follow_redirects)
            brute_futures.append(future_obj)
        return brute_futures

    def brute(self, follow_redirects, max_depth):
        """Run a full attack on the domain with which we have been
        configured.

         Brute force a directory and file structure based on the
         wordlists with which we have been configured.

        follow_redirects: A boolean to indicate whether we should follow redirects
        max_depth: an int. how many layers of directory from the root should be scanned
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

        dir_futures = self.brute_section(
            self.wordlist.path() + [""], follow_redirects
        )

        dir_list = []
        for dir_future in dir_futures:
            dir_request = dir_future.result()
            if dir_request.ok:
                if DEBUG:
                    print("Dir Hit for %s" % dir_request.url)
                path = dir_request.url.partition(self.domain)[2]
                dir_list.append(path)

        depth = 1
        found_dirs = copy.copy(dir_list)

        dir_list = []
        while dir_list and depth != max_depth:
            dir_futures = self.brute_section(
                self.wordlist.path(), self.method, follow_redirects, prefix=prefix_dir
            )
            for dir_future in dir_futures:
                dir_request = dir_future.result()
                if dir_request.ok:
                    path = dir_request.url.partition(self.domain)[2]
                    if DEBUG:
                        print("List Hit for %s" % dir_request.url)
                    dir_list.append(path)
            found_dirs += dir_list
            depth += 1
        found_dirs = list(set(found_dirs))

        if DEBUG:
            print("Finished scanning directories. Dirlist is %s" % str(found_dirs))

        brute_futures = []
        for found_dir in found_dirs:
            brute_futures += self.brute_section(
                complete_filelist, follow_redirects, prefix=found_dir)

        found_files = []
        for brute_future in brute_futures:
            brute_result = brute_future.result()
            if brute_result.ok:
                if DEBUG:
                    print("Hit for %s" % brute_result.url)

                path = brute_result.url.partition(self.domain)[2]
                found_files.append(path)

        self.found_dirs = found_dirs
        self.found_files = found_files

    def check(self, component, follow_redirects=False):
        #TODO don't follow redirects

        headers = requests.utils.default_headers()

        # Select a random user agent or use the default if not configured
        user_agent = random.choice(self.user_agents if self.user_agents else [DEFAULT_USER_AGENT])

        # Select a random proxy if configured with a proxy list
        proxy = {self.protocol: None}
        if [ i for i in self.proxies.values() if i ]:
            proxy = {self.protocol: "%s://%s" % (self.protocol,
                                                 random.choice(self.proxies[self.protocol]))}

        method = self.method
        if self.method == "mix":
            method = random.choice(["GET", "HEAD"])

        if DEBUG:
            print("User agent is %s" % user_agent)
            print("Path is %s" % component)
            print("Proxy is %s" % proxy[self.protocol])

        ua_header = {"User-Agent": user_agent}
        headers.update(ua_header)

        get_result = self.methods[method](
            "{protocol}://{domain}/{component}".format(
                protocol=self.protocol,
                domain=self.domain,
                component=component,
            ),
            proxies=proxy,
            headers=headers,
            allow_redirects=follow_redirects
        )

        return get_result

    def get_results(self, output_format):
        if output_format in ["csv"]:
            raise NotImplementedError

        if output_format == "text":
            for result in self.found_dirs:
                print("Dir: %s" % result)
            for result in self.found_files:
                print("File: %s" % result)
        elif output_format == "json":
            print(
                json.dumps({"dirs": self.found_dirs,
                            "files": self.found_files})
            )

def main(args, config):

    d = Bronson(args.domain, method=config["discovery_method"], protocol=args.protocol)
    for wordlist_type, wordlist_list in config["wordlists"].items():
        for wordlist_f in wordlist_list:
            d.wordlist.add_wordlist(wordlist_type, wordlist_f)

    for useragent_f in config["user_agents"]:
        d.add_user_agent(useragent_f)

    if "proxies" in config and config["proxies"]:
        d.add_proxy_config(config["proxies"])

    if "blacklist" in config and config["blacklist"]:
        d.add_blacklist(config["blacklist"])

    for cookie in args.cookies:
        d.add_cookie(cookie.split(":"))

    d.brute(FOLLOW_REDIRECTS, max_depth=config["max_depth"])
    d.get_results(args.output)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Brute force scanning for HTTP objects on a domain')

    parser.add_argument("--config", type=str, help="YAML config file defining attack parameters",
                        default="bronson.yaml")
    parser.add_argument("--domain", type=str, help="Domain to attack", required=True)
    parser.add_argument("--protocol", type=str, help="HTTP protocol to speak", default="https",
                        choices=["http", "https"])
    parser.add_argument("--output", "-o", dest="output", action="store", default="text",
                        choices=OUTPUT_TYPES, help="Output format")
    parser.add_argument("--cookie", "-c", dest="cookies", action="store", nargs="+",
                        help="A key:value cookie.", default=[])

    args = parser.parse_args()

    with open(args.config) as config_f:
        # TODO allow the config file to override a defaults file
        # TODO allow the command line arguments serve as a way of overriding config
        config = yaml.load(config_f)

    main(args, config)
