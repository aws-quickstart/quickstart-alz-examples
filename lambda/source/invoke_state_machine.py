import json
import boto3
import time
 
from botocore.vendored import requests
 
SUCCESS = "SUCCESS"
FAILED = "FAILED"

# Step Function Boto client
sfn = boto3.client('stepfunctions')

def lambda_handler(event, context):
    
    if event['RequestType'] == 'Delete':
        try:
            responseData = {}
            send_cfnresponse(event, context, SUCCESS, responseData)
        except Exception as inst:
            print(inst)
            send_cfnresponse(event, context, FAILED, {})
    elif event['RequestType'] == 'Create':
        try:

            smArn = event['ResourceProperties']['StateMachineArn']
            addOnS3Bucket = event['ResourceProperties']['AddOnS3Bucket']
            productName = event['ResourceProperties']['ProductName']
            productTemplateS3Url = event['ResourceProperties']['ProductS3Url']
            smInputJSON = create_state_machine_input(addOnS3Bucket, productName, productTemplateS3Url)
            
            # Print inputs from event
            print('State machine ARN: ', smArn)
            print('S3 Bucket to upload addon files: ', addOnS3Bucket)
            print('Product name: ', productName)
            print('Product Cloudformation template S3 URL: ', productTemplateS3Url)
            print('State machine input JSON: ', smInputJSON)
            
            # Start state machine execution
            smExecutionArn = invoke(smArn, smInputJSON)
            
            # Wait for state machine execution to complete. Approx. it takes 35 seconds.
            # TODO - This is not ideal to wait in lambda function. Need refactor.
            time.sleep(45)
            
            # Get state machine execution result
            smExecutionOutput = get_output(smExecutionArn)
            
            send_cfnresponse(event, context, SUCCESS, {})
        except Exception as ex:
            print('Error!')
            print(ex)
            send_cfnresponse(event, context, FAILED, {})

# Create JSON input for state machine
def create_state_machine_input(add_on_bucket, pname, purl):
    # Sample event
    ################
    # {
    # "smArn": "arn:aws:states:us-west-2:046245209178:stateMachine:StateMachine-QLMcJZOuQZY5",
    # "smInputJSON": "{ \"temp_s3_bucket\": \"alz-qs-product1234\", \"product_name\": \"f5\",\"product_s3_url\": \"https:\/\/aws-quickstart.s3.amazonaws.com\/quickstart-f5-big-ip-virtual-edition\/templates\/master.template\"}"
    # }

    smInputJSON = "{\"temp_s3_bucket\": \""+ add_on_bucket +"\",\"product_name\": \""+ pname +"\",\"product_s3_url\": \""+ purl +"\"}"

    return smInputJSON
            

# Invoke state machine
def invoke(stateMachineArn, stateMachineInputJSON):
    
    # The Amazon Resource Name (ARN) of the state machine to execute.
    # Example - arn:aws:states:us-west-2:112233445566:stateMachine:HelloWorld-StateMachine
    STATE_MACHINE_ARN = stateMachineArn
    
    #The string that contains the JSON input data for the execution
    INPUT = stateMachineInputJSON
    
    response = sfn.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        input=INPUT
    )
    
    #display the arn that identifies the execution
    print("state machine execution response:")
    print(response.get('executionArn'))
    
    return response.get('executionArn')

# Get state machine execution output
def get_output(stateMachineExecutionArn):
    
    # The Amazon Resource Name (ARN) of the state machine execution.
    # Example - arn:aws:states:us-west-2:046245209178:execution:StateMachine-QLMcJZOuQZY5:05663906-44d4-4465-921d-58454836ba40
    STATE_MACHINE_EXECUTION_ARN = stateMachineExecutionArn
    
    response = sfn.describe_execution(
        executionArn=stateMachineExecutionArn
    )
    
    # Display the output
    print('State machine execution output: ')
    print(response.get('output'))


#  Copyright 2016 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
#  This file is licensed to you under the AWS Customer Agreement (the "License").
#  You may not use this file except in compliance with the License.
#  A copy of the License is located at http://aws.amazon.com/agreement/ .
#  This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied.
#  See the License for the specific language governing permissions and limitations under the License.

def send_cfnresponse(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']
 
    print(responseUrl)
 
    responseBody = {}
    responseBody['Status'] = responseStatus
    responseBody['Reason'] = 'See the details in CloudWatch Log Stream: ' + context.log_stream_name
    responseBody['PhysicalResourceId'] = physicalResourceId or context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']
    responseBody['NoEcho'] = noEcho
    responseBody['Data'] = responseData
 
    json_responseBody = json.dumps(responseBody)
 
    print("Response body:\n" + json_responseBody)
 
    headers = {
        'content-type' : '',
        'content-length' : str(len(json_responseBody))
    }
 
    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
        print("Status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))