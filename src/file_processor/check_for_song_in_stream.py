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
import os
import boto3
from db_utils import get_db_matches_for_fingerprints, get_last_song_for_stream_from_db, store_song_for_stream_in_db
from s3_utils import download_from_s3_to_local
from fingerprinting import get_fingerprints
from matching import get_best_match
from validation_utils import is_music_file
import json

NO_SONG_DETECTED_TITLE = 'Not Recognized'
SNS_TOPIC = os.getenv('SNSNotificationTopic')
sns_client = boto3.client('sns')


def identify_song_in_stream(stream_name, bucket, key):
    # The stream processor Lambda reads in a certain number of seconds of streaming audio,
    # saves it into an MP3 file on S3.  That trigger this function.

    # this should never happen, but just in case...
    if not is_music_file(key):
        print(f'Skipping {key} in stream processor as it is not a music file')
        return

    local_fname = download_from_s3_to_local(bucket, key)

    fingerprints = get_fingerprints(local_fname)
    matches = get_db_matches_for_fingerprints(fingerprints)
    best_match_song_id, score = get_best_match(matches)
    print(f'Best match song ID for stream data is {best_match_song_id} with score {score}')

    # we get audio from a stream by using a MediaLive channel with Archive output.
    # this means the name of the files will have a fixed prefix and a varying suffix, like:
    #     {nameprefix}_{namemodifier}.{number}.ts
    # we split on the _ character, so the name prefix (the first part) is the identifier
    # of the stream itself
    stream_name = stream_name.split('_')[0]

    # now look in the database for the last song encountered in this stream
    last_song_for_stream = get_last_song_for_stream_from_db(stream_name)
    print(f'Last song for stream {stream_name} is {last_song_for_stream}')

    # last_song_for_stream is None if there is no song in the database yet for this stream
    if last_song_for_stream is None:
        # no matches, so store a string indicating that fact (since this is the first entry for this stream)
        if best_match_song_id is None:
            print(f'No song detected in stream {stream_name} yet')
            best_match_song_id = NO_SONG_DETECTED_TITLE

    # whether we have a song in the database or not, check if it differs
    if last_song_for_stream != best_match_song_id:
        # 1. save the current song in the database table that tracks songs by stream
        print(f'New song detected in stream {stream_name}: ID: {best_match_song_id}, Score: {score}')
        store_song_for_stream_in_db(stream_name, best_match_song_id)

        # 2. send an SNS notification about the newly detected song
        info = {
            "stream": stream_name,
            "song": best_match_song_id,
            "score": score
        }
        response = sns_client.publish(TopicArn=SNS_TOPIC, Message=json.dumps(info))
        print(f'SNS notification returned {json.dumps(response, indent=5)}')
