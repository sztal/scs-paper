.PHONY: help env install-gt install networks data clean clean-build clean-pyc

help:
	@echo "env - set up conda environment"
	@echo "install-gt - install graph tool (required only for downloading networks)"
	@echo "install - setup local package and other dependencies including the pathcensus package"
	@echo "networks-domains - download networks for '1-domains' analysis (requires 'graph_tool')"
	@echo "networks-social - download networks for '2-social' analysis (requires 'graph_tool')"
	@echo "networks-proteins - download networks for '3-proteins' analysis (requires 'graph_tool')"
	@echo "networks - fetch all network datasets (requires 'graph_tool')"
	@echo "data-domains - prepare data for '1-domains' analysis"
	@echo "data-social - prepare data for '2-social' analysis"
	@echo "data-proteins - prepare data for '3-proteins' analysis"
	@echo "data-descriptive - prepare data for '4-descriptive' analysis."
	@echo "data-performance - prepare data for '5-performance' analysis."
	@echo "data - prepare data for analyses"
	@echo "clean - remove auxiliary files and runtime/compilation artifacts"
	@echo "clean-build - clean build artifacts"
	@echo "clean-pyc - clean Python artifacts"

env:
	conda create --yes --name scs-paper python=3.10

install-gt:
	conda install --yes -c conda-forge graph-tool
	conda install --yes zstandard

install:
	pip install -r requirements.txt

networks-domains:
	python analyses/1-domains/fetch_networks.py

networks-social:
	python analyses/2-social/fetch_networks.py

networks-proteins:
	python analyses/3-proteins/fetch_networks.py

networks: networks-domains networks-social networks-proteins

data-domains:
	python analyses/1-domains/prepare_data.py

data-social:
	python analyses/2-social/prepare_data.py

data-proteins:
	python analyses/3-proteins/prepare_data.py

data-descriptive:
	python analyses/4-descriptive/prepare_data.py

data-performance:
	python analyses/5-performance/prepare_data.py

data: data-domains data-social data-proteins data-descriptive data-performance

clean: clean-build clean-py

clean-build:
	rm -fr build/
	rm -fr dist/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.eggs' -exec rm -rf {} +

clean-py:
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*.nbc' -exec rm -f {} +
	find . -name '*.nbi' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
