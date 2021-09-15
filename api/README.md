# S<sup>3</sup>VS back-end API/service
The back-end is implemented in Python (which has the lowest Lambda cold start times) and uses [Pillow-SIMD](https://github.com/uploadcare/pillow-simd) for shrinking tiles (as needed), Aperio-to-sRGB color space conversion, and JPEG compression.

## Prerequisites
The infrastructure code is currently a [SAM app](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html). You'll need to install the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html). You'll also need to [install Docker](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install-mac.html#serverless-sam-cli-install-mac-docker) for the [`--use-container` flag](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-build.html#build-zip-archive) to build the native Linux binaries for the OpenSlide and libdmtx Lambda layers.

You'll also need:
- [ ] A DNS Alias record for the API custom domain. You can create one using Route 53.
- [ ] A SSL certificate for the custom domain. You can request public certificates from AWS Certificate Manager.
- [ ] An unique name for a S3 bucket to contain the .svs files.

## Build and deploy
You can use the `--guided` argument to prompt for deployment parameters, or you can create a AWS SAM configuration file (samconfig.toml) with all the necessary parameters to facilitate deployment.
First build and deploy the Lambda layers, if you haven't yet:
```
cd layers
sam build -u
sam deploy [--guided]
cd ..
```
Then build the Lambda functions:
```
sam build
sam deploy [--guided]
```

## End-to-end testing
Use the [sample web client](/web).
