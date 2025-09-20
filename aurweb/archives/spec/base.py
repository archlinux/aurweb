from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


class GitInfo:
    """Information about a Git repository."""

    """ Path to Git repository. """
    path: str

    """ Local Git repository configuration. """
    config: Dict[str, Any]

    def __init__(self, path: str, config: Dict[str, Any] = {}) -> None:
        self.path = Path(path)
        self.config = config


class SpecOutput:
    """Class used for git_archive.py output details."""

    """ Filename relative to the Git repository root. """
    filename: Path

    """ Git repository information. """
    git_info: GitInfo

    """ Bytes bound for `SpecOutput.filename`. """
    data: bytes

    def __init__(self, filename: str, git_info: GitInfo, data: bytes) -> None:
        self.filename = filename
        self.git_info = git_info
        self.data = data


class SpecBase:
    """
    Base for Spec classes defined in git_archve.py --spec modules.

    All supported --spec modules must contain the following classes:
    - Spec(SpecBase)
    """

    """ A list of SpecOutputs, each of which contain output file data. """
    outputs: List[SpecOutput] = []

    """ A set of repositories to commit changes to. """
    repos: Set[str] = set()

    def generate(self) -> Iterable[SpecOutput]:
        """
        "Pure virtual" output generator.

        `SpecBase.outputs` and `SpecBase.repos` should be populated within an
        overridden version of this function in SpecBase derivatives.
        """
        raise NotImplementedError

    def add_output(self, filename: str, git_info: GitInfo, data: bytes) -> None:
        """
        Add a SpecOutput instance to the set of outputs.

        :param filename: Filename relative to the git repository root
        :param git_info: GitInfo instance
        :param data: Binary data bound for `filename`
        """
        if git_info.path not in self.repos:
            self.repos.add(git_info.path)

        self.outputs.append(
            SpecOutput(
                filename,
                git_info,
                data,
            )
        )
