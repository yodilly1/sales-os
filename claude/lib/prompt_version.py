"""
Prompt Versioning System

Manages prompt versions, metadata, and version history for Claude AI prompts.
Supports semantic versioning and change tracking.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class VersionBump(Enum):
    """Types of version increments."""
    MAJOR = "major"  # Breaking changes to prompt structure/output
    MINOR = "minor"  # New features, backward compatible
    PATCH = "patch"  # Bug fixes, minor improvements


@dataclass
class PromptMetadata:
    """Metadata for a prompt template."""
    name: str
    version: str
    category: str
    description: str
    created_at: datetime
    updated_at: datetime
    author: str = "system"
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "author": self.author,
            "tags": self.tags,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PromptMetadata":
        """Create metadata from dictionary."""
        return cls(
            name=data["name"],
            version=data["version"],
            category=data["category"],
            description=data["description"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            author=data.get("author", "system"),
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", []),
        )


@dataclass
class VersionHistoryEntry:
    """Single entry in version history."""
    version: str
    date: datetime
    changes: str
    content_hash: str
    author: str = "system"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "date": self.date.isoformat(),
            "changes": self.changes,
            "content_hash": self.content_hash,
            "author": self.author,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VersionHistoryEntry":
        """Create from dictionary."""
        return cls(
            version=data["version"],
            date=datetime.fromisoformat(data["date"]),
            changes=data["changes"],
            content_hash=data["content_hash"],
            author=data.get("author", "system"),
        )


class PromptVersion:
    """
    Manages versioning for a prompt template.

    Supports:
    - Semantic versioning (major.minor.patch)
    - Content hashing for change detection
    - Version history tracking
    - Rollback capabilities
    """

    VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

    def __init__(self, version: str = "1.0.0"):
        """Initialize with a version string."""
        self._validate_version(version)
        self._version = version
        self._history: list[VersionHistoryEntry] = []

    @property
    def version(self) -> str:
        """Get current version string."""
        return self._version

    @property
    def major(self) -> int:
        """Get major version number."""
        return int(self._version.split(".")[0])

    @property
    def minor(self) -> int:
        """Get minor version number."""
        return int(self._version.split(".")[1])

    @property
    def patch(self) -> int:
        """Get patch version number."""
        return int(self._version.split(".")[2])

    @property
    def history(self) -> list[VersionHistoryEntry]:
        """Get version history."""
        return self._history.copy()

    def _validate_version(self, version: str) -> None:
        """Validate version string format."""
        if not self.VERSION_PATTERN.match(version):
            raise ValueError(
                f"Invalid version format: {version}. "
                "Expected format: major.minor.patch (e.g., 1.0.0)"
            )

    def bump(self, bump_type: VersionBump) -> str:
        """
        Increment version based on bump type.

        Args:
            bump_type: Type of version increment

        Returns:
            New version string
        """
        major, minor, patch = self.major, self.minor, self.patch

        if bump_type == VersionBump.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif bump_type == VersionBump.MINOR:
            minor += 1
            patch = 0
        elif bump_type == VersionBump.PATCH:
            patch += 1

        self._version = f"{major}.{minor}.{patch}"
        return self._version

    def add_history_entry(
        self,
        changes: str,
        content: str,
        author: str = "system"
    ) -> VersionHistoryEntry:
        """
        Add a new entry to version history.

        Args:
            changes: Description of changes
            content: Current prompt content for hashing
            author: Author of the change

        Returns:
            The created history entry
        """
        content_hash = self._hash_content(content)
        entry = VersionHistoryEntry(
            version=self._version,
            date=datetime.now(),
            changes=changes,
            content_hash=content_hash,
            author=author,
        )
        self._history.append(entry)
        return entry

    def _hash_content(self, content: str) -> str:
        """Generate SHA-256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]

    def has_content_changed(self, new_content: str) -> bool:
        """
        Check if content has changed from last version.

        Args:
            new_content: New content to compare

        Returns:
            True if content differs from last recorded version
        """
        if not self._history:
            return True

        new_hash = self._hash_content(new_content)
        last_hash = self._history[-1].content_hash
        return new_hash != last_hash

    def get_version_at(self, version: str) -> Optional[VersionHistoryEntry]:
        """
        Get history entry for specific version.

        Args:
            version: Version string to look up

        Returns:
            History entry if found, None otherwise
        """
        for entry in self._history:
            if entry.version == version:
                return entry
        return None

    def compare_versions(self, other: str) -> int:
        """
        Compare this version to another.

        Args:
            other: Version string to compare against

        Returns:
            -1 if this < other, 0 if equal, 1 if this > other
        """
        self._validate_version(other)
        other_parts = [int(x) for x in other.split(".")]
        this_parts = [self.major, self.minor, self.patch]

        for this_part, other_part in zip(this_parts, other_parts):
            if this_part < other_part:
                return -1
            if this_part > other_part:
                return 1
        return 0

    def to_dict(self) -> dict:
        """Serialize version info to dictionary."""
        return {
            "current_version": self._version,
            "history": [entry.to_dict() for entry in self._history],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PromptVersion":
        """Deserialize from dictionary."""
        instance = cls(data["current_version"])
        instance._history = [
            VersionHistoryEntry.from_dict(entry)
            for entry in data.get("history", [])
        ]
        return instance

    def __str__(self) -> str:
        return self._version

    def __repr__(self) -> str:
        return f"PromptVersion('{self._version}')"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PromptVersion):
            return self._version == other._version
        if isinstance(other, str):
            return self._version == other
        return False
