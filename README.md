# Identifying music in audio files and streams on AWS
This repo contains sample code that accompanies the blog post [Identifying music in audio files and streams on AWS](https://aws.amazon.com/blogs/media/identifying-music-in-audio-files-and-streams-on-aws/).

This repo includes an AWS SAM template that will create all of the required infrastructure needed, including an S3 bucket, a Lambda function with an EventBridge mechanism to run the Lambda when new files are added to the S3 bucket, an Aurora Serverless v2 database to store the data needed to identify songs, and other elements like an SNS notification topic and SQS queue for notifications.

The code demonstrates how you can "fingerprint" your songs, and then detect the presence of your songs in either stored audio files like MP3s, or within streaming media. The underlying idea is to convert audio data into a spectrogram, and then isolate important markers within the spectrogram that will allow us to identify music. Roughly 10000 to 25000 fingerprints will be created for an average length song.  Each fingerprint is stored as a large integer.  See the blog post for more details about how the system works.

The fingerprinting algorithm used is based on the open source solution found at [this Github repo](https://github.com/notexactlyawe/abracadabra).  That solution (and this one) has an MIT license.

Following is an overview of the architecture that will be used for running the solution, focused on ingestion of known songs and detection of songs in media streams (using Elemental MediaLive).

![Architecture Diagram](architecture.png)

## Requirements

You'll need AWS SAM, Docker, and the AWS CLI installed in order to deploy the project.

[SAM Installation instructions](https://aws.amazon.com/serverless/sam/)

[AWS CLI Installation instructions](https://aws.amazon.com/cli/)

[Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)

## Organization

| File | Purpose |
| --- | --- |
| `template.yml` | This AWS SAM template creates all of the required infrastructure, including an S3 bucket, Lambda functions, an SNS topic, and an SQS queue. |
| `src/file_processor/check_for_song_in_file.py` | Code that copies a file from the S3 bucket to local (temporary) storage so the Lambda function can read it and check for the presence of known songs |
| `src/file_processor/check_for_song_in_stream.py` | Code that copies a file from the S3 bucket to local (temporary) storage so the Lambda function can read it and check for the presence of known songs.  This is designed to read in files that were extracted from an Elemental MediaLive stream.  This process is described below in detail. |
| `src/file_processor/cmtimer.py` | A utility class that measures the time taken by different operations. |
| `src/file_processor/db_utils.py` | Utility functions to read and write data in RDB (Aurora Serverless v2 using PostgreSQL) |
| `src/Dockerfile` | The Dockerfile used to create a Docker image for the Lambda function |
| `src/file_processor/fingerprinting_config.py` | Constant values that can be used to tune the fingerprinting process. |
| `src/file_processor/fingerprinting.py` | The main code to read in an audio file, convert it to a spectrogram, then extract fingerprints from that spectrogram. |
| `src/file_processor/main.py` | Entry point for the Lambda function. |
| `src/file_processor/matching.py` | Code to find the best match, based on fingerprints. |
| `src/file_processor/requirements.txt` | Lists all open source dependencies for the Lambda function. |
| `src/file_processor/s3_utils.py` | Utilities to read and write data and files to/from S3.. |
| `src/file_processor/song_indexing.py` | Code to read in the "known" songs a user has, fingerprinting them and storing those fingerprints in the database. |
| `src/file_processor/validation_utils.py` | Utility class to check if a valid type of music file is being used. |

## Building and Deploying the application

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing serverless applications. It uses Docker to run your Lambda functions in an Amazon Linux environment.

To build and deploy your application for the first time, run the following in your shell:

```bash
sam build --use-container
sam deploy --guided
```

The first command will build the source of your application. The second command will package and deploy your application to AWS, with a series of prompts.

Note that if you save your SAM settings for the project in the `samconfig.toml` file during a guided deployment, the second command can be shortened to `sam deploy` in subsequent deploys, which will use your saved settings.

## Checking for Known Songs in a Stored File
You can check MP3s and other audio files by placing them into the S3 bucket, under the `songs_to_check` folder.  This will result in a report file being generated (JSON format), which is written into the S3 bucket in the same folder as the original music file.

## Checking for Known Songs in a Media Stream
This solution leverages the use of Elemental MediaLive in order to monitor songs on a media stream.  MediaLive can be used in many ways.  For this project, we'll use its archiving ability, which will result in stored audio files for every 12 seconds of data that flows through the stream.  12 seconds is sufficient time to correctly identify most songs, and is short enough to ensure good responsiveness in stream-based detection.

To create a stream, use the AWS Console and navigate to the Elemental MediaLive service.  Then follow these directions:

1. Set up your channel input first by clicking on the `Inputs` menu item on the left, and then on the `Create input` button.  You can use a stream as input, or even an MP4 file that resides in an S3 bucket.  This approach is especially useful for testing this solution.
2. Now that your channel input is defined, click on the `Channels` menu item on the left, and then on the `Create channel` button.  Enter a name for the channel.
3. Change the channel class to `single_pipeline`
4. Click on Add by `Input attachments` on the left side, then choose the input you set up in Step 1.  Click on `Confirm`.
5. Click on Add by `Output groups` and choose `Archive` as the type.  Click on `Confirm`.
6. Under `Archive group destination A`, enter the following in the URL: `s3ssl://SONG_DETECTION_S3_BUCKET_NAME/songs_to_check/streams/stream1`.  Be sure to replace `SONG_DETECTION_S3_BUCKET_NAME` with the name of the bucket that was created.  You can change the name of the stream from `stream1` (at the very end) to another name if you wish.  The stream name will be included as part of the output, so if you monitor multiple streams at once, be sure they all have informative names.
7. Under `Archive Settings`, open the `Additional settings` region and enter `12` for `Rollover interval`.  This means every 12 seconds, a file will be written to S3.
8. Click on the Output item under the `Archive` group under Output groups, and then select the audio 1 stream.
9. In the audio stream, choose `AAC` as the codec. Open the `Codec Configuration` under that and change `Sample Rate` to `44100`.  The Lambda code will resample the data to 44100 if it needs to, which means that setting that here removes an extra resampling step.
10. Click on the `Create channel` button on the left

These steps will create a channel that accepts the input stream and writes out media files (both audio and video) every 12 seconds of the stream.  The Lambda function described above will read in only the audio data in order to do song fingerprinting.

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used a name of 'song-detection' for the stack name, you can run the following:

```bash
sam delete --stack-name song-detection
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
