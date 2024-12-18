"""GitHub repository interaction module for version control operations.

This module provides a robust interface for interacting with GitHub repositories,
handling common operations like cloning, fetching, and managing file content across
different commits. It implements safe cleanup and proper error handling.

Key Features:
    - Repository cloning and cleanup
    - Commit-specific content retrieval
    - File content management
    - Automated branch handling

Use cases include:
- Dynamic Desirability (SN13)
"""

import os
import shutil
import subprocess

import bittensor as bt
from typing import Callable

from atom.utils import run_command
from atom.chain.chain_utils import json_reader
from abc import ABC, abstractmethod


class BaseHandler(ABC):
    """Abstract base class for content handlers.
    
    Defines the interface for content handling operations with get/put operations.
    """

    @abstractmethod
    def get(self):
        """Abstract method to retrieve content."""
        pass

    @abstractmethod
    def put(self):
        """Abstract method to store content."""
        pass


class GithubHandler(BaseHandler):
    """Handles GitHub repository operations for content management.
    
    Manages repository cloning, content retrieval, and content storage operations
    while maintaining proper cleanup of temporary files.

    Attributes:
        REPO_URL (str): URL of the GitHub repository
        original_dir (str): Original working directory path
        repo_name (str): Name of the repository
        repo_path (str): Local path where repository is cloned
    """

    def __init__(self, repo_url: str):
        self.REPO_URL = repo_url

        self.original_dir = os.getcwd()
        self.repo_name = self.REPO_URL.split("/")[-1].replace(".git", "")
        self.repo_path = os.path.join(self.original_dir, self.repo_name)

    def clone(self):
        """Clone the repository to local directory.
        
        Clones the repository if it doesn't already exist locally.
        Logs the operation and handles potential Git errors.
        """
        if not os.path.exists(self.repo_path):
            try:
                bt.logging.info(f"Cloning repository: {self.REPO_URL}")
                run_command(command=["git", "clone", self.REPO_URL])
            except subprocess.CalledProcessError as e:
                bt.logging.error(f"An error occurred during Git operations: {e}")

    def fetch_all(self):
        """Fetch all changes from the remote repository.
        
        Updates the local repository with all remote changes.
        Handles potential Git operation errors.
        """
        try:
            bt.logging.info("Fetching latest changes")
            run_command(["git", "fetch", "--all"], cwd=self.repo_path)

        except subprocess.CalledProcessError as e:
            bt.logging.error(f"An error occurred during Git operations: {e}")
            return None

    def get(self, commit_sha: str, filepath: str, reader: Callable = json_reader):
        """Retrieve content from a specific commit.

        Args:
            commit_sha (str): Hash of the target commit
            filepath (str): Path to the target file within repository
            reader (Callable): Function to read and parse the file content.
                Defaults to json_reader

        Returns:
            The file content parsed by the reader function, or None if operation fails

        Note:
            Automatically handles repository cleanup after operation
        """

        try:
            # Clone and fetch all changes from the repo.
            self.clone()
            self.fetch_all()

            bt.logging.info(f"Checking out commit: {commit_sha}")
            subprocess.run(
                ["git", "checkout", commit_sha], check=True, capture_output=True
            )

            if os.path.exists(filepath):
                bt.logging.info(f"File '{filepath}' found. Reading contents...")
                content = reader(filepath)
                return content
            else:
                bt.logging.error(f"File '{filepath}' not found in this commit.")
                return None

        except subprocess.CalledProcessError as e:
            bt.logging.error(f"An error occurred during Git operations: {e}")
            return None
        except IOError as e:
            bt.logging.error(f"An error occurred while reading the file: {e}")
            return None
        finally:
            if os.path.exists(self.repo_path):
                bt.logging.info(
                    f"Deleting the cloned repository folder: {self.repo_name}"
                )
                shutil.rmtree(self.repo_path)

    def put(
        self,
        content: str,
        folder_name: str,
        file_ext: str,
        hotkey: str,
        branch_name: str = "main",
    ) -> str:
        """Store content in the repository.

        Handles the entire process of adding content to the repository:
            1. Clones/updates the repository
            2. Creates necessary folders
            3. Writes content to file
            4. Commits and pushes changes
            5. Verifies push success
            6. Cleans up local files

        Args:
            content (str): Content to store in the file
            folder_name (str): Target folder path in repository
            file_ext (str): File extension (e.g., "json")
            hotkey (str): Validator hotkey used in commit message
            branch_name (str): Target branch name, defaults to "main"

        Returns:
            str: Remote commit hash after successful push

        Note:
            Automatically handles repository cleanup after operation
        """

        self.clone()

        # all the operations will be done in the cloned repository folder.
        os.chdir(self.repo_path)

        bt.logging.info(f"Checking out and updating branch: {branch_name}")
        run_command(["git", "checkout", branch_name])
        run_command(["git", "pull", "origin", branch_name])

        # If for any reason the folder to be written into was deleted, create the folder.
        if not os.path.exists(folder_name):
            bt.logging.info(f"Creating folder: {folder_name}")
            os.mkdir(os.path.join(self.repo_path, folder_name))

        filename = os.path.join(folder_name, f"{hotkey}.{file_ext}")

        bt.logging.info(f"Creating file: {filename}")
        with open(filename, "w") as f:
            f.write(content)

        bt.logging.info("Staging, committing, and pushing changes")

        try:
            run_command(["git", "add", filename])
            run_command(["git", "commit", "-m", f"{hotkey} added file"])
            run_command(["git", "push", "origin", branch_name])
        except subprocess.CalledProcessError:
            bt.logging.warning(
                "What you're currently trying to commit has no differences to your last commit. Proceeding with last commit..."
            )

        bt.logging.info("Retrieving commit hash")
        local_commit_hash = run_command(["git", "rev-parse", "HEAD"])

        run_command(["git", "fetch", "origin", branch_name])
        remote_commit_hash = run_command(["git", "rev-parse", f"origin/{branch_name}"])

        if local_commit_hash == remote_commit_hash:
            bt.logging.info(f"Successfully pushed. Commit hash: {local_commit_hash}")
        else:
            bt.logging.warning("Local and remote commit hashes differ.")
            bt.logging.warning(f"Local commit hash: {local_commit_hash}")
            bt.logging.warning(f"Remote commit hash: {remote_commit_hash}")

        os.chdir("..")
        bt.logging.info(f"Deleting the cloned repository folder: {self.repo_name}")
        shutil.rmtree(self.repo_name)

        return remote_commit_hash
