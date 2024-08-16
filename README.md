# daedalus-deploy
Deploy tool for the Daedalus app

## Installation
Clone this repo and install dependencies with:
```
pip3 install --user -r requirements.txt
```

## Usage

```
Usage:
  ./daedalus start [--pull] [<configname>]
  ./daedalus stop  [--volumes] [--network] [--kill] [--force]
  ./daedalus destroy
  ./daedalus status
  ./daedalus upgrade

Options:
  --pull                    Pull images before starting
  --volumes                 Remove volumes (WARNING: irreversible data loss)
  --network                 Remove network
  --kill                    Kill the containers (faster, but possible db corruption)
```

Once a configuration is set during `start`, it will be reused by subsequent commands
(`stop`, `status`, `upgrade`, `user`, etc) and removed during destroy.
The configuration usage information is stored in `config/.last_deploy.`

## Deployment configurations
There are three configurations
- noproxy: for local testing
- staging: for deployment onto our staging server at `daedalus.dev.dide.ic.ac.uk`
- prod: tbd!