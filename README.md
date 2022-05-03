## Deploy

The cloud function requires the collection id the be specified in the filename
as the following: "filename[collection=YOUR_COLLECTION_ID].csv" Optionally it is
also possible to add [key=YOUR_COLUMN_FOR_DOCUMENT_ID] to the filename to
specify which column to use for the document id. If no column is specified,
firestore will create a random id.

Run the following command to deploy the cloud function. Fill in: 1. The name of
the bucket that triggers the cloud function 2. The path to the folder that
contains main.py and requirements.txt ( use . for the current directory ) 3.
TRUE or FALSE for UPLOAD_HISTORY depending on if you want to create a separate
collection that keeps file upload history. 4. TRUE or FALSE for
EXCLUDE_DOCUMENT_ID_VALUE. When a document id is specified in the filename the
solution stores a value, such as "id" in both the document id and the data in
this document. If this is not desired, set this EXCLUDE_DOCUMENT_ID_VALUE to
TRUE so that it is only stored as a document id. 5. Optionally you can specify
the region or other parameters, see documentation here:
https://cloud.google.com/sdk/gcloud/reference/functions/deploy

```console
gcloud functions deploy cs_to_firestore \
  --runtime python39 \
  --trigger-resource YOUR_TRIGGER_BUCKET_NAME \
  --trigger-event google.storage.object.finalize \
  --entry-point cs_to_firestore_trigger \
  --source PATH_TO_SOURCE_CODE \
  --memory=1024MB \
  --set-env-vars=UPLOAD_HISTORY=TRUE/FALSE,EXCLUDE_DOCUMENT_ID_VALUE=TRUE/FALSE \
  --timeout=540
```

Note: After deploying the Cloud Function the logs might display a "OpenBLAS
WARNING". This is the result of some of the used packages and does not influence
the functionality of the Cloud Function.
