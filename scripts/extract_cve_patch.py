#!/usr/bin/env python

import sh
import os
import multiprocessing
import argparse
from util.pretty_print import log,success,error

def print_help():
    print("This script is used to extract CVE related commits")
    print("OPTIONS:")
    print("  -r/--repo <value> Specify the directory of the target repository")
    print("  -t/--target <value> Specify the location to write the target file")
    print("EXAMPLE:\n  $ python extract_cve_patch.py -r ./linux -t ./vuln")


def parse_commit(source, commitID, target):
    log('[+] Parsing ' + commitID, 'CYAN')

    target_git = sh.git.bake("--no-pager", _cwd=source)

    modified_files = target_git.diff("--diff-filter=M", "--name-only", commitID + "^", commitID).split('\n')[:-1]
    # some patches modifies so many files,
    # to simplify the problem, we only parse patches that changed no more than 3 files.
    if len(modified_files)>3:
        log('[-] Commit contains too much files! ', 'YELLOW')
        return

    os.system('mkdir -p ' + os.path.join(target, 'SeP', commitID))

    patch_path = os.path.join(target, 'SeP', commitID, 'patch')
    commit_path = os.path.join(target, 'SeP', commitID, 'commit')

    target_git.diff("--diff-filter=M", commitID + '^', commitID, _out=patch_path)
    target_git.log(commitID, "-n 1", "--pretty=full", _out=commit_path)
    # generate full git commit messages and
    # patch file for the commit

    os.system('mkdir -p ' + os.path.join(target, 'SeP', commitID, "before"))
    os.system('mkdir -p ' + os.path.join(target, 'SeP', commitID, "patched"))


    for file in modified_files:
        try:
            # copy each file has been modified, copy them to the target directory
            file_before = os.path.join(target, 'SeP', commitID, 'before', file.replace('/', '_'))
            file_patched = os.path.join(target, 'SeP', commitID, 'patched', file.replace('/', '_'))

            target_git.show(commitID + "^:" + file, _out=file_before)
            target_git.show(commitID + ":" + file, _out=file_patched)

        except Exception:
            # The rule above may not match all submodule updates,
            # In case for bad data, we add a Exception Handler here.
            error('Parse '+ commitID+'Error!')
            error('Delete commit folders: ' + commitID)
            os.system('rm -rf '+os.path.join(target,'SeP',commitID))
            return

    success('Parse ' + commitID + ' Done!')


def parse_repo(source, target):
    target = os.path.abspath(target)
    source = os.path.abspath(source)
    target_git = sh.git.bake("--no-pager", _cwd=source)
    cve_commit_list = target_git.log("--grep=CVE", "--format=%H").split('\n')[:-1]

    tasks = []
    for commit in cve_commit_list:
        tasks.append((source, commit, target))

    # pool = multiprocessing.Pool()
    # pool.map(parse_commit, tasks[0])

    for task in tasks:
        parse_commit(task[0], task[1], task[2])

    success('All things on Parsing Target Done!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="scripts to extract CVE related commits")
    parser.add_argument('-r', '--repo', help="repository's location")
    parser.add_argument('-t', '--target', help="where to store the target file")

    args = parser.parse_args()

    if not os.path.isdir(os.path.join(os.getcwd(), args.repo)):
        print("[-] Repo is Not a valid Dir")
        print_help()
        exit(-1)

    parse_repo(args.repo, args.target)
