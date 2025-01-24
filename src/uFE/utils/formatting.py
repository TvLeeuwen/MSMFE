"""
Modules for standardizing output formatting etc.
"""

# Imports
import time

# Constants
PRINT_LEN = 80


# Defs
def timer(func):
    """Decorator to time functions"""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"{elapsed_time:.4f}s".rjust(PRINT_LEN))

        return result

    return wrapper


def return_timer(func):
    """Decorator to time functions"""

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"{elapsed_time:.4f}s".rjust(PRINT_LEN))

        return result, elapsed_time

    return wrapper


def print_status(
    left_arg: str,
    right_arg: str,
) -> None:
    """
    Prints process status according to the output standard; process justified left,
    status justified right. With a standardized line length of `PRINT_LEN`.

    :param `left_arg`: Process describing argument
    :param `right_arg`: Process status argument
    """
    print(left_arg.ljust(len(left_arg)) + right_arg.rjust(PRINT_LEN - len(left_arg)))


def print_section(repeat=1):
    for _ in range(0, repeat):
        print("_" * PRINT_LEN)
