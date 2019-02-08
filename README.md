# github-scripts
Scripts to maintain GitHub activity.

- gh-checkpatch.py - add status to github pull request for checkpatch.pl and license agreement

- gh-hook-mr.py - merge request hook to rename pull requests

# Usage
- Save service credentials into `.env` file located in user home folder
- Build Docker image
	`docker build -t github-scripts .`
- Run container
	`docker run -t -d -p 80:80 github-scripts`
