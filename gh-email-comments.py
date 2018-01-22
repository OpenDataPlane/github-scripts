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
import pickle
import imaplib
import email
import smtplib
from email.mime.text import MIMEText

configfile = '~/gscripts_config.py'
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

# get Message-Id to reply with correct In-Reply-To
def get_email_id_by_title(title):
	ret_msg_id = None

	imap_login = gcfg.gcfg['imap']['login']
	imap_password = gcfg.gcfg['imap']['pass']

	mail = imaplib.IMAP4_SSL('imap.yandex.ru')
	mail.login(imap_login, imap_password)
	mail.list()

	# Out: list of "folders" aka labels in gmail.
	mail.select("inbox") # connect to inbox.
	mail.select(readonly=1) # Select inbox or default namespace

	# imap truncates subject search
	m = re.search(r'\[(PATCH.*v[0-9]+)\](.*)', title[0:52])
	if not m:
		mail.logout()
		return None

	prefix = m.group(1).lstrip() + " 0/" #look for PATCH v1 0/X
	subject = m.group(2).lstrip()

	(retcode, messages) = mail.uid('search', '(SUBJECT "%s")' % subject)
	for num in messages[0].split():
		typ, data = mail.fetch(num,'(RFC822)')
		msg_str = email.message_from_string(data[0][1])
		m = re.search(prefix,  msg_str['Subject'])
		if not m:
			continue
		ret_msg_id = msg_str['Message-Id']
		break
	mail.logout()
	return ret_msg_id

def smtp_send_comment(pull, rvc, id):
	if rvc.user.name:
		user = "%s(%s)" % (rvc.user.name, rvc.user.login)
	else:
		user = "%s" % (rvc.user.login)

	text = "%s replied on github web page:\n\n" % (user)

	text += "%s\n" % (rvc.path)
	if rvc.position:
		text += "line %s\n" % (rvc.position)
	text += "%s\n" % rvc.diff_hunk
	text += "\n\n"
	text += "Comment:\n"
	text += rvc.body
	text += "\n\n"

	text += "%s\n" % rvc.html_url
	text += "updated_at %s\n" % rvc.updated_at
	msg = MIMEText(text.encode("utf-8"))

	msg['Subject'] = "Re: %s" % pull.title
	msg['From'] =  "Github ODP bot  <odpbot@yandex.ru>"
	msg['To'] = "lng-odp@lists.linaro.org"
	msg['In-Reply-To'] = id
	#msg['To'] = "maxim.uvarov@linaro.org"

	smtp_server = gcfg.gcfg['smtp']['server']
	smtp_login = gcfg.gcfg['smtp']['login']
	smtp_password = gcfg.gcfg['smtp']['pass']

	s = smtplib.SMTP_SSL(smtp_server)
	s.login(smtp_login, smtp_password)
	s.sendmail(msg['From'], msg['To'], msg.as_string())
	s.quit()

def email_new_comment(pull, rvc):
	id = get_email_id_by_title(pull.title)
	smtp_send_comment(pull, rvc, id)

### MAIN

os.system("mkdir -p gh-ec-cache")


for pull in repo.get_pulls():
	try:
		issue = repo.get_issue(pull.number)
	except:
		# timeout ssl http error can happen. Process this pr
		# on next run.
		continue

	pull_cache = {}
	filename = "gh-ec-cache/%d.cache" % pull.number
	try:
		f = open(filename, "rb" );
		pull_cache = pickle.load(f)
		f.close()
	except:
		print "return at 1"
		break

	try:
		for rvc in pull.get_review_comments():
			if rvc.id not in pull_cache:
				email_new_comment(pull, rvc)
				pull_cache[rvc.id] = { rvc.body }
	except:
		print "return at 2"
		break

	f = open(filename, 'w')
	pickle.dump(pull_cache, f)
	f.close()
