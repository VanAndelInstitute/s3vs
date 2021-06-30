# S<sup>3</sup>VS (S3 Virtual Slide)
This is a reference implementation for viewing Aperio SVS digital slide images that are stored in Amazon S3.

## Front-end web client
The S<sup>3</sup>VS front-end [(web)](/web) uses [OpenSeadragon](https://openseadragon.github.io/) and is meant to be embedded in an existing application. Once the back-end is deployed, set the service endpoint in `config.js`, and then you can test the front-end in standalone mode like so:

`npx http-server web`  
or  
`npx serve web`  
or  
`npx servor --static web`

## Back-end API/service
The S<sup>3</sup>VS back-end [(api)](/api) is implemented as an [AWS Serverless](https://aws.amazon.com/serverless/sam/) application. It creates a Lambda function that translates [IIIF](https://iiif.io/api/image/3.0/) image requests to S3 byte-range fetches against the .svs file in an S3 bucket. It relies on a [modified implementation of OpenSlide](https://github.com/VanAndelInstitute/openslide) to read the .svs files from an S3 bucket.  
This implementation uses Amazon API Gateway with an API mapping to a custom domain. If your front-end uses AWS Signature Version 4 signed requests (e.g. using AWS Amplify), another option for the API on AWS is a [S3 Object Lambda](https://docs.aws.amazon.com/AmazonS3/latest/userguide/transforming-objects.html) REST endpoint with a DNS alias record.
