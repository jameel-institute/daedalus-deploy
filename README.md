# daedalus-deploy
Deploy tool for the Daedalus app

## Installation
You should create a suitable virtual environment for installing the tool:
```
python3 -m venv daedalus-venv
```
...and activate it:
```
source daedalus-venv/bin/activate
```
(You can deactivate the venv later if required with `deactivate`.)

With the venv activated, clone this repo and install dependencies with:
```
pip3 install -r requirements.txt./d
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
- fakeproxy: for local testing
- staging: for deployment onto our staging server at `daedalus.dev.dide.ic.ac.uk`
- prod: tbd!