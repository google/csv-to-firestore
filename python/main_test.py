import datetime
import io
import os
import sys
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

from main import check_fs_constraints
from main import cs_to_firestore
from main import get_file
from main import set_document
from mock_test import Db
from mock_test import Storage
import pandas as pd


collection_id = 'test'
key_column = 'product_id'
os.environ['COLLECTION_ID'] = collection_id
os.environ['KEY_COLUMN'] = key_column


def test_valid_fs_constraints():
  # Test if valid document id's are accepted.
  assert check_fs_constraints('543634') is not None
  assert check_fs_constraints('asdfhj') is not None
  assert check_fs_constraints('327h281hd82!#*@') is not None


def test_violating_fs_constraints():
  # Test string that violates 1500 bytes limit.
  test_string = ''
  for i in range(0, 1505):
    test_string += 'a'
  assert check_fs_constraints(test_string) is None
  # Test various firestore constraints.
  assert check_fs_constraints('..') is None
  assert check_fs_constraints('.') is None
  assert check_fs_constraints('/') is None
  assert check_fs_constraints('dfgh/fdghdfg') is None


def test_set_document():
  timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
  product_id = 16383
  db = Db()
  batch = db.batch()
  record = {'test': timestamp, 'product_id': product_id}
  # Test if valid record is accepted by set_document function
  assert set_document(record, db, batch, timestamp)
  batch.commit()
  # Test if calling the record from firestore returns the same record as send.
  assert db.collection('test').document(product_id).get().to_dict() == record
  # Test if record with invalid document_id is rejected.
  record['product_id'] = '.'
  assert not set_document(record, db, batch, timestamp)
  # Test if incorrect document id prints expected message.
  # Redirect sdtout.
  capturedoutput = io.StringIO()
  sys.stdout = capturedoutput
  set_document(record, db, batch, timestamp)
  # Reset stdout
  sys.stdout = sys.__stdout__
  assert """Failed to update record with document id: [.] """ in (
      capturedoutput.getvalue())
  del capturedoutput


def test_get_file():
  bucket = Storage()
  # Send csv to cloud storage annd retrieve the file to verify
  # if it is equal.
  in_df = pd.read_csv(get_file(bucket, 'test.csv'), dtype=object)
  bucket.blob('test.csv').delete()
  assert in_df.equals(pd.read_csv('test.csv', dtype=object))


def test_cs_to_firestore():
  db = Db()
  storage = Storage()
  # Read test.csv to dataframe.
  df = pd.read_csv('test.csv')
  os.environ['COLLECTION_ID'] = collection_id
  os.environ['KEY_COLUMN'] = key_column

  trigger_event = {'name': 'test.csv', 'bucket': 'test'}
  # Send random file to firestore and retrieve it to verify if the returned data
  # is equal.
  cs_to_firestore(trigger_event, storage, db)
  for index, row in df.iterrows():
    data = row.to_dict()
    document_id = str(data[os.getenv('KEY_COLUMN')])
    del data[os.getenv('KEY_COLUMN')]
    out_data = db.collection(
        os.getenv('COLLECTION_ID')).document(document_id).get().to_dict()
    del out_data['timestamp']
    print(data)
    print(out_data)
    assert data == out_data
