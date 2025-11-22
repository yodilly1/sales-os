"""
Competitor Service - Manages competitor database and intelligence.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ...models.battlecard import (
    Competitor,
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorStrength,
    CompetitorWeakness,
    CompetitorListResponse,
)


class CompetitorService:
    """
    Service for managing competitor database.

    Provides CRUD operations and intelligence gathering for competitors.
    Data is persisted to JSON files for simplicity (can be migrated to DB).
    """

    def __init__(self, data_dir: str = "data/reference/competitors"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.competitors_file = self.data_dir / "competitors.json"
        self._ensure_data_file()

    def _ensure_data_file(self) -> None:
        """Ensure the competitors data file exists."""
        if not self.competitors_file.exists():
            self._save_competitors([])

    def _load_competitors(self) -> list[dict]:
        """Load competitors from JSON file."""
        try:
            with open(self.competitors_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_competitors(self, competitors: list[dict]) -> None:
        """Save competitors to JSON file."""
        with open(self.competitors_file, "w") as f:
            json.dump(competitors, f, indent=2, default=str)

    def _competitor_to_dict(self, competitor: Competitor) -> dict:
        """Convert Competitor model to dict for storage."""
        return competitor.model_dump()

    def _dict_to_competitor(self, data: dict) -> Competitor:
        """Convert dict to Competitor model."""
        return Competitor(**data)

    def create(self, competitor_data: CompetitorCreate) -> Competitor:
        """
        Create a new competitor.

        Args:
            competitor_data: Competitor creation data

        Returns:
            Created Competitor instance
        """
        competitors = self._load_competitors()

        # Check for duplicate name
        for c in competitors:
            if c["name"].lower() == competitor_data.name.lower():
                raise ValueError(f"Competitor '{competitor_data.name}' already exists")

        competitor = Competitor(
            id=str(uuid.uuid4()),
            name=competitor_data.name,
            website=competitor_data.website,
            description=competitor_data.description,
            target_market=competitor_data.target_market,
            pricing_model=competitor_data.pricing_model,
            key_products=competitor_data.key_products,
            strengths=[],
            weaknesses=[],
            common_objections=[],
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
        )

        competitors.append(self._competitor_to_dict(competitor))
        self._save_competitors(competitors)

        return competitor

    def get(self, competitor_id: str) -> Optional[Competitor]:
        """
        Get a competitor by ID.

        Args:
            competitor_id: The competitor's ID

        Returns:
            Competitor instance or None if not found
        """
        competitors = self._load_competitors()
        for c in competitors:
            if c["id"] == competitor_id:
                return self._dict_to_competitor(c)
        return None

    def get_by_name(self, name: str) -> Optional[Competitor]:
        """
        Get a competitor by name (case-insensitive).

        Args:
            name: Competitor name

        Returns:
            Competitor instance or None if not found
        """
        competitors = self._load_competitors()
        for c in competitors:
            if c["name"].lower() == name.lower():
                return self._dict_to_competitor(c)
        return None

    def list(
        self,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> CompetitorListResponse:
        """
        List competitors with optional filtering.

        Args:
            search: Optional search term for name/description
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            CompetitorListResponse with competitors and total count
        """
        competitors = self._load_competitors()

        # Apply search filter
        if search:
            search_lower = search.lower()
            competitors = [
                c for c in competitors
                if search_lower in c["name"].lower()
                or search_lower in c.get("description", "").lower()
            ]

        total = len(competitors)

        # Apply pagination
        competitors = competitors[offset:offset + limit]

        return CompetitorListResponse(
            success=True,
            competitors=[self._dict_to_competitor(c) for c in competitors],
            total=total,
        )

    def update(
        self,
        competitor_id: str,
        update_data: CompetitorUpdate,
    ) -> Optional[Competitor]:
        """
        Update an existing competitor.

        Args:
            competitor_id: The competitor's ID
            update_data: Fields to update

        Returns:
            Updated Competitor instance or None if not found
        """
        competitors = self._load_competitors()

        for i, c in enumerate(competitors):
            if c["id"] == competitor_id:
                # Update only provided fields
                update_dict = update_data.model_dump(exclude_none=True)
                for key, value in update_dict.items():
                    if value is not None:
                        if key in ("strengths", "weaknesses"):
                            # Convert Pydantic models to dicts
                            c[key] = [
                                item.model_dump() if hasattr(item, "model_dump") else item
                                for item in value
                            ]
                        else:
                            c[key] = value

                c["last_updated"] = datetime.utcnow().isoformat()
                competitors[i] = c
                self._save_competitors(competitors)

                return self._dict_to_competitor(c)

        return None

    def delete(self, competitor_id: str) -> bool:
        """
        Delete a competitor.

        Args:
            competitor_id: The competitor's ID

        Returns:
            True if deleted, False if not found
        """
        competitors = self._load_competitors()
        original_count = len(competitors)

        competitors = [c for c in competitors if c["id"] != competitor_id]

        if len(competitors) < original_count:
            self._save_competitors(competitors)
            return True

        return False

    def add_strength(
        self,
        competitor_id: str,
        strength: CompetitorStrength,
    ) -> Optional[Competitor]:
        """
        Add a strength to a competitor.

        Args:
            competitor_id: The competitor's ID
            strength: The strength to add

        Returns:
            Updated Competitor or None if not found
        """
        competitors = self._load_competitors()

        for i, c in enumerate(competitors):
            if c["id"] == competitor_id:
                if "strengths" not in c:
                    c["strengths"] = []
                c["strengths"].append(strength.model_dump())
                c["last_updated"] = datetime.utcnow().isoformat()
                competitors[i] = c
                self._save_competitors(competitors)
                return self._dict_to_competitor(c)

        return None

    def add_weakness(
        self,
        competitor_id: str,
        weakness: CompetitorWeakness,
    ) -> Optional[Competitor]:
        """
        Add a weakness to a competitor.

        Args:
            competitor_id: The competitor's ID
            weakness: The weakness to add

        Returns:
            Updated Competitor or None if not found
        """
        competitors = self._load_competitors()

        for i, c in enumerate(competitors):
            if c["id"] == competitor_id:
                if "weaknesses" not in c:
                    c["weaknesses"] = []
                c["weaknesses"].append(weakness.model_dump())
                c["last_updated"] = datetime.utcnow().isoformat()
                competitors[i] = c
                self._save_competitors(competitors)
                return self._dict_to_competitor(c)

        return None

    def update_win_rate(
        self,
        competitor_id: str,
        win_rate: float,
    ) -> Optional[Competitor]:
        """
        Update the win rate against a competitor.

        Args:
            competitor_id: The competitor's ID
            win_rate: Win rate percentage (0-100)

        Returns:
            Updated Competitor or None if not found
        """
        if not 0 <= win_rate <= 100:
            raise ValueError("Win rate must be between 0 and 100")

        competitors = self._load_competitors()

        for i, c in enumerate(competitors):
            if c["id"] == competitor_id:
                c["win_rate_against"] = win_rate
                c["last_updated"] = datetime.utcnow().isoformat()
                competitors[i] = c
                self._save_competitors(competitors)
                return self._dict_to_competitor(c)

        return None

    def add_objection(
        self,
        competitor_id: str,
        objection: str,
    ) -> Optional[Competitor]:
        """
        Add a common objection when competing against this competitor.

        Args:
            competitor_id: The competitor's ID
            objection: The objection text

        Returns:
            Updated Competitor or None if not found
        """
        competitors = self._load_competitors()

        for i, c in enumerate(competitors):
            if c["id"] == competitor_id:
                if "common_objections" not in c:
                    c["common_objections"] = []
                if objection not in c["common_objections"]:
                    c["common_objections"].append(objection)
                    c["last_updated"] = datetime.utcnow().isoformat()
                    competitors[i] = c
                    self._save_competitors(competitors)
                return self._dict_to_competitor(c)

        return None

    def get_all_for_comparison(self, competitor_ids: list[str]) -> list[Competitor]:
        """
        Get multiple competitors for feature comparison.

        Args:
            competitor_ids: List of competitor IDs

        Returns:
            List of Competitor instances
        """
        competitors = self._load_competitors()
        result = []

        for c in competitors:
            if c["id"] in competitor_ids:
                result.append(self._dict_to_competitor(c))

        return result

    def search_by_market(self, market: str) -> list[Competitor]:
        """
        Find competitors targeting a specific market.

        Args:
            market: Target market to search for

        Returns:
            List of matching competitors
        """
        competitors = self._load_competitors()
        market_lower = market.lower()

        return [
            self._dict_to_competitor(c)
            for c in competitors
            if market_lower in c.get("target_market", "").lower()
        ]
