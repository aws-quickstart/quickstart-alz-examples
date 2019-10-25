"""
Create Service Catalog ALZ add-on product template (.template) from (1)
"""

import zipfile
import shutil
import json
import yaml
from ruamel.yaml import YAML
import os
import logging
import utils
logger = logging.getLogger()
logger.setLevel(logging.INFO)

yaml = YAML()
yaml.preserve_quotes = True

sc_product_template_src = 'sc_alz_add_on_product_template.template'
local_file_path = '/tmp/'


# Lambda function handler
def lambda_handler(event, context):
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info('## EVENT')
    logger.info(event)
    
    # Lambda inputs
    temp_s3_bucket = event['temp_s3_bucket']
    product_name = event['product_name']
    
    addOn_zip_filename="alz-qs-"+product_name+".zip"
    sc_product_template_name="sc-"+product_name+".template"

    create_add_on(temp_s3_bucket, addOn_zip_filename, local_file_path, sc_product_template_name)
    utils.upload_to_s3(temp_s3_bucket, local_file_path+sc_product_template_name, sc_product_template_name)

    return {
        'statusCode': 200,
        'body': json.dumps('SC template created successfully!')
    }

# Create Service Catalog ALZ add-on product template (.template)
def create_sc_product_template(file_path, file_name, sc_product_template_target):
    # Unzip the ALZ Add-On package
    zip_call = zipfile.ZipFile(file_path + file_name)
    zip_call.extractall(file_path)
    zip_call.close()

    # Use Service Catalog product template
    shutil.copyfile(sc_product_template_src, file_path + sc_product_template_target)

    # Get the content of Service Catalog product template
    with open(file_path + sc_product_template_target, 'r') as yaml_file:
        sc_product_template_content = yaml.load(yaml_file)

    # Get ALZ Add-On product template
    for root, dirs, files in os.walk(file_path):
        for name in files:
            if (root == file_path + "templates/core_accounts") and (".template" in name):
                alz_add_on_template = "templates/core_accounts/" + name
                break

    # Convert the product template in json to template in yaml
    file = file_path + alz_add_on_template
    if (utils.is_json(file) is True) and (utils.is_yaml(file) is False):
        utils.json_2_yaml(file, file_path + 'temp_yaml.template')
        shutil.move(file_path + 'temp_yaml.template', file_path + alz_add_on_template)
    elif (utils.is_json(file) is False) and (utils.is_yaml(file) is True):
        pass
    else:
        raise ValueError('The file is neither json nor yaml! exit()')
        exit()

    # Get the content of ALZ Add-On product template
    parameter_dict = dict()
    with open(file_path + alz_add_on_template, 'r') as yaml_file:
        alz_add_on_template_content = yaml.load(yaml_file)
        alz_add_on_template_parameters = alz_add_on_template_content["Parameters"]
        for key in alz_add_on_template_parameters:
            parameter_dict[key] = ("!Ref " + key)

    # Populate Service Catalog product template from ALZ Add-On template
    sc_product_template_content["Parameters"].update(alz_add_on_template_content["Parameters"])
    sc_product_template_content["Metadata"]["AWS::CloudFormation::Interface"]["ParameterGroups"].extend\
        (alz_add_on_template_content["Metadata"]["AWS::CloudFormation::Interface"]["ParameterGroups"])
    sc_product_template_content["Resources"]["LandingZoneAddOnConfigDeployer"]["Properties"]["find_replace"][0]["parameters"].update(parameter_dict)

    if sc_product_template_content:
        with open(file_path + sc_product_template_target, 'w') as yaml_file:
            yaml.dump(sc_product_template_content, yaml_file)

    # Clean up extra quotes
    with open(file_path + sc_product_template_target, 'r+') as text_file:
        sc_product_template_content = text_file.readlines()
        text_file.seek(0)
        for line in sc_product_template_content:
            if "'!Ref" in line:
                text_file.write(line.replace("'", ""))
            else:
                text_file.write(line)
        text_file.truncate()
    return


def create_add_on(zip_source_s3_bucket, zip_src_file, local_dest_file_path, sc_product_template_name):
    utils.download_file_from_s3(zip_source_s3_bucket, zip_src_file, local_dest_file_path, zip_src_file)
    create_sc_product_template(local_dest_file_path, zip_src_file, sc_product_template_name)

if __name__ == "__main__":
    zip_src_s3_bucket = input("S3 bucket for Add-On product package [alz-addon-products]: ") or "alz-addon-products"
    zip_src_file = input("Add-On product package name [alz-addon-product.zip]: ") or "alz-addon-product.zip"
    local_dest_file_path = local_file_path
    sc_product_template_name = input(
        "Service Catalog Add-On product template name [sc-addon-product.template]: ") or "sc-addon-product.template"

    # Create Service Catalog template for Add-On product
    create_add_on(zip_src_s3_bucket, zip_src_file, local_dest_file_path, sc_product_template_name)

    exit(0)