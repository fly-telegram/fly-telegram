#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

"""The database from v1"""

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from pathlib import Path
from typing import Any, Dict


class Database(dict):
    def __init__(self, location: str = "database.json"):
        """
        Initializes the database.

        Args:
            location (str): The location of the JSON file.
        """
        self.location = Path(location)
        self.update(**self.load(self.location))

    def load(self, location: Path) -> dict[str, Any]:
        """
        Loads the database from the JSON file.

        Args:
            location (Path): The location of the JSON file.

        Returns:
            Dict[str, Any]: The loaded database.
        """
        if not location.exists():
            return {}
        with location.open("rb") as file:
            return json.load(file)

    def save(self) -> None:
        """
        Saves the database to the JSON file.
        """
        with self.location.open("w") as file:
            json.dump(self, file, indent=2)

        self.update(**self.load(self.location))

    def get(self, *keys):
        """
        Gets a value from the database.

        Args:
            *keys: The keys to access the value.

        Returns:
            Any: The value.
        """
        self.update(**self.load(self.location))

        data = self
        for key in keys:
            if key in data:
                data = data[key]
            else:
                return None
        return data

    def set(self, key: str, value: Any):
        """
        Sets a value in the database.

        Args:
            key (str): The key to set the value.
            value (Any): The value to set.
        """
        self.update(**self.load(self.location))

        self[key] = value
        self.save()

        return self[key]
