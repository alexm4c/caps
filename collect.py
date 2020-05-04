#!/usr/bin/env python

"""usage: collect.py path [-o=] [-h]

Arguments:

path                The directory path containing raw
                    audio to be processed.

Options:

-o, --output-csv    The csv filepath to write results to.
-h, --help          Show this help message and exit.

Requirements:

VLC

#---------------------------------------------------------------------#

This script will find all audio files in the given path, 
prompt the user to describe the audio metadata, and
write the results to a csv file.

If the output csv is not specified. A csv file will be
created in current working directory with the same name
as the input directory.

"""

import os
import sys
import getopt

from ui import *
from audio import *

def collect_metadata(path, output_csv=None):
    """Collect raw audio metadata from terminal ui and write results to csv

    Args:
        path: The directory path containing raw audio to be processed.
        output_csv: Optional csv filepath to write results to

    Returns:
        MetadataList object containing results
    """
    audio_files = list_audio_files(path)

    if not audio_files:
        print_error('No audio files where found in {}'.format(path))
        sys.exit(1)

    event_name = os.path.basename(os.path.dirname(path))

    metadata_list = MetadataList()

    if not output_csv:
        output_csv = '{}.csv'.format(event_name)

    if os.path.isfile(output_csv):
        metadata_list.read_from_csv(output_csv)

    # clear_and_title('Welcome to CAPS, a SALTY Conference Audio Processing System')

    try:
        # Wrap user input block in try-except to catch Ctrl-C and Ctrl+D
        # input so data can be saved before exiting cleanly
        if not confirm('\nFound {} audio files. Continue?'.format(len(audio_files))):
            sys.exit(0)

        event_name = prompt(
            input_prompt="Event",
            message='\nEnter event name',
            condition=lambda x: True if x else False,
            error="You must enter an event name",
            default=event_name,
        )

        for file in audio_files:
            print_title('\nOpening ' + file)

            metadata = metadata_list.get_item('filepath', file)

            if metadata:
                metadata.print_pretty()

            # with VLCPlayer(file) as vlc:
            if confirm('\nSkip this file?', default='no'):
                continue

            if not metadata:
                metadata = metadata_list.add_item({
                    'filepath': file,
                    'event_name': event_name,
                    'title': None,
                    'speakers': None,
                    'segments': None,
                })

            metadata['title'] = prompt(
                input_prompt='Title',
                message='\nEnter the title for this audio',
                condition=lambda x: True if x else False,
                error='You must enter a title',
                default=metadata['title'],
            )

            metadata['speakers'] = multi_prompt(
                input_prompt='Speaker',
                message='\nInput each speakers name',
                defaults=metadata['speakers'],
            )

            metadata['segments'] = multi_prompt(
                input_prompt='Segment',
                message='\nInput start and end cut of each audio segment (mm:ss-mm:ss)',
                condition=is_valid_segment,
                error='You must input the correct format (mm:ss-mm:ss)'
                    ' and start cut must precede end cut',
                defaults=metadata['segments'],
            )

    except (KeyboardInterrupt, EOFError):
        print_error('\nAborted')
    else:
        return metadata_list
    finally:
        if metadata_list and output_csv:
            metadata_list.write_to_csv(output_csv)


def _args():
    path = None
    output_csv = None
    try:
        opts, args = getopt.gnu_getopt(
            sys.argv[1:],
            'o:h',
            ['output-csv=', 'help']
        )
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(1)
    for option, value in opts:
        if option in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        elif option in ('-o', '--output-csv'):
            output_csv = value
    if output_csv and not os.path.isfile(output_csv):
        print_error('{} is not a valid output file'.format(output_csv))
        sys.exit(1)
    if not args:
        print_error('You must provide and input path')
        sys.exit(1)
    else:
        path = args[0]
    return (path, output_csv)


if __name__ == '__main__':
    collect_metadata(*_args())
