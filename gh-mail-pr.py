from github3 import login
from github3 import pulls
from github3 import issues
import os
import re
import glob

gh = login('github-login@domain.com', password='password')
me = gh.user()
print me

repo = gh.repository(me, "Linaro\/odp")
print repo

for r in gh.iter_repos():
	print r.full_name
	print r.name
	if r.full_name == "Linaro/odp":
		repo = r
		break

if not repo:
	exit(1)

def my_system(cmd):
	ret = os.system(cmd)
	if ret:
		print "Error: %s" % cmd

def fix_patch(f, hdr, i, tlen):
	fin = open(f, "r+")
	data = fin.read()
	fin.close()

	new_data = re.sub("\[PATCH.*\]", "[%s %d/%d]" % (hdr, i, tlen), data)

	fout = open(f, "w")
	fout.writelines(new_data)
	fout.close()


def fix_headers(hdr):

	print "Fix hdr with hdr %s\n" % hdr
	pfiles = sorted(glob.glob("./to_send-p*.patch"))
	i = 0
	for f in pfiles:
		i = i + 1
		fix_patch(f, hdr, i, len(pfiles))

	return i

def email_patches(edata):
	#print "Email:", edata['patch_url']
	#print "Email:", edata['base_sha']
	my_system("wget -O pr.patch -o /dev/null %s" % edata['patch_url'])
	fin = open("pr.patch","r+")
	fout = open("pr_mod.patch","w")
	data = fin.readlines()
	efrom = ""

	my_system("rm -rf to_send*.patch")

	for l in data:
		if l[0:9] == "Subject: ":
			fout.write("Github-pr-num: %d\n" % edata['number'])
			fout.write(l)
			continue

		#print "line=%s" % l
		if l.rstrip("\n") != "---":
			fout.write(l)
		else:
			fout.write("---\n")
			fout.write("/** Email created from pull request %d (%s)\n" % (edata['number'], edata['head_label']))
			fout.write(" ** %s\n" % edata['url'])
			fout.write(" ** Patch: %s\n" % edata['patch_url'])
			fout.write(" ** Base sha: %s\n" % edata['base_sha'])
			fout.write(" ** Merge commit sha: %s\n" % edata['merge_commit_sha'])
			fout.write(" **/\n")
		if l[0:6] == "From: ":
			efrom = l[6:].rstrip("\n")
	fout.close()
	fin.close()

	my_system("cat pr_mod.patch | formail -ds sh -c 'cat > to_send-p-$FILENO.patch'")

	num = fix_headers(edata['prefix'])

	c = open("to_send-c-0000.patch","w")
	c.write("From %s %s\n" % (edata['base_sha'], "<date>"))
	c.write("From: %s\n" % "Github ODP bot  <odpbot@yandex.ru>")
	c.write("Date: %s\n" % "<date>")

	m = re.search("\[(.*)\](.*)", edata['title'])
	c.write("Subject: [%s 0/%d]%s\n" % (m.group(1), num, m.group(2)))

	c.write("\n")
	c.write(edata['body_text'])
	c.write("\n")
	c.write("\n")

	c.write("----------------github------------------------\n")
	c.write("/** Email created from pull request %d (%s)\n" % (edata['number'], edata['head_label']))
	c.write(" ** %s\n" % edata['url'])
	c.write(" ** Patch: %s\n" % edata['patch_url'])
	c.write(" ** Base sha: %s\n" % edata['base_sha'])
	c.write(" ** Merge commit sha: %s\n" % edata['merge_commit_sha'])
	c.write(" **/\n")
	c.write("----------------/github------------------------\n")
	c.write("\n")

	c.write("----------------checkpatch.pl------------------------\n")
	c.close()
	my_system("perl ./scripts/checkpatch.pl to_send-p-*.patch | grep -v \"Ignored message types\">> to_send-c-0000.patch")
	c = open("to_send-c-0000.patch","a")
	c.write("----------------/checkpatch.pl------------------------\n")
	c.close()

	my_system("rm -rf pr_mod.patch")
	my_system("rm -rf pr.patch")

	options = "--smtp-server=\"smtp.server\" --smtp-ssl --smtp-pass=\"password\" --smtp-encryption=tls --smtp-user=\"odpbot\" --from=\"Github ODP bot  <odpbot@yandex.ru>\""

	my_system("git send-email --confirm=never --to ml-listp@lists.real  --suppress-cc=all %s to_send*.patch" % options)
	#my_system("git send-email --confirm=never --to muvarov@gmail.com --suppress-cc=all %s to_send*.patch" % options)


#for x in  repo.iter_issues():
#	print"----------------", x.number, "--------"
#	print x.pull_request
#	print "Label:"
#	for l in  x.iter_labels():
#		print l
#	print "Comments:"
#	for c in x.iter_comments():
#		print c.body_text
#	x.add_labels("Maxlabel")
#	email_patches(x.pull_request['patch_url'])

for p in repo.iter_pulls():
	edata= {}
	#print p
	#print p.base.sha
	#print p.head.label
	#print p.body
	#print p.body_text
	print "Pull request %d" %  p.number

	edata['url'] = p.html_url
	edata['head_label'] = p.head.label
	edata['number'] = p.number
	edata['base_sha'] = p.base.sha
	edata['patch_url'] = p.patch_url
	edata['merge_commit_sha'] = p.merge_commit_sha
	edata['title'] = p.title
	edata['body_text'] = p.body_text
	edata['branch'] = p.base.ref


	if p.state != "open":
		continue

	m = re.search(r"\[(PATCH.*)\] (.*)", p.title)
	if not m:
		print("no PATCH in head, skipping\n")
		continue

	edata['prefix'] = m.group(1)

	issue = repo.issue(p.number)

	#for c in  p.iter_commits():
	#	print c.sha

	print "Label:"
	skip = 0
	for l in  issue.iter_labels():
		if l.name == "Email_sent":
			print l.name
			#if p.number == 21:
			#	break
			skip = 1
			break
		if l.name == "No_Email_sent":
			print l.name
			skip = 1
			break
	if skip:
		print "skipping sending email for PR %d\n" % p.number
		continue


	#print "Comments:"
	#for c in p.iter_issue_comments():
	#	print c.body_text

	email_patches(edata)
	issue.add_labels("Email_sent")
