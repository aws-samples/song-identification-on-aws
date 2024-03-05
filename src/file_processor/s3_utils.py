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
from cmtimer import CMtimer
import pathlib
import boto3

s3 = boto3.client('s3')


def download_from_s3_to_local(bucket, key):
    pathinfo = pathlib.PurePath(key)
    local_fname = '/tmp/' + pathinfo.name
    with CMtimer(f"Downloading {key} from bucket {bucket}"):
        s3.download_file(bucket, key, local_fname)
    return local_fname


def send_text_to_s3(bucket, key, text):
    with CMtimer(f"Sending {key} to bucket {bucket}"):
        s3.put_object(Bucket=bucket, Key=key, Body=text)
