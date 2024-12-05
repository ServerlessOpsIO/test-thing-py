# backstage / test-thing-py

Test thing

The full API can be found in the [OpenAPI document](./openapi.yaml).


## Architecture
This is an AWS serverless CRUD API backend service. It is built on top of the following AWS services:
* API Gateway
* Lambda
* DynamoDB
* Cognito (See _Getting Started / API / Authentication and Authorization_ for more)


## New Project Getting Started
This repository was generated from a template intended to get a new API up and running quickly. This section will cover different aspects of the newly created project as well as areas that may need to be modified to meet the specific needs of a new project.


### Database
The database is a DDB table with a primary key composed of a partition key and sort key to form a composite primark key. Both usage of a composite primary key and generically named partition and sort keys were chosen to allow for a variety of different data types to be stored in the table. These keys are:

* Partition Key: `pk`
* Sort Key: `sk`

The starter code assumes the values of _pk_ and _sk_ are the same value and their value is the same as the API's `id` path parameter. When creating new resources the starter code will dynamically create a UUID as the value for `pk` and `sk`.

If you expect to have multiple types of data stored in the same table you should consider using compound key values for _pk_ and _sk_. These are keys where the values are prefixed with a string indicating the data type. For example, prefixing the value with the collection name. eg. _thing#1234_. See the _Code_ section for more information on implimenting this.


### Code
When starting a new project the first place to start with adapting the code to meet the needs of a new project is the [`src/common/common/model/thing.py`](src/common/common/model/thing.py) file. This file contains interfaces for data and DDB table items.

Start by modifying the dataclasses to match the shape of your data. Optionally you can choose to replace that interface with one from another module if you're working with a pre-existing data model. The existing interface definition was chosen simply to make the project work out of the box.

Next, modify the `createKeys()` and `getKeys()` functions as necessary. These functions exist to make working with keys consistent across Lambda functions. If you want to prepend a data type to key values as mentioned in the _Database_ section you can do so here.


### API
This projects provides and OpenAPI document that defines the API. This document is located at [openapi.yaml](./openapi.yaml). This document besides defining the API is also used by the AWS SAM IaC to define the API Gateway resources.

#### Authentication and Authorization
This service is configured to use a pre-existing Cognito User Pool. Clients should obtain a JWT from the Cognito token endpoint using the client's clientId and clientSecret. Each endpoint's scope requirements are defined in the [OpenAPI document](./openapi.yaml).
