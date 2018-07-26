#!/usr/bin/python
# encoding=utf8

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
import os
import sys
reload(sys)  
sys.setdefaultencoding('utf8')

configfile = '~/gscripts_config.py'
sys.path.append(os.path.dirname(os.path.expanduser(configfile)))
import gscripts_config as gcfg

blogin = gcfg.gcfg['bugz']['login']
bpassword = gcfg.gcfg['bugz']['pass']
print ("%s" % blogin)

qin = sys.stdin.read()
#f = open('python_%s.dump' % time.time(), 'w')
#pickle.dump(qin, f)
#f.close()

#fname = "test.dump"
#qin  = pickle.load( open(fname, "rb" ) )

use_refs=['refs/heads/master']

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
	bzapi.login(blogin, bpassword)

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

found = 0
for ref in use_refs:
	if ref == js["ref"]:
		found = 1
		break;
if not found:
	print("<h1>ref %s is not posted to bugs</h1>" % js["ref"])
	print("</body></html>")
	sys.exit(0)

for c in js["commits"]:
	bugset = msg_has_bug(c["message"])
	for bugnum in bugset:
		bug = bzapi.getbug(bugnum)
		bug_msg = "%s\n%s\n%s\n%s %s\n%s\n" % (c["url"],
					js["ref"],
		  			c["timestamp"],
		  			c["author"]["name"], c["author"]["email"],
		  			c["message"])

		update = bzapi.build_update(comment=bug_msg)
		bzapi.update_bugs([bug.id], update)
		print("Posted message to bug %s" % bugnum)

print("<h1>all ok!</h1>")
print("</body></html>")
