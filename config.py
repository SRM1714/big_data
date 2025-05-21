# config.py

# Model options available in Ollama
MODEL_OPTIONS = [
    "llama3",
    "mistral",
    "tinyllama",
    "llama2",
    "phi",
    "gpt4.1"
]

# Selected model (will be overwritten by main.py if args used)
MODEL_NAME = "llama3"

# Dataset structure, ora con nome del database **e** dello schema
DATASETS = {
    "oncomx": {
        "dev": "data/oncomx/dev.json",
        "tables": "data/oncomx/tables.json",
        "db": "oncomx_v1_0_25",
        "schema": "oncomx_v1_0_25"
    },
    "cordis": {
        "dev": "data/cordis/dev.json",
        "tables": "data/cordis/tables.json",
        "db": "cordis_temporary",
        "schema": "unics_cordis"
    },
    "sdss": {
        "dev": "data/sdss/dev.json",
        "tables": "data/sdss/tables.json",
        "db": "skyserver_dr16_2020_11_30",
        "schema": "lite"
    }
}
