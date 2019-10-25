# This module validates the Quick Start CloudFormation template from an S3URL,
# parses the parameters and generate 2 files - parameter.json and parameter.yaml.
# - parameter.json is the input parameter file in jinja2 format, as desired by
# service catalog to launch the CloudFormation template.
# - parameter.yaml file contains the parameters in yaml format using jinja2
# notation, as needed for user-input.yaml file.

import os
import boto3
import json
import yaml
import re
import logging
import utils
logger = logging.getLogger()
logger.setLevel(logging.INFO)

user_input_file_path = "user-input.yaml"
param_file_path = "parameter.json"

cfn_client = boto3.client('cloudformation')

# Lambda function handler
def lambda_handler(event, context):
    logger.info('## ENVIRONMENT VARIABLES')
    logger.info(os.environ)
    logger.info('## EVENT')
    logger.info(event)
    
    # Lambda inputs
    temp_s3_bucket = event['temp_s3_bucket']
    #param_file_path = event['param_file'] # 'parameter.json'
    #user_input_file_path = event['user_input_file'] # parameter.yaml
    product_s3_url = event['product_s3_url'] # https://aws-quickstart.s3.amazonaws.com/quickstart-f5-big-ip-virtual-edition/templates/master.template
    
    
    create_and_upload(product_s3_url, param_file_path, user_input_file_path, temp_s3_bucket)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Created and uploaded parameter and user input file successfully!')
    }


def create_and_upload(template_s3_url, local_param_file, local_userinput_file, s3bucket):
    '''
    Main function - parse cloudformation template from S3URL and generate
    parameter.json and parameter.yaml files.
    '''
    try:
        result = cfn_client.validate_template(TemplateURL=template_s3_url)
        
        # create parameter.json structure
        param_obj = result['Parameters']
        for obj in param_obj:
            [obj.pop(k) for k in list(obj.keys()) if k != 'ParameterKey']
            obj['ParameterValue'] = "{{ "+ obj['ParameterKey'] + " }}"
        
        param_str = json.dumps(param_obj, indent=2, separators=(',', ': '))
        
        dict = { "\"{{":"{{", "}}\"":"}}" }
        cfn_params = search_and_replace(param_str, dict)
        
        userinput_content = generate_userinput_params(param_obj)
        #cfn_params = search_and_replace(json.dumps(param_obj, indent=2, separators=(',', ': ')))
        
        # generate user_input yaml parameter file and upload to s3
        utils.write_to_file('/tmp/'+local_userinput_file, userinput_content)
        utils.upload_to_s3(s3bucket, '/tmp/'+local_userinput_file, local_userinput_file)
        
        # generate parameter.json file and upload to s3
        utils.write_to_file('/tmp/'+local_param_file, cfn_params)
        utils.upload_to_s3(s3bucket, '/tmp/'+local_param_file, local_param_file)
        
    except Exception as e:
        print(e)

def generate_userinput_params(pObj):
    '''
    Generate parameters section for user_input.yaml file
    '''
    
    json_obj = {}
    param_jObj = {}
    
    for obj in pObj:
        json_obj[obj['ParameterKey']] = obj['ParameterValue']
    
    param_jObj['parameters'] = json_obj
    yaml_str = yaml.dump(param_jObj, default_flow_style=False)
    
    dict = { "'{{":"{{", "}}'":"}}" }
    userinput_params = search_and_replace(yaml_str, dict)
    
    return userinput_params
    #print(json.dumps(param_jObj, indent=2, separators=(',', ': ')))
    #print(yaml.dump(param_jObj, default_flow_style=False))

def search_and_replace(content, dict):
    '''
    Returns updated content after replacing "{{ with {{ and }}" with }} in the given `content`.
    {
        "search-term1":"replace-term1"
        search-term2":"replace-term2"
    }
    '''
    
    for search_item, replace_item in dict.items():
        p = re.compile(search_item)
        content = p.sub(replace_item, content)
        #content = result
        
    return content