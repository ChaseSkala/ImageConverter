import os
import rawpy
import requests
import imageio.v3 as iio
import boto3
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError

load_dotenv("tokens.env")

AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY"].strip()
AWS_SECRET_KEY = os.environ["AWS_SECRET_KEY"].strip()
AWS_REGION = os.environ["AWS_REGION"].strip()
S3_BUCKET = os.environ["S3_BUCKET"].strip()


def upload_to_s3(file_path, bucket, object_name, aws_access_key, aws_secret_key, region):
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region
    )
    try:
        s3.upload_file(
            file_path, bucket, object_name,
            ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/jpg'}
        )
        url = f"https://{bucket}.s3.{region}.amazonaws.com/{object_name}"
        return url
    except NoCredentialsError:
        print("AWS credentials not available.")
        return None

def convert_image(event, client):
    files = event.get("files", [])
    posted_images = []

    for file in files:
        try:
            response = requests.get(
                file["url_private"],
                headers={"Authorization": f"Bearer {client.token}"}
            )
            response.raise_for_status()

            temp_path = f"temp_{file['id']}.raw"
            with open(temp_path, "wb") as f:
                f.write(response.content)

            with rawpy.imread(temp_path) as raw:
                rgb_image = raw.postprocess()
                output_path = f"converted_{file['id']}.jpg"
                iio.imwrite(output_path, rgb_image)

            s3_key = f"slack-converted/{file['id']}.jpg"
            s3_url = upload_to_s3(
                output_path, S3_BUCKET, s3_key,
                AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION
            )
            if s3_url:
                client.chat_postMessage(
                    channel=event["channel"],
                    blocks=[
                        {
                            "type": "image",
                            "image_url": s3_url,
                            "alt_text": f"Converted: {file['name']}"
                        }
                    ],
                    text=f"Here is your converted image: {s3_url}"
                )
                posted_images.append(s3_url)
            else:
                print(f"Failed to upload {output_path} to S3.")

            os.remove(temp_path)
            os.remove(output_path)

        except Exception as e:
            print(f"Error converting {file.get('name', 'unknown')}: {e}")

    if posted_images:
        return "Converted and posted images:\n" + "\n".join(posted_images)
    else:
        return "No files converted or posted."