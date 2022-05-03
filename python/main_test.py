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
import sys
from main import check_fs_constraints
from main import cs_to_firestore
from main import get_file
from main import set_document
from main import get_parameters_from_filename
from mock_test import Db
from mock_test import Storage
import pandas as pd
import pytest

# set variables to be used in testing
test_filename = 'filetest[collection=test][key=product_id].csv'
collection_id = 'test'
key_column = 'product_id'
os.environ['COLLECTION_ID'] = collection_id
os.environ['KEY_COLUMN'] = key_column
firestore_path_global = {
          "collection_id": collection_id,
          "document_id": key_column
          }


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
  # set variables for testing
  timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
  firestore_path = {
          "collection_id": 'test',
          "document_id": 'product_id'
          }
  db = Db()
  batch = db.batch()
  product_id = 16383
  record = {'test': timestamp, 'product_id': product_id}
  # Test if valid record is accepted by set_document function
  assert set_document(record, db, batch, timestamp, firestore_path)
  batch.commit()
  # Test if calling the record from firestore returns the same record as send.
  assert db.collection('test').document(product_id).get().to_dict() == record
  # Test if record with invalid document_id is rejected.
  record = {'test': timestamp, 'product_id': '.'}
  assert not set_document(record, db, batch, timestamp, firestore_path)
  # Test if incorrect document id prints expected message.
  # Redirect sdtout.
  capturedoutput = io.StringIO()
  sys.stdout = capturedoutput
  set_document(record, db, batch, timestamp, firestore_path)
  # Reset stdout
  sys.stdout = sys.__stdout__
  assert """Failed to update record with document id: [.] """ in (
      capturedoutput.getvalue())
  del capturedoutput


def test_get_file():
  bucket = Storage()
  # Send csv to cloud storage annd retrieve the file to verify
  # if it is equal.
  in_df = pd.read_csv(get_file(bucket, test_filename), dtype=object)
  bucket.blob(test_filename).delete()
  assert in_df.equals(pd.read_csv(test_filename, dtype=object))


def compare_in_and_out_data_fs(trigger_event, df, exclude_doc_id):
  db = Db()
  storage = Storage()
  cs_to_firestore(trigger_event, storage, db, firestore_path_global)
  for index, row in df.iterrows():
    data = row.to_dict()
    out_data = db.collection(firestore_path_global['collection_id']).document(
        data[firestore_path_global['document_id']]).get().to_dict()
    if exclude_doc_id:
      del data[firestore_path_global['document_id']]
    del out_data['timestamp']
    # check if data returned from firestore matches the data that was inserted
    assert data == out_data


def test_cs_to_firestore():
  db = Db()
  storage = Storage()
  # Read test csv to dataframe.
  df = pd.read_csv(test_filename)
  trigger_event = {'name': test_filename, 'bucket': 'test'}
  # Send random file to firestore and retrieve it to verify if the returned data
  # is equal. Check if EXCLUDE_DOCUMENT_ID_VALUE is properly applied to data.
  os.environ['EXCLUDE_DOCUMENT_ID_VALUE'] = 'TRUE'
  compare_in_and_out_data_fs(trigger_event, df, True)
  os.environ['EXCLUDE_DOCUMENT_ID_VALUE'] = 'FALSE'
  compare_in_and_out_data_fs(trigger_event, df, False)



def assert_filename_parameters(filename, exp_collection_id, exp_document_id):
  parameters = get_parameters_from_filename(filename)
  assert exp_collection_id == parameters['collection_id']
  assert exp_document_id == parameters['document_id']


def test_get_parameters_from_filename():
  assert_filename_parameters(
      'data_from_march[collection=test][key=product_id].csv', 'test',
      'product_id')
  assert_filename_parameters('data_from_march[collection=test3].csv', 'test3',
                             None)
  assert_filename_parameters('key=[data}[collection=test3].csv', 'test3', None)

  # test if missing collection id raises expected ValueError
  with pytest.raises(ValueError):
    get_parameters_from_filename('file_without_collection_id.csv')

