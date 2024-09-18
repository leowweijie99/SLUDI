import argparse
import sys

import incompatibilities


def parseArgs(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', help='The Subject ID for CompCheck to discover', required=False)
    if len(argv) == 0:
        parser.print_help()
        exit(1)
    opts = parser.parse_args(argv)
    return opts


def main():
    opts = parseArgs(sys.argv[1:])
    incompatibilities.run(opts.id)
    exit(0)

if __name__ == "__main__":
    main()