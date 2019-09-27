"""
=========
__main__.py
=========

Runs the harmony_gdal CLI
"""

import argparse
from harmony_gdal.cli import harmony


def run_cli(args):
    """
    Runs the CLI.  Presently stubbed to demonstrate how a non-Harmony CLI fits in and allow
    future implementation or removal if desired.

    Parameters
    ----------
    args : Namespace
        Argument values parsed from the command line, presumably via ArgumentParser.parse_args

    Returns
    -------
    None
    """
    raise Exception("TODO: Implement non-Harmony CLI")


def main():
    """
    Parses command line arguments and invokes the appropriate method to respond to them

    Returns
    -------
    None
    """
    parser = argparse.ArgumentParser(
        prog='l2_subsetter', description='Run the PO.DAAC L2 subsetter')
    harmony.setup_cli(parser)

    args = parser.parse_args()

    if (harmony.is_harmony_cli(args)):
        harmony.run_cli(parser, args)
    else:
        run_cli(args)


if __name__ == "__main__":
    main()
