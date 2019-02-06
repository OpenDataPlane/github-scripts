#!/usr/bin/python
# encoding=utf8

#
# Cron script to validate patches in open pull requests.
# 1. Validation skipped if "checkpatch" label is set.
# 2. Run both checkpatch.pl and odp agreement checks.
# Result is status on odp pull request github web  page and
# label "checkpatch" set.

from github3 import login
import os
import re
import glob
import sys
reload(sys)  
sys.setdefaultencoding('utf8')

configfile = '~/gscripts_config.py'
sys.path.append(os.path.dirname(os.path.expanduser(configfile)))
import gscripts_config as gcfg

gh_login = gcfg.gcfg['gh']['login']
gh_password = gcfg.gcfg['gh']['pass']

gh = login(gh_login, gh_password)

def my_system(cmd):
        ret = os.system(cmd)
        if ret:
                print "Error: %s" % cmd
	return ret

def do_checkpatch(patch):
	f = open("1.patch", "w")
	f.write(patch)
	f.close()

	check_patch_ret = my_system("perl ./scripts/checkpatch.pl 1.patch > /dev/null")
	#print "CHECKPATCH STATUS: %d" % check_patch_ret

	agreement_cmd = "./odp-agreement/odp_check_contr.sh 1.patch ./odp-agreement/Iagree.hash ./odp-agreement/Corplist.hash > /dev/null"
	agreement_ret = my_system(agreement_cmd)
	#print "AGREEMENT STATUS: %d" % agreement_ret

	my_system("rm 1.patch")
	check_patch_ret = 0
	agreement_ret = 0
	return [check_patch_ret, agreement_ret]

my_system("git clone https://git.linaro.org/people/maxim.uvarov/odp-agreement.git")
my_system("cd odp-agreement && git pull")

repo = gh.repository("OpenDataPlane", "odp")
my_issues = repo.issues(state="open")

for my_issue in my_issues:
	skip = 0
	for l in my_issue.labels():
		if l.name == "checkpatch":
			skip = 1
			break
	if skip:
		continue

	pr = my_issue.pull_request()
	if not pr:
		continue
	check_patch_ret = 0
	agreement_ret = 0

	for c in pr.commits():
		(cp_ret, a_ret) = do_checkpatch(c.patch())
		if cp_ret:
			check_patch_ret = 1
		if a_ret:
			agreement_ret = 1


	version = 0
	for m in re.finditer(r'\[PATCH.*v([0-9]+)\]', my_issue.title):
		version = int(m.group(1))

	text = "<pre>v%d checks:\n" % version


	if check_patch_ret == 0:
		text += "checkpatch.pl - OK\n"
	else:
		text += "checkpatch.pl - FAIL\n"

	if agreement_ret == 0:
		text += "ODP License Agreement - PASSED\n"
	else:
		text += "ODP License Agreement - FAILED\n"

	text +="</pre>\n"
	my_issue.create_comment(text)

	label = repo.label("checkpatch")
	if not label:
		label = repo.create_label("checkpatch",  "0000ff")

	my_issue.add_labels("checkpatch")
