#!/usr/bin/env python



# Arguments:
#   Audio metadata (csv or object?)
#   Path to audio

# Options:
#   Path to export processed audio (default = input_dir + '_processed')

# 1. retrieve audio metadata
#
# 2. get audio file list
#
# 3. for each file in list 
#
#   3a open file with pydub
#
#   3b. cut audio into segments and reattach with cross fade
#
#   3c. optimise audio
#           normalise 0.5,
#           high pass 100
#           compression
#           remove silence?
#
#   3d. export as mp3 with tags
#

import timeit
import sys
import logging
import subprocess
import os
import getopt

from ui import *
from metadata import *

from tqdm import tqdm
from tempfile import mkstemp
from sox import Transformer, Combiner
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen import File


def process_audio(metadata_list, output_dir=None):
    # Silence PySox warnings and info
    logging.getLogger('sox').setLevel(logging.ERROR)
    
    output_dir = output_dir if output_dir else './processed'
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    try:
        progress_bar = tqdm(
            total=len(metadata_list),
            bar_format='{desc}{percentage:3.0f}%|'
                       '{bar}'
                       '| {n_fmt}/{total_fmt} ETA {remaining}'
        )
        for metadata in metadata_list:
            title = metadata['title']
            input_path = metadata['filepath']
            output_file = os.path.join(
                output_dir,
                '{0}{1}'.format(title, '.mp3')
            )
            
            progress_bar.set_description(title)

            cut(input_path, output_file, metadata)
            tag(output_file, metadata.toId3())
            progress_bar.update(1)

        progress_bar.close()

    except (KeyboardInterrupt, EOFError):
        print_error('\nAborted')


def cut(input_path, output_file, metadata):
    segments = metadata['segments']
    segments = [ segment_seconds(segment) for segment in segments ]

    with TempFile('.mp3') as temp_file:
        # Open a new temporary file to store audio in between processes
        if segments:
            # Cut audio into segments and create fade in/out
            # We need to use a new temporary file for each
            # audio segment
            temp_segments = [ TempFile('.mp3') for segment in segments ]
            try:
                for index, segment in enumerate(segments):
                    sox = Transformer()
                    sox.channels(1)
                    sox.norm(-24)
                    sox.trim(*segment)
                    sox.fade(1, 2, 't')
                    sox.build(input_path, temp_segments[index].path)

                if len(segments) > 1:
                    # Concatenate all the audio segments back together
                    # and output to our main temporary file
                    Combiner().build(
                        [ temp_segment.path for temp_segment in temp_segments ],
                        temp_file.path,
                        'concatenate',
                    )
                else:
                    # Only one segment so we don't need to combine anything
                    subprocess.run(['cp', temp_segments[0].path, temp_file.path])

            except Exception as e:
                raise(e)
            finally:
                # Cleanup temporary segment files even on error
                if temp_segments:
                    for temp_segment in temp_segments:
                        temp_segment.close()

        # Second process: filter, compress and EQ the
        # audio in temporary file and output to output_file
        sox = Transformer()
        sox.highpass(100)
        sox.lowpass(10000)
        sox.compand(0.005, 0.12, 6, [
            (-90,-90),
            (-70,-55),
            (-50,-35),
            (-32,-32),
            (-24,-24),
            (0,-8),
        ])
        sox.equalizer(3000, 1000, 3)
        sox.equalizer(280, 120, 3)
        sox.build(temp_file.path, output_file)


def tag(input_file, metadata):
    try:
        audio = EasyID3(input_file)
    except ID3NoHeaderError:
        # If file does not currently have an id3 header
        # then create one.
        audio = File(input_file, easy=True)
        audio.add_tags()

    audio['title'] = metadata['title']
    audio['artist'] = metadata['artist']
    audio['album'] = metadata['album']
    audio.save()


class TempFile:
    def __init__(self, prefix=None):
        self.fd, self.path = mkstemp(prefix)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        os.close(self.fd)
        os.remove(self.path)

class SimpleTimer:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = timeit.default_timer()
        return self

    def __exit__(self, type, value, traceback):
        time = timeit.default_timer() - self.start
        time = round(time, 1)
        print('{0} in {1}s'.format(self.name, time))


def _args():
    input_csv = None
    output_dir = None

    try:
        opts, args = getopt.gnu_getopt(
            sys.argv[1:],
            'o:h',
            ['output-dir=', 'help']
        )
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(1)

    for option, value in opts:
        if option in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        elif option in ('-o', '--output-dir'):
            output_dir = value

    if output_dir and not os.path.isdir(output_dir):
        print_error('{} is not a valid output dir'.format(output_dir))
        sys.exit(1)

    if args:
        input_csv = args[0]
    else:
        print_error('You must provide an input path')
        sys.exit(1)

    if not input_csv or not os.path.isfile(input_csv):
        print_error('{} is not a valid input file'.format(input_csv))
        sys.exit(1)

    return input_csv, output_dir


if __name__ == '__main__':
    input_csv, output_dir = _args()
    metadata_list = MetadataList()
    metadata_list.read_from_csv(input_csv)
    process_audio(metadata_list, output_dir)
