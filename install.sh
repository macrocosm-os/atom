# Install poetry
python3.11 -m pip install poetry

# Set the destination of the virtual environment to the project directory
python3.11 -m poetry config virtualenvs.in-project true

# Install the project dependencies
python3.11 -m poetry install

python3.11 -m poetry shell