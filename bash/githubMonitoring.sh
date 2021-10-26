#!/bin/bash
# Script to monitor changes in a Github organization's list of repositories and members
# Run in cron:
# 0 8 * * * ./home/$HOME/github-monitoring.sh

#Traceback on Error and Exit come from https://docwhat.org/tracebacks-in-bash/
set -eu

_showed_traceback=f

traceback() {
  # Hide the traceback() call.
  local -i start=$(( ${1:-0} + 1 ))
  local -i end=${#BASH_SOURCE[@]}
  local -i i=0
  local -i j=0

  echo "Traceback (last called is first):" 1>&2
  for ((i=${start}; i < ${end}; i++)); do
    j=$(( $i - 1 ))
    local function="${FUNCNAME[$i]}"
    local file="${BASH_SOURCE[$i]}"
    local line="${BASH_LINENO[$j]}"
    echo "     ${function}() in ${file}:${line}" 1>&2
  done
}

on_error() {
  local _ec="$?"
  local _cmd="${BASH_COMMAND:-unknown}"
  traceback 1
  _showed_traceback=t
  echo "The command ${_cmd} exited with exit code ${_ec}." 1>&2
}
trap on_error ERR

on_exit() {
  local _ec="$?"
  if [[ $_ec != 0 && "${_showed_traceback}" != t ]]; then
    traceback 1
  fi
}
trap on_exit EXIT

# Setup
NOTIFY_EMAIL="[INSERT EMAIL ADDRESS HERE]"
ORG_NAME="[INSERT ORGANISATION NAME HERE]"
RESULT="100"

# List of repositories
ALL_REPOS="/tmp/all-repos.list"
PRIVATE_REPOS="/tmp/private-repos.list"
PUBLIC_REPOS="/tmp/public-repos.list"

# Members
ADMIN_MEMBERS="/tmp/admin-members.list"
REGULAR_MEMBERS="/tmp/regular-members.list"

# GitHub API pagination support
function repo_list {
    LAST_PAGE=$(curl -s -I -u $GITHUB_USERNAME:$GITHUB_TOKEN $1$2"&page=1" | grep '^Link:' | sed -e 's/^Link:.*page=//g' -e 's/>.*$//g')

    if [ -z "$LAST_PAGE" ]; then
      REPOS=$(curl -s -H "Accept: application/vnd.github.v3+json" -u $GITHUB_USERNAME:$GITHUB_TOKEN $1$2"&page=1")
      echo "$REPOS"
    else
        for p in `seq 1 $LAST_PAGE`; do
            REPOS=$(curl -s -H "Accept: application/vnd.github.v3+json" -u $GITHUB_USERNAME:$GITHUB_TOKEN $1$2"&page=$p")
            echo "$REPOS"
        done
    fi
}

# Check the status of all repos
for repo in `cat "$ALL_REPOS"`; do
  HTTP_STATUS=$(curl -s -u $GITHUB_USERNAME:$GITHUB_TOKEN -o /dev/null -w '%{http_code}' "https://api.github.com/repos/"$repo)
  if [ $HTTP_STATUS -ne 200 ]; then
    ERROR+="$repo "
  fi
done

# Unreachable repos message
if [[ -n $ERROR ]]; then
  FORMAT_ERROR=$(echo $ERROR | tr ' ' '\n')
  ERROR_MESSAGE=$(echo "IMPORTANT\n\nThe status code returned by the repository(ies) below differs from 200.\n\n""$FORMAT_ERROR")
fi

# Get the list of private repositories from the Github API
SCANT=$(repo_list "https://api.github.com/orgs/$ORG_NAME/repos?sort=full_name&per_page=$RESULT&type=" "private" | grep full_name | cut -d'"' -f4)

# Check if changes have been made to the list of private repos
if [[ "$(cat $PRIVATE_REPOS)" != "$SCANT" ]]; then
  DIFFT=$(diff --suppress-common-lines <(cat "$PRIVATE_REPOS") <(echo "$SCANT"))
fi

# Private repos message if change(s) occured
if [[ -n $DIFFT ]]; then
  DIFFT_MESSAGE=$(echo "\n\nPRIVATE REPOSITORIES\n\n""$DIFFT")
fi

# Get the list of public repositories from the Github API
SCANC=$(repo_list "https://api.github.com/orgs/$ORG_NAME/repos?sort=full_name&per_page=$RESULT&type=" "public" | grep full_name | cut -d'"' -f4)

# Check if changes have been made to the list of public repos
if [[ "$(cat $PUBLIC_REPOS)" != "$SCANC" ]]; then
  DIFFC=$(diff --suppress-common-lines <(cat "$PUBLIC_REPOS") <(echo "$SCANC"))
fi

# Public repos message if change(s) occured
if [[ -n $DIFFC ]]; then
  DIFFC_MESSAGE=$(echo "\n\nPUBLIC REPOSITORIES\n\n""$DIFFC")
fi

# Get the list of admin members from the Github API
SCANAM=$(repo_list "https://api.github.com/orgs/$ORG_NAME/members?per_page=$RESULT&role=" "admin" | grep login | cut -d'"' -f4)

# Check if changes have been made to the list of admin members
if [[ "$(cat $ADMIN_MEMBERS)" != "$SCANAM" ]]; then
  DIFFAM=$(diff --suppress-common-lines <(cat "$ADMIN_MEMBERS") <(echo "$SCANAM"))
fi

# Admin members message if change(s) occured
if [[ -n $DIFFAM ]]; then
  DIFFAM_MESSAGE=$(echo "\n\nADMIN MEMBERS\n\n""$DIFFAM")
fi

# Get the list of regular members from the Github API
SCANRM=$(repo_list "https://api.github.com/orgs/$ORG_NAME/members?per_page=$RESULT&role=" "member" | grep login | cut -d'"' -f4)

# Check if changes have been made to the list of regular members
if [[ "$(cat $REGULAR_MEMBERS)" != "$SCANRM" ]]; then
  DIFFRM=$(diff --suppress-common-lines <(cat "$REGULAR_MEMBERS") <(echo "$SCANRM"))
fi

# Regular members message if change(s) occured
if [[ -n $DIFFRM ]]; then
  DIFFRM_MESSAGE=$(echo "\n\nREGULAR MEMBERS\n\n""$DIFFRM")
fi

# Send a notification if changes have been recorded
if [[ -n $DIFFT_MESSAGE || $DIFFC_MESSAGE || $DIFFAM_MESSAGE || $DIFFRM_MESSAGE ]]; then
  echo -e "Hi,\n\nChanges have occured under the $ORG_NAME Github organisation.\n\n< added to known list\n> removed from known list\n\n$ERROR_MESSAGE$DIFFT_MESSAGE$DIFFC_MESSAGE$DIFFAM_MESSAGE$DIFFRM_MESSAGE\n\n-- \nThis script is running on $(hostname), and will notify $NOTIFY_EMAIL of changes to the list of repositories under the $ORG_NAME Github organization." | mail -s "GitHub Monitoring" $NOTIFY_EMAIL
  echo "Changes detected, sent a message to $NOTIFY_EMAIL."
  echo "$SCANT" > $PRIVATE_REPOS
  echo "$SCANC" > $PUBLIC_REPOS
  echo "$SCANT ""$SCANC" | tr ' ' '\n' | sort -f > $ALL_REPOS
  echo "$SCANAM" > $ADMIN_MEMBERS
  echo "$SCANRM" > $REGULAR_MEMBERS
fi
