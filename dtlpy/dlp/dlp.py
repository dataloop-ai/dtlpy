#! /usr/bin/python3
import subprocess
import traceback
import datetime
import logging
import shlex
import sys
import os
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit import prompt
import dtlpy as dlp
from dtlpy import exceptions
from dtlpy.dlp.cli_utilities import FileHistory, get_parser_tree, DlpCompleter
from dtlpy.dlp.parser import get_parser
from dtlpy.dlp.command_executor import CommandExecutor

dlp.client_api.is_cli = True

##########
# Logger #
##########
# set levels for CLI
logger = logging.getLogger(name='dtlpy')
handler_id = next((i for i, hand in enumerate(logger.handlers) if isinstance(hand, logging.StreamHandler)), 0)
logger.handlers[handler_id].setLevel(level=logging.INFO)
logger.propagate = False


def dlp_exit():
    print(datetime.datetime.now(datetime.timezone.utc))
    print("Goodbye ;)")
    sys.exit(0)


def main():
    try:
        parser = get_parser()
        keywords = get_parser_tree(parser=parser)
        args = parser.parse_args()
        history_file = os.path.join(os.getcwd(), ".history.txt")
        command_executor = CommandExecutor(dl=dlp, parser=parser)

        if args.version:
            logger.info("Dataloop SDK Version: {}".format(dlp.__version__))

        elif args.operation == "shell":
            #######################
            # Open Dataloop shell #
            #######################
            while True:
                text = prompt(u"dl>",
                              history=FileHistory(history_file),
                              auto_suggest=AutoSuggestFromHistory(),
                              completer=DlpCompleter(keywords=keywords, dlp=dlp))
                if text == '':
                    # in new line
                    continue

                try:
                    if text in ["-h", "--help"]:
                        text = "help"
                    text = shlex.split(text)
                    if text[0] not in keywords:
                        p = subprocess.Popen(text)
                        p.communicate()
                        continue
                    parser = get_parser()
                    args = parser.parse_args(text)
                    if args.operation == "exit":
                        dlp_exit()
                    else:
                        command_executor.run(args=args)
                except exceptions.TokenExpired:
                    print(datetime.datetime.now(datetime.timezone.utc))
                    print("[ERROR] token expired, please login.")
                    continue
                except SystemExit as e:
                    # exit
                    if e.code == 0:
                        if "-h" in text or "--help" in text:
                            continue
                        else:
                            sys.exit(0)
                    # error
                    else:
                        print(datetime.datetime.now(datetime.timezone.utc))
                        print('"{command}" is not a valid command'.format(command=text))
                        continue
                except Exception as e:
                    print(datetime.datetime.now(datetime.timezone.utc))
                    if hasattr(e, 'message'):
                        print(e.message)
                    else:
                        print(e.__str__())
                    continue

        else:
            ######################
            # Run single command #
            ######################
            try:
                command_executor.run(args=args)
                sys.exit(0)
            except exceptions.TokenExpired:
                print(datetime.datetime.now(datetime.timezone.utc))
                print("[ERROR] token expired, please login.")
                sys.exit(1)
            except Exception as e:
                print(datetime.datetime.now(datetime.timezone.utc))
                print(traceback.format_exc())
                print(e)
                sys.exit(1)
    except KeyboardInterrupt:
        dlp_exit()
    except EOFError:
        dlp_exit()
    except Exception:
        print(traceback.format_exc())
        dlp_exit()


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(datetime.datetime.now(datetime.timezone.utc))
        print("[ERROR]\t%s" % err)
    print("Dataloop.ai CLI. Type dlp --help for options")
