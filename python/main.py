# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# TODO(psnel) run live tests with large amount of data to discover limits

import datetime
import io
import os
import re

from google.cloud import firestore
from google.cloud import storage
import pandas as pd

StringIO = io.StringIO
datetime = datetime.datetime


def cs_to_firestore_trigger(event, context):
  """Triggered by cloud storage file upload, initializes client file processing.

  Executed whenever the cloud function is triggered by a new file
  in the cloud storage bucket. Function initializes a cloud storage and
  firestore client whom are forwarded to cs_to_firestore that will process the
  file.

  Args:
    event: event object from trigger containing information on the location of
      the trigger file.
    context: context object from trigger. (not used)

  Returns:
    None
  """
  firestore_path = get_parameters_from_filename(event['name'])
  storage_client, db = storage.Client(), firestore.Client()
  cs_to_firestore(event, storage_client, db, firestore_path)


def cs_to_firestore(event, storage_client, db, firestore_path):
  """Triggered by cs_to_firestore_trigger process and sends file to Firestore.

  Function is triggered by cs_to_firestore_trigger and receives path to cs file
  and a storage and firestore client. Function:
    1. calls function to read file from cloud storage.
    2. runs through all elements in the file and sends them in batches to
    Firestore.
    3. prints that function was successfully completed for cloud logging.

  Args:
    event: event object from trigger containing information on the location of
      the trigger file.
    storage_client: initialized google cloud storage client object.
    db: initialized firestore client object.
    firestore_path: Tuple containing the collection and document id.

  Returns:
    None
  """
  print('started processing file ' + event['name'])
  csv_file = get_file(storage_client.get_bucket(event['bucket']), event['name'])

  chunk_size = 500  # maximum batch size for API
  row_counter = 0
  failed_records_counter = 0

  # loop through csv and insert rows in batches for firestore
  with pd.read_csv(csv_file, chunksize=chunk_size) as reader:
    for chunk in reader:
      chunk_timestamp_utc = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
      data_dict = chunk.to_dict(orient='records')
      # initialize batch for upload
      batch = db.batch()
      for record in data_dict:
        if set_document(record, db, batch, chunk_timestamp_utc, firestore_path):
          row_counter += 1
        else:
          failed_records_counter += 1
      batch.commit()

  # add document to firestore to record the processed file
  if os.getenv('UPLOAD_HISTORY') != 'FALSE':
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    # concatenate timestamp to filename to create unique document id
    document_id = (event['name'] + '_' + timestamp)
    # sent log to firestore
    db.collection(firestore_path['collection_id'] +
                  '_upload_history').document(document_id).set({
                      'bucket': event['bucket'],
                      'filename': event['name'],
                      'number_of_records': row_counter,
                      'timestamp': timestamp,
                  })

  print(f"""Successfully updated {row_counter} records for {event['bucket']}
with {event['name']}.""")
  if failed_records_counter != 0:
    print(f'{failed_records_counter}records failed to upload, see cloud logs.')


def get_file(bucket, name):
  """Retrieves and parses a file from cloud storage.

  The function retrieves the file with the specified name from cloud storage.
  Downloads the file as a string and decodes it so that it can later be read
  into pandas.

  Args:
    bucket: initialzed storage_client on previously given bucket name.
    name: file name of the file to be retrieved from cloud storage.

  Returns:
    blob: a wrapper around cloud storage object containing the file contents
  """
  blob = bucket.blob(name)
  blob = blob.download_as_bytes()
  blob = blob.decode('utf-8')
  blob = StringIO(blob)
  return blob


def set_document(record, db, batch, timestamp, firestore_path):
  """Constructs and sets firestore documenent in batch based on given record.

  Receives a record that will be inserted into a firestore document that is
  added to the current batch.

  Args:
    record: dictionary item containing the data to be send to firestore
    db: firestore client
    batch: batch where the record will be set
    timestamp: UTC timestamp as string
    firestore_path: Tuple containing the collection and document id (is None
      if not specified).

  Returns:
    False if incorrect document id and True if record was set in batch.
  """
  document_id = firestore_path['document_id']
  # create a key value pair in dictionary containing the current timestamp
  record['timestamp'] = timestamp
  # if document id is specified; check if it meets firestore requirements
  if firestore_path['document_id'] is not None:
    document_id = str(record[firestore_path['document_id']])
    if check_fs_constraints(document_id) is None:
      print(f"""Failed to update record with document id: [{document_id}] due to
  incorrect string format. See firestore documentation
  https://firebase.google.com/docs/firestore/quotas""")
      return False
    if os.getenv('EXCLUDE_DOCUMENT_ID_VALUE') == 'TRUE':  
      del record[firestore_path['document_id']]
  data_path_and_id = db.collection(firestore_path['collection_id']).document(document_id)
  batch.set(data_path_and_id, record)
  return True


def check_fs_constraints(document_id_str):
  """Verifies of document id matches firestore constraints.

  Receives a string that will be matched to a regular expression. Returns None
  if it violates firestore constraints.

  Args:
    document_id_str: document id string

  Returns:
    pattern.match(document_id_str): Can be either None or True.
  """
  pattern = re.compile(r'^(?!\.\.?$)(?!.*__.*__)([^/]{1,1500})$')
  return pattern.match(document_id_str)


def get_parameters_from_filename(filename):
  """Receives a filename and returns the defined collection and document id.

  Receives a filename as string and calls regex_search_string to find
  a specific parameter stated in this string. Returns a tuple containing the
  collection and document id used to store data in firestore.

  Args:
    filename: string filename

  Returns:
    Tuple containing a collection id and the column to be used for document id's
  """
  collection_id = regex_search_string(filename, 'collection')
  document_id = regex_search_string(filename, 'key')
  # raise error if no collection id is found
  if collection_id is None:
    raise ValueError('there was no collection id specified in the filename, ',
    'try adding [collection=your_collection_id]'
    )
  return {
          "collection_id": collection_id,
          "document_id": document_id
          }


def regex_search_string(filename, parameter):
  """Searches parameter in filename.

  Returns none if parameter was not found.

  Args:
    filename: string filename
    parameter: parameter to find in filename such as collection id or key.

  Returns:
    Value specified for the parameter in the filename or None if not found.
  """
  out = re.search(r'\[' + parameter + r'=(.*?)\]', filename)
  if out is None:
    return None
  return out.group().replace('[' + parameter + '=', '').replace(']', '')
