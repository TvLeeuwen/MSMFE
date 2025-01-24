# imports --------------------------------------------------------------------
import sys
from pathlib import Path


# defs -----------------------------------------------------------------------
def ask_user_to_continue(msg="Do you want to continue? (y/n): "):
    while True:
        response = input(msg).strip().lower()
        if response in ["y", "Y", "yes", "Yes"]:
            return True
        elif response in ["n", "N", "no", "No"]:
            return False
        else:
            print("Invalid input. Please enter 'y' for yes or 'n' for no.")


def handle_args_dir_match(input_file: Path, output_file: Path):
    if input_file.parents[0] != output_file.parents[0]:
        print("Warning: non-matching input and output directory")
        print(input_file)
        print(output_file)
        if not ask_user_to_continue():
            print("Exiting module...")
            sys.exit()


def handle_args_suffix(output_file: Path, suffix: str = ".mesh"):
    if output_file.suffix != suffix:
        output_file = output_file.with_suffix(suffix)

    return output_file


def handle_args_integer(arg):
    if not isinstance(arg, int):
        sys.exit(f"Error: Input value must be an integer, current value: {arg}")
