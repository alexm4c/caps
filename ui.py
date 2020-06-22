#!/usr/bin/env python

"""
audio.py

This module is a library of helper classes and functions for...

#---------------------------------------------------------------------#

Classes and functions defined in this module include:

    Style
    print_info
    print_error
    print_title
    clear_and_title
    prompt
    multi_prompt

"""

import subprocess


class Style:
    # Define various unix terminal escape sequences changing
    # terminal text style such as colour, font weight, etc.
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_info(string):
    # Output string to terminal with a predefined title style.
    print('{0}{1}{2}'.format(
        Style.BLUE,
        string,
        Style.END
    ))


def print_error(string):
    # Output string to terminal with a predefined title style.
    print('{0}{1}{2}'.format(
        Style.RED,
        string,
        Style.END
    ))


def print_title(string):
    # Output string to terminal with a predefined title style.
    print("{0}{1}{2}{3}".format(
        Style.BOLD,
        Style.GREEN,
        string,
        Style.END,
    ))


def clear_and_title(string):
    # Clear the terminal and print a title.
    subprocess.call('clear')
    print_title(string)


def prompt(
    input_prompt,
    message='',
    error='',
    condition=None,
    default='',
):
    # Prompt a terminal user for input. If the input passes the given
    # check, returns the users input. If the input fails the check,
    # prints an error and will reprompt the user until their input is valid.
    if message:
        print('{0}:'.format(message))

    while True:
        if input_prompt and default:
            default_prompt = ' [{0}{1}{2}]'.format(
                Style.YELLOW,
                default,
                Style.END,
            )
            input_prompt = input_prompt + default_prompt

        response = input('{}> '.format(input_prompt))
        response = response if response else default

        if condition and not condition(response):
            print_error('{}'.format(error))
        else:
            break

    return response


def multi_prompt(
    input_prompt,
    message='',
    error='',
    condition=None,
    defaults=[],
):
    # Similar to prompt() except this function can prompt the
    # user for multiple responses to the same prompt. For example,
    # recording multiple speakers preset in a single audio file.
    if message:
        print('{0}:'.format(message))

    print_info('Empty line to continue, Ctrl+D to undo')

    responses = []
    index = 0

    while True:
        try:
            if defaults and index < len(defaults):
                default = defaults[index] 
            else:
                default = None

            response = prompt(
                input_prompt=input_prompt,
                condition=condition,
                error=error,
                default=default
            )

            if response:
                index = index + 1
                responses.append(response)
            elif not responses:
                # Error and reprompt if user responses are empty
                print_error('You must input at least one {}'.format(input_prompt))
            else:
                break

        except EOFError:
            # Catch Ctrl+D input and remove last response
            print()
            if responses:
                responses.pop()
                index = index - 1
                info = '{0}: {1}'.format(
                    input_prompt,
                    ', '.join(responses) if len(responses) else None
                )
                print_info(info)

    return responses


def confirm(message, default='yes'):
    # Prompt the user for a yes/no response
    # and return True if yes and False if no.
    def is_yes(string):
        return string.lower() in ['yes', 'ye', 'y']

    def is_no(string):
        return string.lower() in ['no', 'n']

    def is_valid(string):
        return is_yes(string) or is_no(string)

    if not is_valid(default):
        raise ValueError('\'default\' must be yes or no')

    message = '{0} (yes/no) [{1}{2}{3}]'.format(
        message,
        Style.YELLOW,
        default,
        Style.END,
    )

    response = prompt(
        input_prompt='',
        message=message,
        condition=is_valid,
        error='Please respond yes or no',
        default=default,
    )

    return True if is_yes(response) else not is_no(response)


if __name__ == "__main__":
    print(__doc__)
