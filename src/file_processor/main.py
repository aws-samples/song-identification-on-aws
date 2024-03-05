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
import json
from song_indexing import get_fingerprints_and_store
from check_for_song_in_file import identify_song_in_file
from check_for_song_in_stream import identify_song_in_stream

INDEX_FOLDER = "songs_to_index"
CHECK_FOLDER = "songs_to_check"
STREAM_CHECK_FOLDER = "songs_to_check/streams/"


def lambda_handler(event, context):

    # print("Received event: " + json.dumps(event, indent=2))
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']

    fname = key.lower()
    if fname.startswith(STREAM_CHECK_FOLDER):

        # get the stream name from the key
        stream_name = key.replace(STREAM_CHECK_FOLDER, '')
        identify_song_in_stream(stream_name, bucket, key)
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully checked stream in {key} in bucket {bucket}')
        }

    elif fname.startswith(CHECK_FOLDER):

        identify_song_in_file(bucket, key)
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully checked file {key} in bucket {bucket}')
        }

    elif fname.startswith(INDEX_FOLDER):

        get_fingerprints_and_store(bucket, key)
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successful fingerprinting of {key} in bucket {bucket}')
        }

    else:
        return {
            'statusCode': 400,  # bad request
            'body': json.dumps(f'Files must be in either the {CHECK_FOLDER} or {INDEX_FOLDER} folders')
        }
