Bronson
========

Bronson is a HTTP brute force path scanning tool. It uses wordlists
and permutations of those lists to discover objects on a target
webserver.

![Awwww yeah](https://i1.wp.com/25.media.tumblr.com/0cd5774d2d0b90ae6446b244bb027952/tumblr_mmb6cfL5NM1r4in5yo1_400.gif)

Support is offered for generation of permutations of filenames, by
using the ```filename``` and ```extension``` lists. All filenames are
combined with all extensions to generate a complete list.

Bronson uses [requests-futures](https://github.com/ross/requests-futures) to very quickly cover a large number of requests in parallel and as a result is quite fast.

Creating an attack
--------

A Bronson attack is started by running the command like so:
```./bronson.py --domain site-to-attack.example.com --config ./config.example.yaml```

Bronson supports configuration via a YAML file - see
```config.example.yaml``` for an example. This file is largely
comprised of definitions of wordlists and related files.

For Bronson to be useful, configure it with more extensive wordlists.
