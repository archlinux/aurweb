# aurweb Web Authentication

aurweb uses an HTTP cookie to persist user sessions across requests.
This cookie **must** be delivered with a request in order to be considered
an authenticated user.

See [HTTP Cookie](#http-cookie) for detailed information about the cookie.

## HTTP Cookie

aurweb utilizes an HTTP cookie by the name of `AURSID` to track
user authentication across requests.

This cookie's requirements changes due to aurweb's configuration
in the following ways:

- `options.disable_http_login: 0`
    - [Samesite=LAX](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#samesite_attribute), Max-Age
- `options.disable_http_login: 1`
    - [Samesite=LAX](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#samesite_attribute), [Secure, HttpOnly](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies), Max-Age

### Max-Age

The value used for the `AURSID` Max-Age attribute is decided based
off of the "Remember Me" checkbox on the login page. If it was not
checked, we don't set Max-Age and it becomes a session cookie.
Otherwise we make it a persistent cookie and for the expiry date
we use `options.persistent_cookie_timeout`.
It indicates the number of seconds the session should live.

### Notes

At all times, aur.archlinux.org operates over HTTPS. Secure cookies will
only remain intact when subsequently requesting an aurweb route through
the HTTPS scheme at the same host as the cookie was obtained.

## Login Process

When a user logs in to aurweb, the following steps are taken:

1. Was a Referer header delivered from an address starting with
`{aurweb_url}/login`?
    1. No, an HTTP 400 Bad Request response is returned
    2. Yes, move on to 2
2. Does a Users database record exist for the given username/email?
    1. No, you are returned to the login page with `Bad username or password.`
    error
    2. Yes, move on to 3
3. Is the user suspended?
    1. Yes, you are returned to the login page with `Account Suspended` error
    2. No, move on to 4
4. Can the user login with the given password?
    1. No, you are returned to the login page with `Bad username or password.`
    error
    2. Yes, move on to 5
5. Update the user's `LastLogin` and `LastLoginIPAddress` columns
6. Does the user have a related Sessions record?
    1. No, generate a new Sessions record with a new unique `SessionID`
    2. Yes, update the Sessions record's `SessionID` column with a new unique
    string and update the Sessions record's `LastUpdateTS` column if it has
    expired
    3. In both cases, set the user's `InactivityTS` column to `0`
    4. In both cases, return the new `SessionID` column value and move on to 7
7. Return a redirect to the `next` GET variable with the
following cookies set:
    1. `AURSID`
        - Unique session string matching the user's related
        `Sessions.SessionID` column
    2. `AURTZ`
        - User's timezone setting
    3. `AURLANG`
        - User's language setting
    4. `AURREMEMBER`
        - Boolean state of the "Remember Me" checkbox when login submitted

## Auth Verification

When a request is made toward aurweb, a middleware is responsible for
verifying the user's auth cookie. If no valid `AURSID` cookie could be
found for a user in the database, the request is considered unauthenticated.

The following list of steps describes exactly how this verification works:
1. Was the `AURSID` cookie delivered?
    1. No, the algorithm ends, you are considered unauthenticated
    2. Yes, move on to 2
2. Was the `AURREMEMBER` cookie delivered with a value of `True`?
    1. No, set the expected session timeout **T** to `options.login_timeout`
    2. Yes, set the expected session timeout **T** to
    `options.persistent_cookie_timeout`
3. Does a Sessions database record exist which matches the `AURSID`?
    1. No, the algorithm ends, you are considered unauthenticated
    2. Yes, move on to 4
4. Does the Sessions record's LastUpdateTS column fit within `utcnow - T`?
    1. No, the Sessions record at hand is deleted, the algorithm ends, you
    are considered unauthenticated
    2. Yes, move on to 5
5. You are considered authenticated

## aur.archlinux.org Auth-Related Configuration

- Operates over HTTPS with a Let's Encrypt SSL certificate
- `options.disable_http_login: 1`
- `options.login_timeout: <default_provided_in_config.defaults>`
- `options.persistent_cookie_timeout: <default_provided_in_config.defaults>`
