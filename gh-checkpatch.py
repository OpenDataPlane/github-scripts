#!/usr/bin/python
#
# Cron script to validate patches in open pull requests.
# 1. Validation skipped if "checkpatch" label is set.
# 2. Run both checkpatch.pl and odp agreement checks.
# Result is status on odp pull request github web  page and
# label "checkpatch" set.

from github import Github
import github
import os
import re
import glob
import sys

configfile = '/home/muvarov/gscripts_config.py'
sys.path.append(os.path.dirname(os.path.expanduser(configfile)))
import gscripts_config as gcfg

gh_login = gcfg.gcfg['gh']['login']
gh_password = gcfg.gcfg['gh']['pass']

g = Github(gh_login, password=gh_password)

for repo in g.get_user().get_repos():
	if repo.full_name == "Linaro/odp":
		break
if not repo:
	exit(1)

def my_system(cmd):
        ret = os.system(cmd)
        if ret:
                print "Error: %s" % cmd
	return ret

def do_checkpatch(sha):
	patch = "%s.patch" % sha
	my_system("rm %s 2>/dev/null" % patch)

	ret = my_system("wget https://github.com/Linaro/odp/commit/%s > /dev/null" % patch)
	if ret:
		print "Download %s failed, abort!\n" % patch
		sys.exit(1)

	check_patch_ret = my_system("perl ./scripts/checkpatch.pl %s > /dev/null" % patch)
	print "CHECKPATCH STATUS: %d" % check_patch_ret

	agreement_cmd = "./odp-agreement/odp_check_contr.sh %s ./odp-agreement/Iagree.hash ./odp-agreement/Corplist.hash > /dev/null" % patch
	agreement_ret = my_system(agreement_cmd)
	print "AGREEMENT STATUS: %d" % agreement_ret

	my_system("rm %s" % patch)
	return [check_patch_ret, agreement_ret]

my_system("git clone https://git.linaro.org/people/maxim.uvarov/odp-agreement.git")

for pull in repo.get_pulls():
	issue = repo.get_issue(pull.number)
	skip = 0
	for l in issue.get_labels():
		if l.name == "checkpatch":
			skip = 1
			break
	if skip:
		continue

	for c in pull.get_commits():
		(check_patch_ret, agreement_ret) = do_checkpatch(c.commit.sha)
		if check_patch_ret == 0:
			c.create_status(state="success",
					target_url="http://none",
					description="checkpatch.pl", context="checkpatch success")
		else:
			c.create_status(state="failure",
					target_url="http://none",
					description="checkpatch.pl", context="checkpatch failed")

		if agreement_ret == 0:
			c.create_status(state="success",
					target_url="http://none",
					description="ODP License Agreement",
					context="ODP License Agreement")
		else:
			c.create_status(state="failure", 
					target_url="https://www.opendataplane.org/contributor/individual/", 
					description="ODP License Agreement",
					context="ODP License Agreement")

	label = repo.get_label("checkpatch")
	if not label:
		label = repo.create_label("checkpatch",  "0000ff")
	
	issue.add_to_labels(label)
