#!/usr/bin/python

# bugzilla github push web hook
#
# Scripts updates bugzilla bug with merged commit message

from __future__ import print_function
import pprint
import bugzilla


import cgi
import pickle
import sys
import time
import json
from StringIO import StringIO
import sys, urllib
from cgi import parse_qs, escape
import re

qin = sys.stdin.read()
f = open('python_%s.dump' % time.time(), 'w')
pickle.dump(qin, f)
f.close()

#fname = "python_1492447091.72.dump"
#qin  = pickle.load( open(fname, "rb" ) )

def msg_has_bug(msg):
	buglist = set()
	print("%s\n" % msg)
	for m in re.finditer('https://bugs\.linaro\.org/show_bug\.cgi\?id=([0-9]+)', msg):
                buglist.add(m.group(1))

	for m in re.finditer(r'[bB]ug #([0-9]+)', msg):
                buglist.add(m.group(1))

	for m in re.finditer(r'[bB]ug ([0-9]+)', msg):
                buglist.add(m.group(1))

	for m in re.finditer(r'[bB]ug: ([0-9]+)', msg):
                buglist.add(m.group(1))

	for m in re.finditer(r'[Ff]ixes: ([0-9]+)', msg):
                buglist.add(m.group(1))

	print("%s\n" % str(buglist))
        return buglist

URL = "https://bugs.linaro.org"

bzapi = bugzilla.Bugzilla(URL)
if not bzapi.logged_in:
    bzapi.login("login@linaro.org", "password")

print("Content-type: text/html\n")
print("""<!DOCTYPE HTML>
        <html>
        <head>
            <meta charset="utf-8">
            <title>some title</title>
        </head>
        <body>""")

io = StringIO(qin)
js = json.load(io)

for c in js["commits"]:
	bugset = msg_has_bug(c["message"])
	for bugnum in bugset:
		bug = bzapi.getbug(bugnum)
		bug_msg = "%s\n%s\n%s %s\n%s\n" % (c["url"],
		  			c["timestamp"],
		  			c["author"]["name"], c["author"]["email"],
		  			c["message"])

		update = bzapi.build_update(comment=bug_msg)
		bzapi.update_bugs([bug.id], update)
		print("Posted message to bug %s" % bugnum)

print("<h1>all ok!</h1>")
print("</body></html>")
