"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import pathlib
from db_utils import store_fingerprints_to_db
from s3_utils import download_from_s3_to_local
from fingerprinting import get_fingerprints
from validation_utils import is_music_file


def get_fingerprints_and_store(bucket, key):

    # silently ignore any files we can't process
    if not is_music_file(key):
        return

    local_fname = download_from_s3_to_local(bucket, key)

    # get the name of the file (sans extention) as the ID, and
    # create fingerprints for song and store to DB
    pathinfo = pathlib.PurePath(key)
    songid = pathinfo.stem
    file_fingerprints = get_fingerprints(local_fname)

    print(f'{songid} has {len(file_fingerprints)} fingerprints')

    store_fingerprints_to_db(songid, file_fingerprints)
