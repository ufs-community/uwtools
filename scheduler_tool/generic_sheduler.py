#!/usr/bin/env python

import os

def mkdir_p(dir):
    '''make a directory (dir) if it doesn't exist'''
    if not os.path.exists(dir):
        os.mkdir(dir)

job_directory = "%s/jobCards" %os.getcwd()
home = os.environ['HOMEPATH']

# Make top level directories
mkdir_p(job_directory)

def get_non_negative_int(prompt):
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print("Sorry, Enter an integer.")
            continue

        if value < 0:
            print("Sorry, your response must not be negative.")
            continue
        else:
            break
    return value

def validate_clock(in_):
    while True:
        try:
            a, b, c = in_.split(":")
            for v in [a, b, c]:
                assert len(v) == 2
            _, _, _ = int(a), int(b), int(c)
        except ValueError:
            print("Sorry, Enter in format HH:MM:SS.")
            continue

        if _ < 0:
            print("Sorry, your response must not be negative.")
            continue
        else:
            break
    return _, _, _

jobname = input("Enter Name of Job: \n")
std_out = input("Enter Path to STDOUT: \n")
std_err = input("Enter Path to STD_Error: \n")
walltime = validate_clock(input("Enter Wall Time in HH:MM:SS: \n"))
queue_name = input("Enter Queue Name: \n")
acc_name = input("Enter Account Name: \n")
node_count = get_non_negative_int("Enter Node Count: \n")
core_node = get_non_negative_int("Enter Cores Per node: \n")

job_file = os.path.join(job_directory,"%s.sh" %jobname)

with open(job_file, 'w') as fh:
        fh.writelines("#!/bin/bash\n")
        fh.writelines("#SBATCH --job-name=%s\n" % jobname)
        fh.writelines("#SBATCH --output=.out/%s.out\n" % std_out)
        fh.writelines("#SBATCH --error=.out/%s.err\n" % std_err)
        fh.writelines("#SBATCH --time=%s:%s:%s\n" % walltime)
        fh.writelines("#SBATCH --partition=%s\n" % queue_name)
        fh.writelines("#SBATCH --account=%s\n" % acc_name)
        fh.writelines("#SBATCH --nodes=%s\n" % node_count)
        fh.writelines("#SBATCH --ntasks-per-node=%s\n" % core_node)
        fh.writelines("echo Hello World \n")