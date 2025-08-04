## Authenticate

Xray provides a REST API with endpoints specifically made for dealing with test management.  
Requests made to Xray's REST API must be authenticated based on an API Key created for some user in the Xray [Global Settings: API Keys](https://docs.getxray.app/display/XRAYCLOUD/Global+Settings%3A+API+Keys).  
Thus, the first step you need to do is to obtain a token based on the Client ID and Client Secret of your assigned API Key. You can then use that token to make requests to the Xray Cloud.

Authenticates the requester based on the provided Client Id and Client Secret and returns an authorization token to be used in other API requests.

**Request**

**Example**

`{` `"client_id"``:` `"32A27E69C0AC4E539C1401643709E8E7"``,``"client_secret"``:` `"d62f81eb9ed859e22e54356dd8a00e4a5f0d0c2b2b52340776f6c7d6d757b962"` `}`

Example Requests

curl -H "Content-Type: application/json" -X POST --data @"cloud\_auth.json" https://xray.cloud.getxray.app/api/v2/authenticate

curl -H "Content-Type: application/json" -X POST --data '{ "client\_id": "32A27E69B0AC4E539C1401643799E8E7","client\_secret": "d62f81eb9ed859e11e54356dd8a00e4a5f0d0c2a2b52340776f6c7d6d757b962" }'  https://xray.cloud.getxray.app/api/v2/authenticate

# the following example, shows a way of setting a shell variable with the token value, so it can be used in subsequent requests

token=$(curl -H "Content-Type: application/json" -X POST --data @"cloud\_auth.json" https://xray.cloud.getxray.app/api/v2/authenticate| tr -d '"')  

**Responses**

200 OK : **application/json** : Successful. Returns a JSON string (delimited with the " character), containing the authorization token.

`"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0ZW5hbnQiOiI0MjZiYzA4Yy02N2VmLTNjMjYtYWU1YS03NjczYTB1ZjIwNjkiLCJ1c2VyS2V5IjoiYW5kcmUucm9kcmlndWVzIiwiaWF0IjixNTI1ODcxODkzLCJleHAiOjE1MjU5NTgyOTMsImF1ZCI6IhMyQTI3RTY5QjBBQzRFNTM5QzE0MDE2NDM3OTlFOEU3IiwiaXNzIjoiY29tLnhwYW5kaXQueHJheSIsInN1YiI6IjMyQTI3RTY5QjBBQzRFNTM5QzE0MDE2NDM3OTlFOEU3In0.8ah2IQ9rA_zotyh_6trFgfIvhn2awdFFrOHnN2F2H7m"`

400 BAD\_REQUEST : **text/plain** **:** Wrong request syntax.

401 UNAUTHORIZED : **text/plain** : The Xray license is not valid.

500  INTERNAL SERVER ERROR : **text/plain** : An internal error occurred when authenticating the request.