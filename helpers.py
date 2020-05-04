#!/usr/bin/env python

"""
helpers.py

This module is a library of helper classes and functions for
processing audio and collecting metadata. Specifically it contains
functions that help with finding and opening audio files, reading
and writing metadata to csv, and prompting a terminal user for input.

#---------------------------------------------------------------------#

Classes and functions defined in this module include:

    VLCPlayer
    write_metadata_csv
    read_metadata_csv
    print_metadata
    list_audio_files
    find
    timestamp_seconds
    is_valid_segment
    Style
    print_info
    print_error
    print_title
    clear_and_title
    prompt
    multi_prompt
"""

import csv
import glob
import os
import re
import subprocess


# The list of extensions of file types that this module will process
VALID_AUDIO = ('.mp3',)


class VLCPlayer:
    # Provide a clean way to open an audio file with VLC, silence
    # it's stdout messages, and then terminate the subproccess.
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.devnull = open(os.devnull, 'w')
        self.vlc = subprocess.Popen(
            ['vlc', self.path],
            stdout=self.devnull,
            stderr=self.devnull,
        )
        return self

    def __exit__(self, type, value, traceback):
        self.vlc.terminate()
        self.devnull.close()


class MetadataList(list):
    # Dictionary list of audio metadata in a specific format
    KEYS = ['filepath', 'event_name', 'title', 'speakers', 'segments']

    def add_item(self, data={}):
        metadata = self.Metadata(data)
        self.append(metadata)
        return metadata

    def get_item(self, key, value):
        # Search through metadata and returns the
        # first item with matching key value pair.
        for item in self:
            if item and item[key] == value:
                return item

    def write_to_csv(self, output_csv):
        # Write the dictionary list of audio metadata into a csv file.
        rows = []
        for metadata in self:
            if metadata:
                row = {}
                row['filepath'] = metadata['filepath']
                row['event_name'] = metadata['event_name']
                row['title'] = metadata['title']
                if metadata['speakers']:
                    row['speakers'] = ';'.join(metadata['speakers'])
                if metadata['segments']:
                    row['segments'] = ';'.join(metadata['segments'])
                rows.append(row)

        with open(output_csv, "w", newline='') as file:
            dict_writer = csv.DictWriter(
                file,
                self.KEYS,
                quoting=csv.QUOTE_ALL,
            )
            dict_writer.writeheader()
            dict_writer.writerows(rows)

    def read_from_csv(self, input_csv):
        # Reads a csv file of audio metadata into a dictionary list
        with open(input_csv, "r") as file:
            reader = csv.DictReader(
                file,
                self.KEYS,
                quoting=csv.QUOTE_ALL,
            )
            for row in reader:
                row['speakers'] = row['speakers'].split(';')
                row['segments'] = row['segments'].split(';')
                self.add_item(row)

    class Metadata(dict):
        def print_pretty(self):
            # Print in a human readable format
            print()
            print('{0}Filepath:{1}\t{2}'.format(
                Style.BOLD,
                Style.END,
                self['filepath'],
            ))
            print('{0}Event:{1}\t\t{2}'.format(
                Style.BOLD,
                Style.END,
                self['event_name'],
            ))
            print('{0}Title:{1}\t\t{2}'.format(
                Style.BOLD,
                Style.END,
                self['title'],
            ))
            print('{0}Speakers:{1}\t{2}'.format(
                Style.BOLD,
                Style.END,
                ', '.join(self['speakers']),
            ))
            print('{0}Segments:{1}\t{2}'.format(
                Style.BOLD,
                Style.END,
                ', '.join(self['segments'])),
            )


def list_audio_files(path):
    # Search the given input directory for all audio that matches 
    # valid file extensions and returns a list of their paths.
    audio_files = []
    
    for filepath in glob.glob(path):
        if os.path.isfile(filepath):
            audio_files.append(os.path.join(filepath))
        else:
            for root, _, files in os.walk(filepath):
                for file in files:
                    audio_files.append(os.path.join(root, file))

    audio_files = filter(
        lambda x: True if x.lower().endswith(VALID_AUDIO) else False,
        audio_files,
    )

    return list(audio_files)


def timestamp_seconds(string):
    # Convert and audio timestamp string in format mm:ss into
    # it's seconds value
    minutes, seconds = [ int(x) for x in string.split(':') ]
    return seconds + (minutes * 60)


def is_valid_segment(string):
    # Validate and audio segment made up of a start timestamp and end
    # timestamp delimited by '-' (mm:ss-mm:ss). Segments with end cuts
    # that procede start cuts are invalid Returns True if valid or None
    # and False if invalid.
    if not string:
        # Defer None validation
        return True

    if not re.match(r'^\d{2}:[0-5]\d-\d{2}:[0-5]\d$', string):
        return False

    start, end = [ timestamp_seconds(x) for x in string.split('-') ]
    return start < end


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
    # prints an error and reprompts the user until their input is valid.
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
                # Error and reprompt if user reponses are empty
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
