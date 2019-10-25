import boto3
import yaml
from ruamel.yaml import YAML
import json

yaml = YAML()
s3_client = boto3.client('s3')

def write_to_file(filepath, content):
    ''' Writes `content` to file at `filepath` '''
    param_file = open(filepath, 'w')
    param_file.write(content)
    param_file.close()

def upload_to_s3(bucket_name, local_file_path, s3_file_path):
    ''' Upload a file to S3 bucket '''
    #print("Uploading file to s3 location {}/{}".format(bucket_name, s3_file_path))
    s3_client.upload_file(local_file_path, bucket_name, s3_file_path)

def upload_fileobj_to_s3(data, bucket_name, s3_file_path):
    ''' Upload a file like object to S3 bucket '''
    #print("Uploading file to s3 location {}/{}".format(bucket_name, s3_file_path))
    s3_client.upload_fileobj(data, bucket_name, s3_file_path)

def getobj_from_s3(bucket_name, s3_file_path):
    ''' Get an object from S3 bucket and return the object '''
    return s3_client.get_object(Bucket=bucket_name, Key=s3_file_path)

def download_file_from_s3(bucket, key, file_path, file_name):
    ''' Download file from S3 bucket to a local file path '''
    s3_client.download_file(bucket, key, file_path + file_name)
    return

def delete_file_from_s3(bucket_name, file_name):
    s3 = boto3.client('s3')
    s3.delete_object(Bucket=bucket_name, Key=file_name)
    return

def json_2_yaml(input_file, out_file):
    ''' Convert json file to yaml file '''
    with open(input_file, 'r') as json_file:
        json_content = json.load(json_file)
        with open(out_file, 'w') as yaml_file:
            yaml.dump(json_content, yaml_file)
    return

def is_yaml(file):
    with open(file, 'r') as stream:
        try:
            yaml.load(stream)
            return True
        except Exception as e:
            return False

def is_json(file):
    with open(file, 'r') as stream:
        try:
            json.loads(stream)
            return True
        except Exception as e:
            return False