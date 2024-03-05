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
import json
from db_utils import create_tables_if_needed, get_db_matches_for_fingerprints
from s3_utils import download_from_s3_to_local, send_text_to_s3
from fingerprinting import get_fingerprints
from matching import get_best_match
from validation_utils import is_music_file


def identify_song_in_file(bucket, key):
    # used for checking individual files dropped into the S3 folder.
    # this creates fingerprints for this file, then looks in the DB
    # for matches.

    # ignore any files we can't process
    if not is_music_file(key):
        print(f'Skipping {key} as it is not a music file')
        return

    local_fname = download_from_s3_to_local(bucket, key)

    create_tables_if_needed()

    fingerprints = get_fingerprints(local_fname)
    matches = get_db_matches_for_fingerprints(fingerprints)
    best_match_song_id, score = get_best_match(matches)

    print(f'Best match for {key} is {best_match_song_id} with score {score}')

    report_data = json.dumps({
        "song": best_match_song_id,
        "score": int(score)
        })

    # create a report and upload to S3
    pathinfo = pathlib.PurePath(key)
    folder = pathinfo.parent.as_posix()
    songid = pathinfo.stem
    report_name = f'{folder}/{songid}.json'
    print(f'Writing report {report_name} to {bucket}')
    send_text_to_s3(bucket, report_name, report_data)
