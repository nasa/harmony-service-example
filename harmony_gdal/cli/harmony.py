"""
=========
harmony.py
=========

Parses CLI arguments provided by Harmony and invokes the subsetter accordingly
"""

import json
import hashlib
import urllib

from os import path, makedirs
from harmony_gdal.transform import invoke

def setup_cli(parser):
    """
    Adds Harmony arguments to the CLI being parsed by the provided parser

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser being used to parse CLI arguments

    Returns
    -------
    None
    """
    parser.add_argument('--harmony-action',
                        choices=['invoke'],
                        help='the action Harmony needs to perform (currently only "invoke")')
    parser.add_argument('--harmony-input',
                        help='the input data for the action provided by Harmony')


def is_harmony_cli(args):
    """
    Returns True if the passed parsed CLI arguments constitute a Harmony CLI invocation, False otherwise

    Parameters
    ----------
    args : Namespace
        Argument values parsed from the command line, presumably via ArgumentParser.parse_args

    Returnså
    -------
    is_harmony_cli : bool
        True if the provided arguments constitute a Harmony CLI invocation, False otherwise
    """
    return bool('harmony_action' in args)


def run_cli(parser, args):
    """
    Runs the Harmony CLI invocation captured by the given args

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser being used to parse CLI arguments, used to provide CLI argument errors
    args : Namespace
        Argument values parsed from the command line, presumably via ArgumentParser.parse_args

    Returns
    -------
    is_harmony_cli : bool
        True if the provided arguments constitute a Harmony CLI invocation, False otherwise
    """

    if args.harmony_action in ['invoke'] and not bool(args.harmony_input):
        parser.error(
            '--harmony-input must be provided for --harmony-action  %s' % (args.harmony_action))

    input = None
    output_name = None
    if args.harmony_input:
        input = json.loads(args.harmony_input)
        output_name = hashlib.sha256(
            args.harmony_input.encode('utf-8')).hexdigest()

    if args.harmony_action == 'invoke':
        invoke(input, output_name)
