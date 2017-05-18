#!/usr/bin/python

# github pull request update script
#
# Script changes patch version and remove label Email_sent
# Note: version changed only on pull request update event.

import cgi
import pickle
import sys
import time
import json
from StringIO import StringIO
import sys, urllib
from cgi import parse_qs, escape
import re

from github3 import login
from github3 import pulls
from github3 import issues
import os


qin = sys.stdin.read()
#f = open('mr_%s.dump' % time.time(), 'w')
#pickle.dump(qin, f)
#f.close()

#fname = "mr_1493307805.62.dump"
#qin  = pickle.load( open(fname, "rb" ) )

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

gh = login('login-github@domain.com', password='password')
me = gh.user()
print me

repo = 0
for r in gh.iter_repos():
	print r.full_name
	if r.full_name == "Linaro/odp":
	#if r.full_name == "muvarov/odp":
		repo = r
		break

if not repo:
	print "Repo not found"
	sys.exit(1)

#for key, value in js['pull_request'].iteritems() :
#   print "\n\n\n\n----------------"
#    print key
#    print value

action = js['action']
if action == "synchronize" or action == "opened":
	print("<h1>action is %s, process</h1>" % action)
else:
	print("<h1>action is %s, do nothing</h1>" % action)
	print("</body></html>")
	sys.exit(0)

pr_num  = js['pull_request']['number']
pr = repo.pull_request(pr_num)
issue =  repo.issue(pr_num)


branch  = js['pull_request']['base']['ref']
print "branch = %s\n" % branch

title = issue.title

version = 0
for m in re.finditer(r'PATCH.*v([0-9]+)', title):
	version = int(m.group(1))

version += 1

m = re.search(r"\[PATCH.*\] (.*)", title)
if m:
	title = m.group(1)

if branch == "api-next":
	issue.edit(title="[PATCH API-NEXT v%d] %s" % (version, title))
elif branch == "cloud-dev":
	issue.edit(title="[PATCH CLOUD-DEV v%d] %s" % (version, title))
else:
	issue.edit(title="[PATCH v%d] %s" % (version, title))
print issue.title

commits = js['pull_request']['commits']
if commits > 20:
	issue.add_labels("No_Email_sent")
else:
	# return code does not reflect if event was actually
	# removed
	issue.remove_label("Email_sent")

print "body_text %s\n" % issue.body_text


print("<h1>all ok!</h1>")
print("</body></html>")
