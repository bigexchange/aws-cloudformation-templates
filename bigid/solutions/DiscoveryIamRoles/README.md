### AWS Client side validation
```
aws cloudformation validate-template --template-body file://bigid-saas-roles.yaml
```

### How to deploy via CLI using example parameters
aws cloudformation create-stack --stack-name test-role-creation-from-cli --template-body file://bigid-saas-roles.yaml --parameters file://param-example.json --capabilities CAPABILITY_NAMED_IAM