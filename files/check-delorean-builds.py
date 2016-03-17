#!/usr/bin/env python
import csv
import sys
import requests
from cStringIO import StringIO

# Delorean build statuses
BUILD_STATUSES = ['SUCCESS', 'FAILED']

# URL to Delorean build statuses in csv format
DEFAULT_RELEASE = "centos7"
DEFAULT_TAG = "current"
VERSIONS = "http://trunk.rdoproject.org/{0}/{1}/versions.csv"
REPORT = "http://trunk.rdoproject.org/{0}/{1}/report.html"

# Nagios-compatible exit codes
EXIT_CODES = {
    'OK': 0,
    'WARNING': 1,
    'CRITICAL': 2,
    'UNKNOWN': 3
}


def return_exit(status, message=None):
    """
    Helper to exit the script in a way meaningful for use in monitoring
    :param status: Can be one of 'OK', 'WARNING', 'CRITICAL, 'UNKNOWN'
    :param message: An optional message to print
    :return: exits script
    """
    # Sanity check
    if status not in EXIT_CODES:
        return_exit('UNKNOWN', 'Attempted exit through an unknown exit code')

    # If there's a message, write to stderr if not OK, otherwise stdout
    if message:
        if 'OK' not in status:
            sys.stderr.write(message)
        else:
            sys.stdout.write(message)

    sys.exit(EXIT_CODES[status])


def retrieve_versions(url):
    """
    Helper to download the versions report and return a dictionary
    :param url: URL to download the csv file from
    :return: csv DictReader object
    """
    # Get the csv content into a dummy file in-memory
    versions = requests.get(url).text
    versions_file = StringIO(versions)
    versions_file.seek(0)

    # Return a parsed csv object
    csv_versions = csv.DictReader(versions_file)
    return csv_versions


if __name__ == '__main__':
    try:
        release = sys.argv[1]
        tag = sys.argv[2]
    except IndexError:
        # Default to master current
        release = DEFAULT_RELEASE
        tag = DEFAULT_TAG
    url = VERSIONS.format(release, tag)

    versions = retrieve_versions(url)
    report = REPORT.format(release, tag)

    projects = []
    problem = False
    for line in versions:
        source_repo = line['Source Repo']
        source_sha = line['Source Sha']
        project = source_repo.split('/')[-1]
        status = line['Status']

        if "SUCCESS" not in status:
            projects.append(project)
            problem = True

    if problem:
        error_message = "Build failure on {0}/{1}:".format(release, tag)
        projects = ', '.join(projects)
        message = "{0} {1}: {2}".format(error_message, projects, report)
        return_exit('CRITICAL', message)
    else:
        return_exit('OK', 'No build failures detected: {0}'.format(report))
