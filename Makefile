.PHONY: clean train-nlu train-core cmdline server

.DEFAULT_GOAL := default

TEST_PATH=./

help:
	@echo "    clean"
	@echo "        Remove python artifacts and build artifacts."
	@echo "    train-nlu"
	@echo "        Trains a new nlu model using the projects Rasa NLU config"
	@echo "    train-core"
	@echo "        Trains a new dialogue model using the story training data"
	@echo "    action-server"
	@echo "        Starts the server for custom action."
	@echo "    cmdline"
	@echo "       This will load the assistant in your terminal for you to chat."


clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf docs/_build

action-server:
	python -m rasa_core_sdk.endpoint --actions rasa_data/actions

run-socket:
	# python -m rasa_core_sdk.endpoint --actions rasa_data/actions &
	python -m rasa_core.run -d rasa_data/models/current/dialogue -u rasa_data/models/current/nlu --port 5005 --credentials rasa_data/credentials.yml --endpoints rasa_data/endpoints.yml
