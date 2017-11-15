#!/usr/bin/env python
"""
<Program Name>
  in_toto_run.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  June 27, 2016

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a command line interface which takes any link command of the software
  supply chain as input and wraps in_toto metadata recording.

  in_toto run options are separated from the command to be executed by
  a double dash.

  The implementation of the tasks can be found in runlib.

  Example Usage
  ```
  in-toto-run --step-name write-code --materials . --products . --key bob \
      -- vi foo.py
  ```

"""

import sys
import argparse
import in_toto.user_settings
from in_toto import (util, runlib, log)

def in_toto_run(step_name, material_list, product_list,
    link_cmd_args, key, record_streams, use_gpg=False):
  """
  <Purpose>
    Calls runlib.in_toto_run and catches exceptions

  <Arguments>
    step_name:
            A unique name to relate link metadata with a step defined in the
            layout.
    material_list:
            List of file or directory paths that should be recorded as
            materials.
    product_list:
            List of file or directory paths that should be recorded as
            products.
    link_cmd_args:
            A list where the first element is a command and the remaining
            elements are arguments passed to that command.
    key:
            Private key to sign link metadata.
            Format is securesystemslib.formats.KEY_SCHEMA
            If `use_gpg` is True, then this parameter is expected to be a
            GPG keyid.
    record_streams:
            A bool that specifies whether to redirect standard output and
            and standard error to a temporary file which is returned to the
            caller (True) or not (False).
    use_gpg:
            If true the `key` argument will be interpreted as GPG keyid


  <Exceptions>
    SystemExit if any exception occurs

  <Side Effects>
    Calls sys.exit(1) if an exception is raised

  <Returns>
    None.
  """

  try:
    runlib.in_toto_run(step_name, material_list, product_list,
        link_cmd_args, key, record_streams, use_gpg)
  except Exception as e:
    log.error("in toto run - {}".format(e))
    sys.exit(1)

def main():
  """Parse arguments, load key from disk (prompts for password if key is
  encrypted) and call in_toto_run. """

  parser = argparse.ArgumentParser(
      description="Executes link command and records metadata")
  # Whitespace padding to align with program name
  lpad = (len(parser.prog) + 1) * " "

  parser.usage = ("\n"
      "%(prog)s  --step-name <unique step name>\n{0}"
               " --key <functionary private key path or GPG keyid>\n{0}"
               "[--use-gpg]\n{0}"
               "[--materials <filepath>[ <filepath> ...]]\n{0}"
               "[--products <filepath>[ <filepath> ...]]\n{0}"
               "[--record-streams]\n{0}"
               "[--no-command]\n{0}"
               "[--verbose] -- <cmd> [args]\n\n"
               .format(lpad))

  in_toto_args = parser.add_argument_group("in-toto options")

   # FIXME: Do we limit the allowed characters for the name?
  in_toto_args.add_argument("-n", "--step-name", type=str, required=True,
      help="Unique name for link metadata")

  in_toto_args.add_argument("-m", "--materials", type=str, required=False,
      nargs='+', help="Files to record before link command execution")

  in_toto_args.add_argument("-p", "--products", type=str, required=False,
      nargs='+', help="Files to record after link command execution")

  in_toto_args.add_argument("-k", "--key", type=str, required=True,
      help="Path to private key to sign link metadata (PEM) or GPG keyid")

  in_toto_args.add_argument("-g", "--use-gpg", dest="use_gpg", default=False,
      action="store_true", help=("Load `--key <keyid>` from GPG keyring "
      "instead of PEM file (EXPERIMENTAL)"))

  in_toto_args.add_argument("-b", "--record-streams",
      help="If set redirects stdout/stderr and stores to link metadata",
      dest="record_streams", default=False, action="store_true")

  in_toto_args.add_argument("-x", "--no-command",
      help="Set if step does not have a command",
      dest="no_command", default=False, action="store_true")

  in_toto_args.add_argument("-v", "--verbose", dest="verbose",
      help="Verbose execution.", default=False, action="store_true")

  # FIXME: This is not yet ideal.
  # What should we do with tokens like > or ; ?
  in_toto_args.add_argument("link_cmd", nargs="*",
    help="Link command to be executed with options and arguments")

  args = parser.parse_args()

  # Turn on all the `log.info()` in the library
  if args.verbose:
    log.logging.getLogger().setLevel(log.logging.INFO)

  # Override defaults in settings.py with environment variables and RCfiles
  in_toto.user_settings.set_settings()

  # We load the key here because it might prompt the user for a password in
  # case the key is encrypted. Something that should not happen in the library.
  if not args.use_gpg:
    try:
      key = util.prompt_import_rsa_key_from_file(args.key)
    except Exception as e:
      log.error("in load key - {}".format(e))
      sys.exit(1)
  else:
    key = args.key
    # TODO: Check if we can actually load the GPG key from the keyid
    pass

  if args.no_command:
    in_toto_run(args.step_name, args.materials, args.products, [],
      key, args.record_streams)
  else:
    if not args.link_cmd:
      parser.print_usage()
      parser.exit("For no command use --no-command option")
    in_toto_run(args.step_name, args.materials, args.products,
      args.link_cmd, key, args.record_streams, args.use_gpg)

if __name__ == "__main__":
  main()
