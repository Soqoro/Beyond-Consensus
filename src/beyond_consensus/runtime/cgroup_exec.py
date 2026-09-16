"""Trusted host bootstrap: join the invocation cgroup before starting Apptainer.

Invoked by absolute path with Python -I -S. Never imports candidate code.
"""
import os
import sys


if __name__ == "__main__":
    with open(sys.argv[1], "w", encoding="ascii") as stream:
        stream.write(str(os.getpid()))
    os.execve(sys.argv[2], sys.argv[2:], os.environ)
