# S<sup>3</sup>VS back-end API/service
There are a few choices for the back-end:
* A [Java](Java) impementation that uses [Graphics2D](https://docs.oracle.com/javase/8/docs/api/java/awt/Graphics2D.html) for shrinking tiles (as needed) and [ImageIO](https://docs.oracle.com/javase/7/docs/api/javax/imageio/ImageIO.html) for JPEG compression.
* A [Node.js](Node.js) implementation that uses the [sharp](https://sharp.pixelplumbing.com/) image processing module (which includes OpenSlide) for shrinking tiles (as needed) and JPEG compression.
* A [Python](Python) implementation that uses [Pillow-SIMD](https://github.com/uploadcare/pillow-simd) for shrinking tiles (as needed) and JPEG compression.


## Prerequisites
The infrastructure code is currently a [SAM app](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html). You'll need to install the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html). You'll also need to [install Docker](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install-mac.html#serverless-sam-cli-install-mac-docker) for the [`--use-container` flag](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-build.html#build-zip-archive) to build the native Linux binaries for the OpenSlide and libdmtx Lambda layers.

You'll also need:
- [ ] A DNS Alias record for the API custom domain. You can create one using Route 53.
- [ ] A SSL certificate for the custom domain. You can request public certificates from AWS Certificate Manager.
- [ ] An unique name for a S3 bucket to contain the .svs files.

## Build and deploy
You can use the `--guided` argument to prompt for deployment parameters, or you can create a AWS SAM configuration file (samconfig.toml) with all the necessary parameters to facilitate deployment.
```
sam build -u [--cached]
sam deploy [--guided]
```

## End-to-end testing
Use the [sample web client](/web).
