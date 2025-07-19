# daedalus-deploy
Deploy tool for the Daedalus app

## Requirements

1. [Python3](https://www.python.org/downloads/) (>= 3.10)
2. [Hatch](https://hatch.pypa.io/latest/install/)

## Installation

This project is built with hatch. It is not published to PyPI, so must be run using hatch from local source.

Clone this repo, then: `hatch shell` before using the deploy tool as below. (You can exit the hatch shell with `exit`.)

## Usage

```
Usage:
  daedalus start [--pull] [<configname>]
  daedalus stop  [--volumes] [--network] [--kill] [--force]
  daedalus destroy
  daedalus status
  daedalus upgrade

Options:
  --pull                    Pull images before starting
  --volumes                 Remove volumes (WARNING: irreversible data loss)
  --network                 Remove network
  --kill                    Kill the containers (faster, but possible db corruption)
```

For example, you can start the local dev deploy (with fake proxy ssl) using: `daedalus start fakeproxy`.

Once a configuration is set during `start`, it will be reused by subsequent commands
(`stop`, `status`, `upgrade`, `user`, etc) and removed during destroy.
The configuration usage information is stored in `config/.last_deploy.`

## Deployment configurations
There are three configurations
- fakeproxy: for local testing
- staging: for deployment onto our staging server at `daedalus-dev.dide.ic.ac.uk`
- prod: on the way!

## Development

### Testing
Run tests with `hatch test`. Generate coverage with `hatch test --cover`.

### Linting
Run linting with automatic fixes with `hatch fmt`. To check linting only, with no file changes, use `hatch fmt --check`.

## Using Let's Encrypt

We mount a shared volume (`daedalus-tls`) into the proxy, and a long-running
process, [acme-buddy](https://github.com/reside-ic/acme-buddy), is our ACME client
that talks to Let's Encrypt and requests a new certificate a while before expiry.
It then writes that into the `daedalus-tls` volume, and sends a signal to the
proxy causing Nginx to load the new certificate.

When testing this on a new deployment, we should set an environment variable
`ACME_BUDDY_STAGING` to `1` - this causes acme-buddy to request staging certificates
from Let's Encrypt. This provides test certificates; without doing this, there is a
[rate limit](https://letsencrypt.org/docs/rate-limits/) of 5 renewals per day
per domain name. Once testing looks good, the environment variable can be omitted
or set to `0` for the final deploy.
