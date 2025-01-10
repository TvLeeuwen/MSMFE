import os
import inspect
from datetime import datetime
from functools import wraps


def log_md(log_file=None):
    """
    A decorator to log the execution of the main function with date, time,
    filename, and arguments.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # If no log file is specified, run the function without logging
            if log_file is None:
                return func(*args, **kwargs)

            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
            caller_filename = os.path.basename(inspect.getfile(func))

            # Format the header with date, time, and filename
            header = f"# {current_datetime} \n## `{caller_filename}`\n"
            message = ""

            # Get the function's parameter names and default values
            sig = inspect.signature(func)
            params = sig.parameters

            # Map each positional argument to its parameter name
            if args or kwargs:
                message += "- Parameters:\n"
                for i, arg in enumerate(args):
                    param_name = list(params.keys())[i]
                    message += f"  - {param_name}: `{arg}`\n"
                # Add each keyword argument with its original parameter name
                for key, value in kwargs.items():
                    message += f"  - {key}: `{value}`\n"
            # Add a line for user notes
            message += "- Notes:"

            # Read the existing content of the log file (to prepend)
            if os.path.exists(log_file):
                with open(log_file, "r") as file:
                    existing_content = file.read()
            else:
                existing_content = ""

            # Write the new log entry at the beginning of the log file
            with open(log_file, "w") as file:
                file.write(header + message + "\n\n" + existing_content)

            # Execute the original function
            return func(*args, **kwargs)
        return wrapper
    return decorator
