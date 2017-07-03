#!/usr/bin/env python3

import requests

HTTP_METHODS = {
    "GET": requests.get,
    "POST": requests.post,
    "HEAD": requests.head
}

def make_session_methods(session_obj):
    return {
        "GET": session_obj.get,
        "POST": session_obj.post,
        "HEAD": session_obj.head
    }
