import os
import logging
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
from datetime import timedelta

logging.basicConfig(level=logging.INFO)
BUCKET = os.getenv('GCS_BUCKET')
try:
    storage_client = storage.Client()
except DefaultCredentialsError:
    logging.warning('GCS credentials not found. Set up ADC or GOOGLE_APPLICATION_CREDENTIALS.')
    storage_client = None
except Exception as e:
    logging.exception("Storage client init error: %s", e)
    storage_client = None

def upload_bytes_to_gcs(bucket_name: str, destination_path: str, data: bytes, content_type: str = 'application/octet-stream') -> str:
    """
    Upload bytes to GCS. If credentials available, upload and return a signed URL valid for 1 hour.
    If LOCAL_DEV is true, save to local_storage/ and return the path.
    If storage client not available, return a gs:// path placeholder.
    """
    if os.getenv("LOCAL_DEV") == "true":
        local_storage_dir = "local_storage"
        if not os.path.exists(local_storage_dir):
            os.makedirs(local_storage_dir)
        
        # Ensure the resumes subdirectory exists
        resumes_dir = os.path.join(local_storage_dir, "resumes")
        if not os.path.exists(resumes_dir):
            os.makedirs(resumes_dir)

        local_path = os.path.join(local_storage_dir, destination_path)
        with open(local_path, "wb") as f:
            f.write(data)
        logging.info(f"Saved file locally to {local_path}")
        return local_path

    if storage_client is None:
        logging.info('Storage client not available; skipping upload. Returning local placeholder path.')
        return f'gs://{bucket_name}/{destination_path}'

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_path)
    blob.upload_from_string(data, content_type=content_type)
    try:
        # generate_signed_url method may differ by library version.
        url = blob.generate_signed_url(expiration=timedelta(hours=1))
        logging.info("Uploaded to GCS and generated signed URL: %s", url)
        return url
    except Exception as e:
        logging.exception("Could not create signed URL; returning gs:// path. Error: %s", e)
        try:
            # If make_public is allowed, optionally make public (commented as default)
            # blob.make_public()
            # return blob.public_url
            return f'gs://{bucket_name}/{destination_path}'
        except Exception:
            return f'gs://{bucket_name}/{destination_path}'
