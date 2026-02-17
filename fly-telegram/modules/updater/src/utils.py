#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

import git
import os

from database import database

try:
    repo = git.Repo(os.path.dirname(os.path.abspath(__name__)))
    origin = repo.remote("origin")

    repo_initialized = True

except git.exc.InvalidGitRepositoryError:
    repo = git.Repo.init(os.path.dirname(os.path.abspath(__name__)))
    origin = repo.create_remote("origin", database.get("git.origin"))

    repo_initialized = False