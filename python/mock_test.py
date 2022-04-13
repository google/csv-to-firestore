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
import csv


class Db:

  def __init__(self):
    self.data = {}

  def collection(self, id):
    self.collection_id = str(id)
    return self

  def document(self, id):
    self.document_id = str(id)
    return self

  def get(self):
    return self

  def to_dict(self):
    return self.data[self.collection_id][self.document_id]

  def set(self, data):
    if self.collection_id not in self.data:
      self.data[self.collection_id] = {}
    self.data[self.collection_id][self.document_id] = data

  def batch(self):
    return Batch(self)


class Batch:

  def __init__(self, db):
    self.data = []
    self.batch_db = db

  def set(self, path, record):
    self.data.append({
        'collection': path.collection_id,
        'document': path.document_id,
        'data': record
    })

  def commit(self):
    for i in self.data:
      if i['collection'] not in self.batch_db.data:
        self.batch_db.data[i['collection']] = {}
      self.batch_db.data[i['collection']][i['document']] = i['data']
    self.data = {}


class Storage:

  def __init__(self):
    self.bucket_name = None
    self.file_name = None
    self.data = ''

  def bucket(self, name):
    self.bucket_name = name
    return self

  def blob(self, name):
    self.file_name = name
    return self

  def download_as_bytes(self):
    with open(self.file_name) as csvfile:
      reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
      for row in reader:
        self.data += ','.join(row)
        self.data += '\n'
      csvfile.close()
    return self

  def decode(self, encoding):
    return self.data

  def delete(self):
    del self

  def get_bucket(self, bucket_name):
    self.bucket_name = bucket_name
    return self
