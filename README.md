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
