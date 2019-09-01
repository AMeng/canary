## Canary

A CLI tool that emits OS events and logs the results as JSON.

### Commands:

#### Create a file
Create an empty file. The file is not automatically deleted.
```
./canary.py file create /tmp/example.txt
```

#### Modify a file
Modify a file by updating its last modified date.
```
./canary.py file modify /tmp/example.txt
```

#### Delete a file
```
./canary.py file delete /tmp/example.txt
```

#### Start a process
Run an executable and immediately terminate it.
Takes optional `--args` to send to the executable.
```
./canary.py process /path/to/executable
```

#### Send a network request
Send a network request to the specified host and port. Takes optional `--protocol`
to specify `tcp` or `udp` and `--data` to send data to the recipient.
```
./canary.py process /path/to/executable.sh
```

### Batching Commands:
A json configuration file can be used to batch any number of commands.
```
./canary.py batch /path/to/configuration.json
```

### Development:
A `Dockerfile` and `Makefile` are provided to ease development.

#### Validate
Validate any changes by running tests and linters.
```
make validate
```

#### Run locally
Run the batch file at `canary.json` on your local machine.
```
make run
```

#### Run in Docker
Run the batch file at `canary.json` in docker (Alpine Linux).
```
make run_docker
```
