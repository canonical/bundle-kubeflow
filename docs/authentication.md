# Authentication

Charmed Kubeflow uses [Dex][dex] for authentication. Dex allows for pluggable authentication
against many different identity providers, while presenting a unified
[OpenId Connect (OIDC)][oidc] interface.

[dex]: https://github.com/dexidp/dex
[oidc]: https://en.wikipedia.org/wiki/OpenID_Connect


## Auth Flow

The authentication flow for an unauthenticated request consists of these steps:

 - User makes an unauthenticated request
   - Redirected to /dex
 - User logs in via Dex
 - Redirected to gatekeeper callback endpoint
   - Sets a cookie with auth token for future requests
 - Redirected back to original page, with authorization token

### Unauthenticated Request

The flow of an unauthenticated request is shown here:

<img
    src="img/dex-unauthenticated.svg"
    alt="Unauthenticated Request"
    height="500" />

 - A user makes a request that goes through Ambassador
 - Ambassador checks with the gatekeeper service before allowing any request to go through
 - The gatekeeper service responds to Ambassador that the request is unauthenticated, and a redirect URL
 - Ambassador returns an HTTP 301 redirecting user to Dex

### Logging In

<img
    src="img/dex-login.svg"
    alt="Logging In"
    height="500" />

 - User makes request to /dex
 - Ambassador is configured to not check with the gatekeeper for requests to /dex
 - Dex presents a login page to the user
 - The user submits their credentials
 - Dex uses the configured connector to authenticate the user against an external auth service
   - Dex may also be configured with basic username/password support. This is the default in Charmed Kubeflow.
   - See the [dex configuration](#configuring-dex) section for more information on how to configure Dex with
     other connectors.
 - Dex redirects the user to a callback URL managed by the gatekeeper


### Receive Token

<img
    src="img/dex-callback.svg"
    alt="Receive Token"
    height="500" />

 - User makes request to callback URL
 - Ambassador sends request to gatekeeper service
 - Gatekeeper service generates JWT token in the `Set-Cookie` response header

### Authenticated Request

<img
    src="img/dex-authenticated.svg"
    alt="Authenticated Request"
    height="500" />

 - User makes authenticated request
 - Ambassador checks with the gatekeeper service to see if request is authenticated
 - Gatekeeper service affirms request is authenticated by looking at JWT token
 - Ambassador communicates with Kubeflow service for requested endpoint
 - Ambassador returns requested endpoint to user


## Configuring Dex

Dex presents a unified OIDC interface that is capable of authenticating against many different
backend authentication services. See the Dex README section on [Connectors][connectors] for a
complete list.

[connectors]: https://github.com/dexidp/dex#connectors

By default, Dex is configured with a basic username/password combo. These values can be displayed
with:

    juju config dex-auth username
    juju config dex-auth password

If you would like to configure dex to use a different connector, start by disabling the default
username/password:

    juju config dex-auth username='' password=''

Then, configure the connectors you wish to use:

    juju config dex-auth connectors="$CONNECTOR_YAML"

Where `$CONNECTOR_YAML` is a YAML list of connector configurations. The complete list of available
connector configurations can be found here:

https://github.com/dexidp/dex/tree/master/Documentation/connectors

As an example connector configuration, this is what you might use for `$CONNECTOR_YAML` to configure
Dex to authenticate against an OpenLDAP server:

```json
[{
    "id": "ldap",
    "name": "OpenLDAP",
    "type": "ldap",
    "config": {
        "bindDN": "cn=admin,dc=example,dc=org",
        "bindPW": "admin",
        "groupSearch": {
            "baseDN": "cn=admin,dc=example,dc=org",
            "filter": "",
            "groupAttr": "DN",
            "nameAttr": "cn",
            "userAttr": "DN"
        },
        "host": "ldap-service.auth.svc.cluster.local:389",
        "insecureNoSSL": true,
        "userSearch": {
            "baseDN": "cn=admin,dc=example,dc=org",
            "emailAttr": "DN",
            "filter": "",
            "idAttr": "DN",
            "nameAttr": "cn",
            "username": "cn"
        },
        "usernamePrompt": "Email Address"
    }
}]
'
```
