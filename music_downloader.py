#!/usr/bin/env python

from __future__ import print_function
import os
import re
import subprocess

from bs4 import BeautifulSoup

# Version compatiblity
import sys
if (sys.version_info > (3, 0)):
    from urllib.request import urlopen
    from urllib.parse import quote_plus as qp
    raw_input = input
else:
    from urllib2 import urlopen
    from urllib import quote_plus as qp


def extract_videos(html):
    """
    Parses given html and returns a list of (Title, Link) for
    every movie found.
    """
    soup = BeautifulSoup(html, 'html.parser')
    pattern = re.compile(r'/watch\?v=')
    found = soup.find_all('a', 'yt-uix-tile-link', href=pattern)
    return [(x.text.encode('utf-8'), x.get('href')) for x in found]


def list_movies(movies):
    for idx, (title, _) in enumerate(movies):
        yield '[{}] {}'.format(idx, title)


def search_videos(query):
    """
    Searchs for videos given a query
    """
    response = urlopen('https://www.youtube.com/results?search_query=' + query)
    return extract_videos(response.read())

def query_and_download(search, has_prompts=True, is_quiet=False):
    """
    Queries the internet for given lyrics and downloads them into the current working directory.
    If has_prompts is False, will download first available song.
    If is_quiet is True, will run beautiful-soup in quiet mode. Prompts will also automatically be turned
                         off in quiet mode. This is mainly so that instantmusic can be run as a background process.

    Returns the title of the video downloaded from.
    """
    if not is_quiet:
        print('Searching...')

    available = search_videos(search)

    if not is_quiet:
        if not available:
            print('No results found matching your query.')
            sys.exit(2) # Indicate failure using the exit code
        else:
            if has_prompts:
                print('Found:', '\n'.join(list_movies(available)))

    # We only ask the user which one they want if prompts are on, of course
    if has_prompts and not is_quiet:
        choice = ''
        while choice.strip() == '':
            choice = raw_input('Pick one: ')
        title, video_link = available[int(choice)]

        # prompt = raw_input('Download "%s"? (y/n) ' % title)
        # if prompt != 'y':
            # sys.exit()
    # Otherwise, just download the first in available list
    else:
        title, video_link = available[0]


    command_tokens = [
        'youtube-dl',
        '--extract-audio',
        '--audio-format',  'mp3',
        '--audio-quality',  '0',
        'http://www.youtube.com/' + video_link]

    if is_quiet:
        command_tokens.insert(1, '-q')

    command = ' '.join(command_tokens)


    # Youtube-dl is a proof that god exists.
    if not is_quiet:
        print('Downloading')
        
    # output = os.system(command)
    output = subprocess.check_output(command_tokens)
    print ( "output was {}".format(output) )
    
    # m = re.search("Decoding of (.*) finished", output)
    m = re.search("Destination: (.*[.]mp3)", output)
    if m:
        fn = m.group(1)
        fnDest = os.path.join("/home/ealfonso/Music/ytdl", os.path.basename(fn))
        subprocess.call(["mv", fn, fnDest])
        subprocess.Popen(["mpg321", fnDest])
    return title

def search_uses_flags(argstring, *flags):
    """
    Check if the given flags are being used in the command line argument string
    """
    for flag in flags:
        if (argstring.find(flag) != 0):
            return True
    return False

def main():
    """
    Run the program session
    """
    argument_string = ' '.join(sys.argv[1:])
    search = ''

    # No command-line arguments
    if not sys.argv[1:]:
        # We do not want to accept empty inputs :)
        while search == '':
            search = raw_input('Enter songname/ lyrics/ artist.. or whatever\n> ')
        search = qp(search)
        downloaded = query_and_download(search)

    # Command-line arguments detected!
    else:
        # No flags at all are specified
        if not search_uses_flags(argument_string, '-s', '-i', '-f', '-p', '-q'):
            search = qp(' '.join(sys.argv[1:]))
            downloaded = query_and_download(search)

        # No input flags are specified
        elif not search_uses_flags(argument_string, '-s', '-i', '-f'):
            # Default to -s
            lyrics = argument_string.replace('-p', '').replace('-q', '')
            search = qp(lyrics)
            downloaded = query_and_download(search, not search_uses_flags('-p'), search_uses_flags('-q'))

        # Some input flags are specified
        elif not search_uses_flags(argument_string, "-L"):
            #just list titles and urls
            query = argument_string.replace('-L', '')
            results = search_videos(qp(" ".join(query)))
            #todo include image thumb
            lines = [u"\t".join(map(lambda x: x.decode("utf8"), line)) for line in results]
            # print ( "hola: {} ".format(len(lines) ))
            # print ( map(type, lines) )
            
            # print ( "\n".join(lines))
            print ( "\n".join((x.encode("utf8") for x in lines)))
            # print ( "hola" )
            
        else:
            # Lots of parser-building fun!
            import argparse
            parser = argparse.ArgumentParser(description='Instantly download any song!')
            parser.add_argument('-p', action='store_false', dest='has_prompt', help="Turn off download prompts")
            parser.add_argument('-q', action='store_true', dest='is_quiet', help="Run in quiet mode. Automatically turns off prompts.")
            parser.add_argument('-s', action='store', dest='song', nargs='+', help='Download a single song.')
            parser.add_argument('-l', action='store', dest='songlist', nargs='+', help='Download a list of songs, with lyrics separated by a comma (e.g. "i tried so hard and got so far, blackbird singing in the dead of night, hey shawty it\'s your birthday).')
            parser.add_argument('-f', action='store', dest='file', nargs='+', help='Download a list of songs from a file input. Each line in the file is considered one song.')

            # Parse and check arguments
            results = parser.parse_args()

            song_list = []
            if results.song:
                song_list.append(qp(' '.join(results.song)))

            if results.songlist:
                songs = ' '.join(results.songlist)
                song_list.extend([qp(song) for song in songs.split(',')])

            if results.file:
                with open(results.file[0], 'r') as f:
                    songs = f.readlines()
                    # strip out any empty lines
                    songs = filter(None, (song.rstrip() for song in songs))
                    # strip out any new lines
                    songs = [qp(song.strip()) for song in songs if song]
                    song_list.extend(songs)

            prompt = True if results.has_prompt else False
            quiet = True if results.is_quiet else False

            downloads = []
            for song in song_list:
                downloads.append(query_and_download(song, prompt, quiet))

            print('Downloaded: %s' % ', '.join(downloads))

            

if __name__ == '__main__':
    main()
