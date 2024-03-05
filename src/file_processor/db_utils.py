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
from boto3.session import Session
import os
from collections import defaultdict


session = Session()
rds_data = session.client(service_name='rds-data')
DBClusterArn = os.environ['DBClusterArn']
DBName = os.environ['DBName']
SecretArn = os.environ['SecretArn']


def create_tables_if_needed():
    cmd = "CREATE TABLE IF NOT EXISTS fingerprints " \
        "(id SERIAL PRIMARY KEY, songid VARCHAR(128), hash bigint, timestep INT);"
    run_command(cmd)

    cmd = "CREATE INDEX IF NOT EXISTS hash_index on fingerprints (hash);"
    run_command(cmd)

    cmd = "CREATE TABLE IF NOT EXISTS streams " \
        "(streamid VARCHAR(128) PRIMARY KEY, songid VARCHAR(128));"
    run_command(cmd)

    cmd = "CREATE INDEX IF NOT EXISTS stream_index on streams (streamid);"
    run_command(cmd)


def run_command(sql_statement):
    # Use the Data API ExecuteStatement operation to run the SQL command
    result = rds_data.execute_statement(
        resourceArn=DBClusterArn,
        secretArn=SecretArn,
        database=DBName,
        sql=sql_statement
    )
    return result


def store_fingerprints_to_db(songid, file_fingerprints):
    # need a table to store them
    create_tables_if_needed()

    # a song might have 25,000 fingerprints, so we need to be careful about the string length
    # therefore, we batch these inserts into SQL commands roughly 64KB long (the max allowed)
    vals = []
    batches_done = 0
    for hash, timeindex in file_fingerprints:
        vals.append(f"('{songid}', {hash}, {timeindex})")
        joined_string = ','.join(vals)
        if len(joined_string) >= 64000:
            sql = f"INSERT INTO fingerprints (songid, hash, timestep) VALUES {joined_string};"
            # print(f'SQL command to insert fingerprints is {len(sql)} chars long')
            # print(f'Initial chars: {sql[0:300]}')
            run_command(sql)
            vals = []
            batches_done += 1

    # get any of the leftovers
    if len(vals) > 0:
        sql = f"INSERT INTO fingerprints (songid, hash, timestep) VALUES {','.join(vals)};"
        print(f'Final SQL command to insert fingerprints is {len(sql)} chars long')
        run_command(sql)
        batches_done += 1
    print(f'{batches_done} INSERTs issued')


def get_db_matches_for_fingerprints(fingerprints):
    # make sure we have a table to select from
    create_tables_if_needed()

    # first, retrieve all matching hashes
    prefix = "SELECT songid, hash, timestep FROM fingerprints WHERE hash in "
    # we need to break this into possibly multiple selects, in order to keep the total length
    # of the query less than 64K
    result_rows = []
    hashes_for_select = []
    batches_done = 0

    hashes_to_find = [h for h, _ in fingerprints]
    # get rid of dupes
    hashes_to_find = list(set(hashes_to_find))
    print(f'Searching in DB for matching for {len(hashes_to_find)} fingerprints')

    for hash in hashes_to_find:

        hashes_for_select.append(str(hash))
        sql = f"{prefix} ({','.join(hashes_for_select)});"
        if len(sql) >= 64000:
            print(f'SQL command to get matches is {len(sql)} chars long, starting chars: {sql[0:300]}')
            result = run_command(sql)
            result_rows.extend(result['records'])
            print(f'{len(result_rows)} rows of results so far ')

            hashes_for_select = []
            batches_done += 1

    # get any of the leftovers once we drop out of the loop
    if len(hashes_for_select) > 0:
        sql = f"{prefix} ({','.join(hashes_for_select)});"
        print(f'SQL command to get matches is {len(sql)} chars long, starting chars: {sql[0:300]}')
        result = run_command(sql)
        result_rows.extend(result['records'])
        print(f'{len(result_rows)} rows of results so far ')
        batches_done += 1

    # finish any leftovers
    print(f'{batches_done} SELECTs issued, {len(result_rows)} total rows returned')

    # now refactor the results into a list we can use
    # the first step is to map the fingerprints we are searching for to their timesteps
    timesteps_by_hash = {}
    for h, t in fingerprints:
        timesteps_by_hash[h] = t

    # and then use that mapping as part of the returned data
    results = defaultdict(list)
    for row in result_rows:
        songid = row[0]['stringValue']
        search_for_hash = row[1]['longValue']
        timestep = row[2]['longValue']
        results[songid].append((timestep, timesteps_by_hash[search_for_hash]))

    return results


def get_last_song_for_stream_from_db(streamid):
    # make sure we have a table to select from
    create_tables_if_needed()

    sql = f"SELECT songid FROM streams WHERE streamid = '{streamid}';"
    result = run_command(sql)
    if len(result['records']) == 0:
        return None
    else:
        return result['records'][0][0]['stringValue']


def store_song_for_stream_in_db(streamid, songid):
    # make sure we have a table to select from
    create_tables_if_needed()

    sql = f"INSERT INTO streams (streamid, songid) VALUES ('{streamid}', '{songid}') " \
          f"ON CONFLICT (streamid) DO UPDATE SET songid = '{songid}';"
    run_command(sql)
