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

import datetime
import io
import os
import re

import pandas as pd
from google.cloud import firestore
from google.cloud import storage

StringIO = io.StringIO
datetime = datetime.datetime

class Config:
  def __init__(self):
    self.id = os.getenv('COLLECTION_ID')
    self.key_column = os.getenv('KEY_COLUMN')

def cs_to_firestore_trigger(event, context):
  """Triggered by cloud storage file upload, initializes client and start file 
  processing.

  Function is run whenever the cloud function is triggered by a new file 
  in the cloud storage bucked. Function initials a cloud storage and firestore
  client whom are forwared to cs_to_firestore that will process the file.

  Args:
    event: event object from trigger containing information on the location of
      the trigger file.
    context: context object from trigger.

  Returns:
    None
  """
  storage_client, db = storage.Client(), firestore.Client()
  cs_to_firestore(event, storage_client, db)


def cs_to_firestore(event, storage_client, db):
  """Triggered by cs_to_firestore_trigger process and send file to Firestore.

  function is triggered by s_to_firestore_trigger receiving path to cs file
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

  Returns:
    None
  """
  print('started processing file' + event['name'])
  csv_file = get_file(storage_client.get_bucket(event['bucket']), event['name'])

  chunk_size = 500
  row_counter = 0
  failed_records_counter = 0
  with pd.read_csv(csv_file, chunksize=chunk_size) as reader:
    for chunk in reader:
      chunk_timestamp_utc = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
      data_dict = chunk.to_dict(orient='records')
      # initialize batch for upload
      batch = db.batch()
      for record in data_dict:
        if set_document(record, db, batch, chunk_timestamp_utc):
          row_counter += 1
        else:
          failed_records_counter += 1
      batch.commit()

  # add document to firestore to record the processed file
  timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
  document_id = (event['name'] + '_' + timestamp)
  db.collection(Config().id + '_upload_history').document(document_id).set({
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

  Based on the storage_client the function retrieves the file with the
  specified name from cloud storage. Download the file as a string and
  decodes it so that it can later be read in pandas.

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


def set_document(record, db, batch, timestamp):
  """Constructs and sets firestore documenent in batch based on record.

  Receives a record that will be inserted into a firestore document that is
  added to the current batch.

  Args:
    record: an individual dictionary item containing all data that has to send
      to firestore
    db: firestore client
    batch: batch where the record will be set

  Returns:
    None
  """
  document_id = str(record[Config().key_column])
  if check_fs_constraints(document_id) is None:
    print(f"""Failed to update record with document id: [{document_id}] due to
incorrect string format. See firestore documentation
https://firebase.google.com/docs/firestore/quotas""")
    return False
  record['timestamp'] = timestamp
  del record[Config().key_column]
  data_path_and_id = db.collection(Config().id).document(document_id)
  batch.set(data_path_and_id, record)
  return True


def check_fs_constraints(document_id_str):
  """Verifies of document id matches firestore constraints.

  Receives a string that will be matched to a regular expression. If string
  matches it violates the constraints and returns None.

  Args:
    document_id_str: document id string
  Returns:
    pattern.match(document_id_str): Can be either None or True.
  """
  pattern = re.compile('^(?!\.\.?$)(?!.*__.*__)([^/]{1,1500})$')
  return pattern.match(document_id_str)
