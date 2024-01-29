In Kubernetes, communication between the api-server and any admission controllers is via HTTPS only

Therefore certificates are needed for webhook admission server to utilise so it can communicate securely

The genSSH script generates a valid key and certificate that our server can utilise. It also requests kubernetes to sign the certificate.
