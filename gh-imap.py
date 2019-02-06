#!/usr/bin/env python3

import imaplib
import email
import re
import sys
import os

from github3 import login
from github3 import pulls
from github3 import issues

configfile = '~/gscripts_config.py'
sys.path.append(os.path.dirname(os.path.expanduser(configfile)))
import gscripts_config as gcfg

imap_login = gcfg.gcfg['imap']['login']
imap_password = gcfg.gcfg['imap']['pass']

mail = imaplib.IMAP4_SSL('imap.yandex.ru')
mail.login(imap_login, imap_password)
mail.list()
# Out: list of "folders" aka labels in gmail.
mail.select("inbox") # connect to inbox.

pull_rq_db = {}

gh_login = gcfg.gcfg['gh']['login']
gh_password = gcfg.gcfg['gh']['pass']

gh = login(gh_login, password=gh_password)
me = gh.user()
print(me)

repo = gh.repository(me, "OpenDataPlane\/odp")
print(repo)

for r in gh.iter_repos():
	print(r.full_name)
	print(r.name)
	if r.full_name == "OpenDataPlane/odp":
		repo = r
		break

if not repo:
	exit(1)

print("Using github repo %s" % r.full_name)

# get new messages

def is_patch(msg):
	m = re.search("\nSubject.*Re:.*PATCH.*\n", msg)
	if m:
		#print(m.group(0))
		return 1
	return 0

def get_find_pull_req(msg):
	m = re.search(r'https://github.com/OpenDataPlane/odp/pull/.*\n', msg)
	if m:
		return m.group(0)[35:]
	return ""

def process_email(i, efrom, msg, pr):
	#f = open("eml/em-%d.dat" % i, "w")
	#f.write(msg)
	#f.close()

	#for ic in pr.iter_issue_comments():
	#	print(ic)
	issue = repo.issue(pr.number)

	pre_msg = "<pre>From: %s\n %s </pre>" % (efrom, msg)
	issue.create_comment(pre_msg)

	return

def get_all_prs():
	print("reading cache")
	mail.select(readonly=1) # Select inbox or default namespace
	(retcode, messages) = mail.search(None, '(SEEN)')

	for num in messages[0].split():
		typ, data = mail.fetch(num,'(RFC822)')
		msg_str = email.message_from_string(data[0][1])
		msg = str(msg_str)
		pr = get_find_pull_req(msg)
		if pr != "":
			pull_rq_db[msg_str['Message-ID']] = pr
			#print(pr,)
			#sys.stdout.flush()
		print("%d/%d\n" % (num, len(messages[0].split())))
	print("reading cache done")
	return


get_all_prs()

mail.select(readonly=0) # Select inbox or default namespace
(retcode, messages) = mail.search(None, '(UNSEEN)')
#(retcode, messages) = mail.search(None, '(SEEN)')

print(retcode)
print(messages)

if retcode != 'OK':
	exit (1)

i = 0
for num in messages[0].split():
	typ, data = mail.fetch(num,'(RFC822)')

	msg_str = email.message_from_string(data[0][1])
	msg = str(msg_str)

	if not is_patch(msg):
		continue

	if msg_str.is_multipart():
		continue

	#print("Message-ID=", msg_str['Message-ID'])
	#print("In-Reply-To=", msg_str['In-Reply-To'])
	#print("Pull request =", pr)

	if not 'In-Reply-To' in msg_str:
		print("x",)
		sys.stdout.flush()
		i = i + 1
		continue

	pr = get_find_pull_req(msg)
	if pr != "":
		pull_rq_db[msg_str['Message-ID']] = pr
	else:
		if msg_str['In-Reply-To'] in pull_rq_db:
			pr = pull_rq_db[msg_str['In-Reply-To']]
			print("Found pr from in replay")
	if pr == "":
		print(".",)
		sys.stdout.flush()
		i = i + 1
		continue

	efrom = msg_str['From']
	body = msg_str.get_payload(decode=True)

	print("Message-ID=", msg_str['Message-ID'])
	print("In-Reply-To=", msg_str['In-Reply-To'])
	print("Pull request =", pr)

	mail.store(num, '+FLAGS', '\\SEEN')
	process_email(i, efrom, body, repo.pull_request(pr))

	#f = open("eml/em-%d.eml" % i, "w")
	#f.write(msg)
	#f.close()

	i = i + 1

