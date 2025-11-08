# Data Synchronizing Facade
This Project provides a Flask Application for receiving and transforming asynchronous data via LoRa and providing it synchronous 

## Prerequirements
This project is build using the uv package manager.
Specifically the uv package manager at version 0.9.3 
If you want to build and run this project, i recommend using it too.

You can install uv using either pip:
```shell
pip install uv==0.9.3
```
or command line arguments in windows:
```shell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.9.3/install.ps1 | iex"
```

in unix based os:
```shell
curl -LsSf https://astral.sh/uv/0.9.3/install.sh | sh
```

## setup the project
after you have installed the uv package manager, the project can be setup by using:
```shell
uv sync
```

## run the project
To run the project, use the following command
```shell
uv run -m flask --app src.main run --no-reload
```