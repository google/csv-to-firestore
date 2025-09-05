# CSV to Firestore

The CSV to Firestore solution takes a CSV file from a Cloud Storage bucket, parses it and sends it to Firestore. The solution is automatically triggered when a new file is uploaded in the Cloud Storage bucket. In order to serve a variety of applications, the solution allows you to (1) select which cloud bucket to use, (2) specify to which collection to send the data and (3) if you want to use a specific column as document id.

## Parsing Example

CSV file with id as document id:

```
id, product_name, price_usd
1,television,399
2,water bottle,15
3,glass mug,5
```

Data in Firestore:

![Screenshot of data in Firestore](./firestore_example_screenshot.png)

## Deployment

The cloud function requires the collection id the be specified in the filename
as the following: "filename[collection=YOUR_COLLECTION_ID].csv".
Optionally it is also possible to add the following options:
  - "[key=YOUR_COLUMN_FOR_DOCUMENT_ID]" to specify which column to use for the document
  id. If no column is specified, Firestore will create a random id.
  - "[database=YOUR_DATABASE_NAME]" to specify which database to use, if you're not using
  the default one.

Retrieve the repository by running the following command:

``` git clone https://github.com/Google/csv-to-firestore ```

Complete and run the following command to deploy the cloud function.

```console
gcloud functions deploy csv_to_firestore \
  --runtime python312 \
  --region YOUR_CLOUD_FUNCTION_REGION \
  --trigger-resource YOUR_TRIGGER_BUCKET_NAME \
  --trigger-event google.storage.object.finalize \
  --trigger-location LOCATION_OF_YOUR_DATABASE \
  --entry-point csv_to_firestore_trigger \
  --source PATH_TO_SOURCE_CODE \
  --memory=1024MB \
  --set-env-vars=UPLOAD_HISTORY=TRUE/FALSE,EXCLUDE_DOCUMENT_ID_VALUE=TRUE/FALSE \
  --timeout=540
```

Complete the following parameters in the command:
1. YOUR_CLOUD_FUNCTION_REGION: The region where your cloud function will be hosted. Ideally, it should be located in the same region as your database. A list of all available locations is available in the [Google Cloud help pages](https://cloud.google.com/run/docs/locations).
2. YOUR_TRIGGER_BUCKET_NAME: The path of the cloud storage bucket that triggers the cloud function.
3. LOCATION_OF_YOUR_DATABASE: The location of your Firestore database. This is required if you are using a regionalized Firestore database.
4. PATH_TO_SOURCE_CODE: The path to the folder that contains main.py and requirements.txt ( use . for the current directory )
5. UPLOAD_HISTORY: TRUE or FALSE depending on if you want to create a separate collection that keeps file upload history.
6. EXCLUDE_DOCUMENT_ID_VALUE: TRUE or FALSE. When a document id is specified in the filename the solution stores a value, such as "id" in both the document id and the data in this document. If this is not desired, set this EXCLUDE_DOCUMENT_ID_VALUE to TRUE so that it is only stored as a document id
7. Optionally you can specify the region or other parameters, see documentation here: https://cloud.google.com/sdk/gcloud/reference/functions/deploy

**Note:** After deploying the Cloud Function the logs might display a "OpenBLAS
WARNING". This is the result of some of the used packages and does not influence the functionality of the Cloud Function.

### Permissions
Give the service account that the Cloud Function is running with the following
permissions:
- roles/datastore.user
- roles/storage.objectViewer
- roles/storage.insightsCollectorService
- roles/iam.serviceAccountTokenCreator
- roles/eventarc.eventReceiver
- roles/pubsub.publisher

### Deploying BQ Export to Firestore
If you have your data on BigQuery and want to set up an automated workflow to export this table to Firestore you
can follow the following instructions.

1. Install [Terraform](https://www.terraform.io/downloads)
2. Set up the variables for terraform in the `example.tfvars` file. See `variables.tf` for description of each
 variable.
3. Run: `terraform init` from the terraform directory
4. Run: `terraform plan -var-file="example.tfvars"` to see the planned changes
5. Run: `terraform apply -var-file="example.tfvars"` to deploy the Cloud Function and set up the workflow.
6. (optional) If you want to maintain your Terraform state on GCP instead of locally; navigate to the backend.tf file and uncomment the resource. Fill in the bucket name "resource.google_storage_bucket.backend" and run terraform init to sync terraform with GCS rather than local state saving and recovery.

#### Guided tutorial for deployment
[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/google/csv-to-firestore&cloudshell_open_in_editor=example.tfvars&cloudshell_workspace=terraform%2F&cloudshell_tutorial=tutorial.md&ephemeral=true)

### Disclaimer
This is not an officially supported Google product. Please be aware that bugs may lurk, and that we reserve the right to make small backwards-incompatible changes. Feel free to open bugs or feature requests, or contribute directly (see CONTRIBUTING.md for details).