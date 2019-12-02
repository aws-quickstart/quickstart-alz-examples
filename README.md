# ISV product packaging solution for AWS Landing Zone

The Amazon Web Services (AWS) Landing Zone solution automates customers’ landing zone deployment and configuration with AWS security and operation best practices. AWS Control Tower extends AWS Landing Zone as a managed landing zone service to further simplify landing zone deployment and management. But after customers set up their landing zone environments through either AWS Landing Zone or AWS Control Tower, they can encounter challenges when deploying additional AWS solutions or Independent Software Vendor (ISV) products, all referred to as add-on products, in their environments.

The solution described here packages ISV products or any services that are configured by AWS Quick Starts or other AWS CloudFormation templates, into an add-on product package for automated deployment in AWS Landing Zone accounts.

The solution detail and user procedure are described in [this blog](https://aws.amazon.com/blogs/infrastructure-and-automation/automating-isv-product-packaging-and-deployment-in-aws-landing-zone/). 

To generate an add-on product package, run the [solution master template](https://github.com/aws-quickstart/quickstart-alz-examples/blob/master/templates/qs-alz-master.template) through AWS CloudFormation Stack.  