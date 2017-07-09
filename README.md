Bronson
========

Bronson is a HTTP brute force path scanning tool. It uses wordlists
and permutations of those lists to discover objects on a target
webserver with a variety of measures to hamper blocking or detection..

![Awwww yeah](https://i1.wp.com/25.media.tumblr.com/0cd5774d2d0b90ae6446b244bb027952/tumblr_mmb6cfL5NM1r4in5yo1_400.gif)

Support is offered for generation of permutations of filenames, by
using the ```filename``` and ```extension``` lists. All filenames are
combined with all extensions to generate a complete list.

Bronson uses [requests-futures](https://github.com/ross/requests-futures) to very quickly cover a large number of requests in parallel and as a result is quite fast.

Creating an attack
--------

A Bronson attack is started by running the command like so:
```./bronson.py --domain site-to-attack.example.com --config ./config.example.yaml```

Configuration
--------
> ⚠️ For Bronson to be useful, configure it with more extensive wordlists than the ones provided. ⚠️

Bronson supports configuration via a YAML file - see
```config.example.yaml``` for an example. This file is largely
comprised of definitions of wordlists and related files.

Files will be scanned for based on the permutations of the
```filename``` and ```extension``` lists - for example, a filename
list of ```["test", "lol", "derp"]``` and an extension list of
```["txt", "html"]``` will result in a file list of
```["test.txt", "test.html", "lol.txt", "lol.html", "derp.txt", "derp.html"]```.

#### User agents
Multiple user agents can be configured via the ```user_agents```
stanza which allows a list of agents. A random user agent will be
chosen on a per-request basis by default. If no user agents are
configured, a very obvious user agent will be used as an alternative.

#### Proxies
In the same fashion as user agents, proxies can be configued to be randomly used - if
multiple proxies are included in the ```proxies``` key in the
configuration file, one proxy will be randomly selected per
request. If this section is empty or absent, no proxy will be
used. Ensure that if using proxies that your selection of proxies
corresponds to that of the site you are scanning - if no appropriate
proxy is available, the proxy will simply be bypassed.

#### HTTP methods
By default the HTTP method used for file discovery is a GET. A HEAD
can be also used, or the special method "mix" may be used for the
```discovery_method``` config option which will randomly choose
between the two. POST is also available for use but will result in
strange results in most cases.

#### Cookies
Cookes can be passed on a per-attack basis via the ```--cookie```
switch. This can be provided multiple times to add multiple cookies.

#### Blacklist
If a path is to be skipped (sensitive path, very large file etc),
config.yaml accepts a list of files to ignore under the
```blacklist``` heading. Currently only full paths are supported.

Output
--------
Currently JSON and plaintext are supported for output (via the
```--output``` command line switch), with plaintext being the default.

Dependencies
-------
Bronson relies on ```requests```, ```requests-futures``` and other
libraries. The dependencies can be installed in a virtualenv by
running ```make virtualenv_run``` and the virtualenv can then be
activated by running ```source virtualenv_run/bin/activate```.

Bronson requires python3.
