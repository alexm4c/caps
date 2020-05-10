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
#   3b. cut audio into segments and reattach with crossface
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

from tempfile import mkstemp
from sox import Transformer, Combiner
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen import File


def cut(input_file, output_file, segments):
    
    files = [ mkstemp('.mp3') for segment in segments ]

    for index, segment in enumerate(segments):
        sox = Transformer()
        sox.channels(1)
        sox.highpass(100)
        sox.lowpass(10000)
        sox.trim(*segment)
        sox.fade(1, 2, 't')
        sox.build(input_file, files[index][1])

    Combiner().build([ file[1] for file in files ], output_file, 'concatenate')

    for file in files:
        os.close(file[0])
        os.remove(file[1])



def optimise(input_file, output_file):
    sox = Transformer()
    sox.norm(-24)
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
    sox.build(input_file, output_file)


def cut_optimise(input_file, output_file, segments):
    try:
        temp_file1 = mkstemp('.mp3')
        temp_file2 = mkstemp('.mp3')

        cut(input_file, temp_file1[1], segments)
        optimise(temp_file1[1], temp_file2[1])

        subprocess.run(['cp', temp_file2[1], output_file])

    except Exception as e:
        print(e)
        sys.exit(1)

    finally:
        os.close(temp_file1[0])
        os.remove(temp_file1[1])
        os.close(temp_file2[0])
        os.remove(temp_file2[1])

    return output_file



def tag(input_file):
    try:
       audio = EasyID3(input_file)
    except ID3NoHeaderError:
       audio = File(input_file, easy=True)
       audio.add_tags()

    audio["title"] = "Some Title"
    audio["artist"] = "Speaker 1,Speaker 2,Speaker 3"
    audio["album"] = "Socialism 2019"
    audio.save()


if __name__ == '__main__':

    # Silence PySox warnings and info
    logging.getLogger('sox').setLevel(logging.ERROR)
    
    start = timeit.default_timer()    
    
    input_file = "sadia.mp3"
    output_file = "sadia_processed.mp3"

    cut_optimise(
        input_file,
        output_file,
        segments = [
            (0, 5),
            (10, 15),
            (20, 25),
        ],
    )
    tag(output_file)
  
    stop = timeit.default_timer()
    print('finished in : ', end='')
    print(stop - start)
