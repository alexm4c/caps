# PAPS - Python Audio Processing System

I've written these python scripts to help tag and optimise raw audio 
recordings of lectures, etc.

## Dependencies

These scripts were written for python3

Additionally, you will need vlc and sox installed on your machine.

### VLC

VLC is used to preview the raw audio so you can determine at which
timestamps it should be cut.

	sudo apt install vlc

### sox

Sox is the fastest audio processing software I could find. We intend to
process many, potentially large audio files, so speed is critical.

	sudo apt install sox libsox-fmt-mp3

## Installation

	pip install -r requirements.txt

## Usage

There are two main modules: `collect.py` and `process.py`

### Collect

	python collect.py path/to/audio/dir

`collect.py` will prompt you to describe the audio metadata: title, 
speakers, and audio segments to cut.

### Process

	python process.py collected_metadata.csv

`process.py` will use the output from `collect.py` to cut each audio
file into segments, roughly optimise for voice, converted to MP3 format,
and then finally add metadata with ID3 tags.
