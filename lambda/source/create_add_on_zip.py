# This module creates Add on product zip file and upload to S3 bucket
# Copies the template file from QS templates (e.g https://s3.amazonaws.com/aws-quickstart/quickstart-aws-vpc/templates/aws-vpc.template)
# Copies the paramter files ( user-input.yaml,<productName>_parameter.json)from source bucket. Source bucket receive these files from earlier program as output
# create add_on_manifest.yaml from the sample file
# Receives 4 inputs  -
# ProductName - name of the add-on product for ALZ ,default= product1234 , this name is being used to create add-on bucket name and add-on zip file name.
# qsProductTemplate - the s3 location of Quick start product template, default = "https://s3.amazonaws.com/aws-quickstart/quickstart-aws-vpc/templates/aws-vpc.template"
# sourceBucketForParameterFiles - source s3 bucket name which containes converted parameter files in jinja2 format, default="addon-product-paramterfiles"
# sourceProductParamterFileName - Jinja2 formatted product parameter filename, default="Addon-Product1_parameter.json"


import urllib.request
import os
import io
import zipfile
import json
from ruamel.yaml import YAML
import re
import yaml
import logging
import utils
import shutil
import tempfile
logger = logging.getLogger()
logger.setLevel(logging.INFO)

yaml = YAML()
yaml.preserve_quotes = True

# Constants
sample_addOn_manifest_file="sample_add_on_manifest.yaml"
sample_userInput_file="sample_user_input2.yaml"
addOn_manifest_filename="add_on_manifest.yaml"
addOn_userInput_filename="user-input.yaml"
param_file_path = "parameter.json"

# Lambda function handler
def lambda_handler(event, context):
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info('## EVENT')
    logger.info(event)

    # Lambda inputs
    temp_s3_bucket = event['temp_s3_bucket']
    product_name = event['product_name']
    #param_file_path = event['param_file'] # 'parameter.json'
    product_s3_url = event['product_s3_url'] # https://aws-quickstart.s3.amazonaws.com/quickstart-f5-big-ip-virtual-edition/templates/master.template

    # Temp variables
    addOn_parameter_core_path="parameters/core_accounts/"
    product_core_file_path = addOn_parameter_core_path+"aws-landing-zone-"+product_name+".json"
    addOn_zip_filename="alz-qs-"+product_name+".zip"
    addOnTemplateCorePath="templates/core_accounts/"
    add_on_template = "aws-landing-zone-"+product_name+".template"
    addOn_template_filepath = addOnTemplateCorePath+add_on_template

    main(temp_s3_bucket, param_file_path, product_s3_url, product_name, product_core_file_path, addOn_template_filepath, sample_addOn_manifest_file, addOn_zip_filename)

    return {
        'statusCode': 200,
        'body': json.dumps('Addon zip created successfully!')
    }


def main(source_s3_bucket, parameter_json_filename, template_s3_url, product_name, product_core_file_path, addOn_template_filepath, sample_addOn_manifest_file, addOn_zip_filename):
    try:
        # define some parameters
        fileList=() # to concatenate list of filenames and fileContent

        # Call functions
        fileList=[*fileList, fetchUserInputData(source_s3_bucket,addOn_userInput_filename,product_core_file_path)] # function call and concatenate results
        fileList=[*fileList, fetchAddonManifestData(product_name, sample_addOn_manifest_file)]# function call and concatenate results
        fileList=[*fileList, fetchAddonProductParameterData(source_s3_bucket,parameter_json_filename, product_core_file_path)] # function call and concatenate results
        fileList=[*fileList, fetchProductTemplateData(template_s3_url, addOn_template_filepath)] # function call and concatenate results
        createZip(fileList,source_s3_bucket,addOn_zip_filename)
        utils.delete_file_from_s3(source_s3_bucket, parameter_json_filename)
        utils.delete_file_from_s3(source_s3_bucket, addOn_userInput_filename)

    except Exception as e:
        raise

# get the user-input.yaml file data from source S3 bucket
def fetchUserInputData(sourceBucketForParameterFiles,addOn_userInput_filename,addOnProductParameterCoreFile):
    userInputObj=utils.getobj_from_s3(sourceBucketForParameterFiles, addOn_userInput_filename)
    userInputContent=userInputObj['Body'].read()

    # Read sample user-input file content
    sampleUIFile=open(sample_userInput_file,'r')
    sampleUIFileContent=sampleUIFile.read()
    # Merge parameters file content into user-input file
    p=re.compile("productParameters")
    mergedFileContent = p.sub(userInputContent.decode('utf-8'), sampleUIFileContent)
    # replace the product parameter file placeholder with actual product name
    q=re.compile("parameters/core_accounts/productParameterFileName.json")
    mergedFileContent = q.sub(addOnProductParameterCoreFile, mergedFileContent)
    # Write locally
    mergedFileBinaryContent=io.BytesIO(bytes(mergedFileContent,'utf-8'))
    sampleUIFile.close()
    file = open('/tmp/merged-user-input.yaml', 'w')
    file.write(mergedFileContent)
    file.close()
    # Fix indentation
    with open('/tmp/merged-user-input.yaml', 'r+') as text_file:
        fileContent = text_file.readlines()
        text_file.seek(0)
        count = 0
        for line in fileContent:
            if count==3:
                text_file.write("    "+line)
            elif "parameters:" in line:
                text_file.write(line)
                count = count+1
            else:
                text_file.write(line)
        text_file.truncate()

    mergedFile=open('/tmp/merged-user-input.yaml','r')
    mergedFileContent=mergedFile.read()
    mergedFileContentBinary=io.BytesIO(bytes(mergedFileContent,'utf-8'))
    mergedFile.close()

    return (addOn_userInput_filename,mergedFileContentBinary)

# create manifest file from the sample manifest file by replacing values
def fetchAddonManifestData(productName, sampleAddOnManifestFile):
    sampleFile=open(sampleAddOnManifestFile,'r')
    sampleFileContent=sampleFile.read()
    p=re.compile("ProductName")
    addOnFileContent=p.sub(productName, sampleFileContent)
    addOnFileBinaryContent=io.BytesIO(bytes(addOnFileContent,'utf-8'))
    sampleFile.close()
    return (addOn_manifest_filename,addOnFileBinaryContent)


# get the product parameter file data from source S3 bucket
def fetchAddonProductParameterData(sourceBucketForParameterFiles,sourceProductParamterFileName, addOnProductParameterCoreFile):
    addOnProductParameterObj=utils.getobj_from_s3(sourceBucketForParameterFiles, sourceProductParamterFileName)
    addOnProductParameterContent=addOnProductParameterObj['Body'].read()
    addOnProductParameterContent=io.BytesIO(addOnProductParameterContent)
    return (addOnProductParameterCoreFile,addOnProductParameterContent)

# get the product template data from source S3 bucket
def fetchProductTemplateData(qsProductTemplate, addOnTemplateCoreFile):
    webURL = urllib.request.urlopen(qsProductTemplate)
    data = webURL.read()
    # created file out of data to pass as parameter to util function
    file = "/tmp/templateTestFile"
    fileObj = open(file, "wb")
    fileObj.write(data)
    if (utils.is_json(file) is True) and (utils.is_yaml(file) is False):
        jsonObject=json.loads(data.decode('utf-8'))
        str = json.dumps(jsonObject, indent=4, sort_keys=True)
    elif (utils.is_json(file) is False) and (utils.is_yaml(file) is True):
        yamlObject = yaml.load(data)
        out = io.StringIO();
        yaml.dump(yamlObject, out)
        str = out.getvalue()
    qsProductTemplateContent=io.StringIO(str)
    return (addOnTemplateCoreFile,qsProductTemplateContent)

# Add all of the contents into zip file and upload it to S3
def createZip(fileList,addOnTempBucket,addOnTempZip):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for file_name, data in fileList:
                zip_file.writestr(file_name, data.getvalue())
        zip_buffer.seek(0)  # So that bytes are read from beginning
        utils.upload_fileobj_to_s3(zip_buffer, addOnTempBucket, addOnTempZip)
