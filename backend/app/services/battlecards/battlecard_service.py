"""
Battlecard Service - Main service for battlecard management.

Handles CRUD operations, versioning, sharing, and favorites for battlecards.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ...models.battlecard import (
    Battlecard,
    BattlecardType,
    BattlecardStatus,
    BattlecardContent,
    BattlecardVersion,
    BattlecardGenerateRequest,
    BattlecardUpdateRequest,
    BattlecardResponse,
    BattlecardListResponse,
    BattlecardSearchRequest,
    BattlecardExportRequest,
    BattlecardExportFormat,
)
from .competitor_service import CompetitorService
from .generator import BattlecardGenerator


class BattlecardService:
    """
    Main service for battlecard operations.

    Provides:
    - CRUD operations for battlecards
    - Generation of new battlecards using AI
    - Version history management
    - Team sharing and favorites
    - Export functionality
    """

    def __init__(
        self,
        data_dir: str = "data/reference/competitors",
        prompts_dir: str = "claude/prompts",
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.battlecards_file = self.data_dir / "battlecards.json"

        self.competitor_service = CompetitorService(data_dir)
        self.generator = BattlecardGenerator(prompts_dir)

        self._ensure_data_file()

    def _ensure_data_file(self) -> None:
        """Ensure the battlecards data file exists."""
        if not self.battlecards_file.exists():
            self._save_battlecards([])

    def _load_battlecards(self) -> List[dict]:
        """Load battlecards from JSON file."""
        try:
            with open(self.battlecards_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_battlecards(self, battlecards: List[dict]) -> None:
        """Save battlecards to JSON file."""
        with open(self.battlecards_file, "w") as f:
            json.dump(battlecards, f, indent=2, default=str)

    def _battlecard_to_dict(self, battlecard: Battlecard) -> dict:
        """Convert Battlecard model to dict for storage."""
        return battlecard.model_dump()

    def _dict_to_battlecard(self, data: dict) -> Battlecard:
        """Convert dict to Battlecard model."""
        return Battlecard(**data)

    async def generate(
        self,
        request: BattlecardGenerateRequest,
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
    ) -> BattlecardResponse:
        """
        Generate a new battlecard using AI.

        Args:
            request: Generation request with type and context
            user_id: ID of user creating the battlecard
            team_id: Team ID for the battlecard

        Returns:
            BattlecardResponse with the generated battlecard
        """
        try:
            # Get competitor if specified
            competitor = None
            competitors = []
            competitor_ids = []

            if request.competitor_id:
                competitor = self.competitor_service.get(request.competitor_id)
                if competitor:
                    competitor_ids.append(request.competitor_id)
            elif request.competitor_name:
                competitor = self.competitor_service.get_by_name(request.competitor_name)
                if competitor:
                    competitor_ids.append(competitor.id)

            if request.competitors_to_compare:
                for name in request.competitors_to_compare:
                    c = self.competitor_service.get_by_name(name)
                    if c:
                        competitors.append(c)
                        competitor_ids.append(c.id)

            # Generate content
            content = await self.generator.generate(
                request=request,
                competitor=competitor,
                competitors=competitors if competitors else None,
                product_info={"context": request.product_context} if request.product_context else None,
            )

            # Create battlecard
            now = datetime.utcnow()
            battlecard = Battlecard(
                id=str(uuid.uuid4()),
                title=request.title,
                type=request.type,
                status=BattlecardStatus.PUBLISHED if request.auto_publish else BattlecardStatus.DRAFT,
                description=request.additional_context,
                content=content,
                tags=[],
                created_by=user_id,
                team_id=team_id,
                is_shared=False,
                version=1,
                version_history=[],
                competitor_ids=competitor_ids,
                created_at=now,
                last_updated=now,
            )

            # Save battlecard
            battlecards = self._load_battlecards()
            battlecards.append(self._battlecard_to_dict(battlecard))
            self._save_battlecards(battlecards)

            return BattlecardResponse(
                success=True,
                battlecard=battlecard,
                message="Battlecard generated successfully",
            )

        except Exception as e:
            return BattlecardResponse(
                success=False,
                battlecard=None,
                message=f"Failed to generate battlecard: {str(e)}",
            )

    def get(self, battlecard_id: str) -> Optional[Battlecard]:
        """
        Get a battlecard by ID.

        Args:
            battlecard_id: The battlecard's ID

        Returns:
            Battlecard instance or None if not found
        """
        battlecards = self._load_battlecards()
        for bc in battlecards:
            if bc["id"] == battlecard_id:
                # Increment view count
                bc["view_count"] = bc.get("view_count", 0) + 1
                self._save_battlecards(battlecards)
                return self._dict_to_battlecard(bc)
        return None

    def list(
        self,
        request: Optional[BattlecardSearchRequest] = None,
    ) -> BattlecardListResponse:
        """
        List battlecards with optional filtering.

        Args:
            request: Search/filter request

        Returns:
            BattlecardListResponse with battlecards and pagination
        """
        battlecards = self._load_battlecards()

        if request:
            # Apply filters
            if request.query:
                query_lower = request.query.lower()
                battlecards = [
                    bc for bc in battlecards
                    if query_lower in bc.get("title", "").lower()
                    or query_lower in bc.get("description", "").lower()
                ]

            if request.type:
                battlecards = [
                    bc for bc in battlecards
                    if bc.get("type") == request.type.value
                ]

            if request.status:
                battlecards = [
                    bc for bc in battlecards
                    if bc.get("status") == request.status.value
                ]

            if request.competitor_id:
                battlecards = [
                    bc for bc in battlecards
                    if request.competitor_id in bc.get("competitor_ids", [])
                ]

            if request.tags:
                battlecards = [
                    bc for bc in battlecards
                    if any(tag in bc.get("tags", []) for tag in request.tags)
                ]

            if request.favorites_only and request.team_id:
                # This would filter to favorites - simplified for now
                pass

            if request.team_id:
                battlecards = [
                    bc for bc in battlecards
                    if bc.get("team_id") == request.team_id
                    or request.team_id in bc.get("shared_with_teams", [])
                ]

            # Pagination
            page = request.page
            page_size = request.page_size
        else:
            page = 1
            page_size = 20

        total = len(battlecards)
        offset = (page - 1) * page_size
        battlecards = battlecards[offset:offset + page_size]

        return BattlecardListResponse(
            success=True,
            battlecards=[self._dict_to_battlecard(bc) for bc in battlecards],
            total=total,
            page=page,
            page_size=page_size,
        )

    def update(
        self,
        battlecard_id: str,
        request: BattlecardUpdateRequest,
        user_id: Optional[str] = None,
    ) -> BattlecardResponse:
        """
        Update an existing battlecard.

        Args:
            battlecard_id: The battlecard's ID
            request: Update request
            user_id: ID of user making the update

        Returns:
            BattlecardResponse with updated battlecard
        """
        battlecards = self._load_battlecards()

        for i, bc in enumerate(battlecards):
            if bc["id"] == battlecard_id:
                # Create version snapshot before updating
                old_version = BattlecardVersion(
                    version=bc.get("version", 1),
                    created_at=datetime.fromisoformat(bc.get("last_updated", datetime.utcnow().isoformat())),
                    created_by=user_id or "system",
                    change_summary="Update before version " + str(bc.get("version", 1) + 1),
                    content_snapshot=bc.get("content", {}),
                )

                # Update fields
                update_dict = request.model_dump(exclude_none=True)
                for key, value in update_dict.items():
                    if key == "content" and value:
                        bc["content"] = value.model_dump()
                    else:
                        bc[key] = value

                # Update version
                bc["version"] = bc.get("version", 1) + 1
                bc["last_updated"] = datetime.utcnow().isoformat()

                # Add to version history
                if "version_history" not in bc:
                    bc["version_history"] = []
                bc["version_history"].append(old_version.model_dump())

                battlecards[i] = bc
                self._save_battlecards(battlecards)

                return BattlecardResponse(
                    success=True,
                    battlecard=self._dict_to_battlecard(bc),
                    message="Battlecard updated successfully",
                )

        return BattlecardResponse(
            success=False,
            battlecard=None,
            message="Battlecard not found",
        )

    def delete(self, battlecard_id: str) -> bool:
        """
        Delete a battlecard.

        Args:
            battlecard_id: The battlecard's ID

        Returns:
            True if deleted, False if not found
        """
        battlecards = self._load_battlecards()
        original_count = len(battlecards)

        battlecards = [bc for bc in battlecards if bc["id"] != battlecard_id]

        if len(battlecards) < original_count:
            self._save_battlecards(battlecards)
            return True

        return False

    def share(
        self,
        battlecard_id: str,
        team_ids: List[str],
    ) -> BattlecardResponse:
        """
        Share a battlecard with teams.

        Args:
            battlecard_id: The battlecard's ID
            team_ids: List of team IDs to share with

        Returns:
            BattlecardResponse with updated battlecard
        """
        battlecards = self._load_battlecards()

        for i, bc in enumerate(battlecards):
            if bc["id"] == battlecard_id:
                bc["is_shared"] = True
                existing_teams = set(bc.get("shared_with_teams", []))
                existing_teams.update(team_ids)
                bc["shared_with_teams"] = list(existing_teams)
                bc["last_updated"] = datetime.utcnow().isoformat()

                battlecards[i] = bc
                self._save_battlecards(battlecards)

                return BattlecardResponse(
                    success=True,
                    battlecard=self._dict_to_battlecard(bc),
                    message="Battlecard shared successfully",
                )

        return BattlecardResponse(
            success=False,
            battlecard=None,
            message="Battlecard not found",
        )

    def unshare(
        self,
        battlecard_id: str,
        team_ids: List[str],
    ) -> BattlecardResponse:
        """
        Unshare a battlecard from teams.

        Args:
            battlecard_id: The battlecard's ID
            team_ids: List of team IDs to unshare from

        Returns:
            BattlecardResponse with updated battlecard
        """
        battlecards = self._load_battlecards()

        for i, bc in enumerate(battlecards):
            if bc["id"] == battlecard_id:
                existing_teams = set(bc.get("shared_with_teams", []))
                existing_teams -= set(team_ids)
                bc["shared_with_teams"] = list(existing_teams)
                bc["is_shared"] = len(bc["shared_with_teams"]) > 0
                bc["last_updated"] = datetime.utcnow().isoformat()

                battlecards[i] = bc
                self._save_battlecards(battlecards)

                return BattlecardResponse(
                    success=True,
                    battlecard=self._dict_to_battlecard(bc),
                    message="Battlecard unshared successfully",
                )

        return BattlecardResponse(
            success=False,
            battlecard=None,
            message="Battlecard not found",
        )

    def toggle_favorite(
        self,
        battlecard_id: str,
        user_id: str,
    ) -> BattlecardResponse:
        """
        Toggle favorite status for a user.

        Args:
            battlecard_id: The battlecard's ID
            user_id: User ID to toggle favorite for

        Returns:
            BattlecardResponse with updated battlecard
        """
        battlecards = self._load_battlecards()

        for i, bc in enumerate(battlecards):
            if bc["id"] == battlecard_id:
                favorited_by = set(bc.get("favorited_by", []))
                if user_id in favorited_by:
                    favorited_by.remove(user_id)
                    message = "Removed from favorites"
                else:
                    favorited_by.add(user_id)
                    message = "Added to favorites"

                bc["favorited_by"] = list(favorited_by)
                battlecards[i] = bc
                self._save_battlecards(battlecards)

                return BattlecardResponse(
                    success=True,
                    battlecard=self._dict_to_battlecard(bc),
                    message=message,
                )

        return BattlecardResponse(
            success=False,
            battlecard=None,
            message="Battlecard not found",
        )

    def get_favorites(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> BattlecardListResponse:
        """
        Get a user's favorite battlecards.

        Args:
            user_id: User ID to get favorites for
            page: Page number
            page_size: Results per page

        Returns:
            BattlecardListResponse with favorite battlecards
        """
        battlecards = self._load_battlecards()

        favorites = [
            bc for bc in battlecards
            if user_id in bc.get("favorited_by", [])
        ]

        total = len(favorites)
        offset = (page - 1) * page_size
        favorites = favorites[offset:offset + page_size]

        return BattlecardListResponse(
            success=True,
            battlecards=[self._dict_to_battlecard(bc) for bc in favorites],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_version_history(
        self,
        battlecard_id: str,
    ) -> List[BattlecardVersion]:
        """
        Get version history for a battlecard.

        Args:
            battlecard_id: The battlecard's ID

        Returns:
            List of BattlecardVersion entries
        """
        battlecard = self.get(battlecard_id)
        if battlecard:
            return battlecard.version_history
        return []

    def restore_version(
        self,
        battlecard_id: str,
        version_number: int,
        user_id: Optional[str] = None,
    ) -> BattlecardResponse:
        """
        Restore a battlecard to a previous version.

        Args:
            battlecard_id: The battlecard's ID
            version_number: Version number to restore
            user_id: User performing the restore

        Returns:
            BattlecardResponse with restored battlecard
        """
        battlecards = self._load_battlecards()

        for i, bc in enumerate(battlecards):
            if bc["id"] == battlecard_id:
                # Find the version
                version_history = bc.get("version_history", [])
                target_version = None
                for v in version_history:
                    if v["version"] == version_number:
                        target_version = v
                        break

                if not target_version:
                    return BattlecardResponse(
                        success=False,
                        battlecard=None,
                        message=f"Version {version_number} not found",
                    )

                # Create version snapshot before restoring
                old_version = BattlecardVersion(
                    version=bc.get("version", 1),
                    created_at=datetime.utcnow(),
                    created_by=user_id or "system",
                    change_summary=f"Before restoring to version {version_number}",
                    content_snapshot=bc.get("content", {}),
                )
                bc["version_history"].append(old_version.model_dump())

                # Restore content
                bc["content"] = target_version["content_snapshot"]
                bc["version"] = bc.get("version", 1) + 1
                bc["last_updated"] = datetime.utcnow().isoformat()

                battlecards[i] = bc
                self._save_battlecards(battlecards)

                return BattlecardResponse(
                    success=True,
                    battlecard=self._dict_to_battlecard(bc),
                    message=f"Restored to version {version_number}",
                )

        return BattlecardResponse(
            success=False,
            battlecard=None,
            message="Battlecard not found",
        )

    async def refresh_from_win_loss(
        self,
        battlecard_id: str,
        win_loss_data: List[dict],
    ) -> BattlecardResponse:
        """
        Refresh a battlecard with new win/loss data.

        Args:
            battlecard_id: The battlecard's ID
            win_loss_data: New win/loss data

        Returns:
            BattlecardResponse with updated battlecard
        """
        battlecard = self.get(battlecard_id)
        if not battlecard:
            return BattlecardResponse(
                success=False,
                battlecard=None,
                message="Battlecard not found",
            )

        # Update content with new data
        updated_content = await self.generator.refresh_from_data(
            battlecard.type,
            battlecard.content,
            {"win_loss_data": win_loss_data},
        )

        return self.update(
            battlecard_id,
            BattlecardUpdateRequest(content=updated_content),
        )

    def export(
        self,
        request: BattlecardExportRequest,
    ) -> dict:
        """
        Export a battlecard in the specified format.

        Args:
            request: Export request with format

        Returns:
            Dict with export data or error
        """
        battlecard = self.get(request.battlecard_id)
        if not battlecard:
            return {"success": False, "error": "Battlecard not found"}

        if request.format == BattlecardExportFormat.JSON:
            data = battlecard.model_dump()
            if not request.include_version_history:
                data.pop("version_history", None)
            return {"success": True, "data": data, "content_type": "application/json"}

        elif request.format == BattlecardExportFormat.MARKDOWN:
            md = self._to_markdown(battlecard)
            return {"success": True, "data": md, "content_type": "text/markdown"}

        elif request.format == BattlecardExportFormat.HTML:
            html = self._to_html(battlecard)
            return {"success": True, "data": html, "content_type": "text/html"}

        elif request.format == BattlecardExportFormat.PDF:
            # PDF generation would require additional library
            return {
                "success": False,
                "error": "PDF export requires rendering service",
            }

        return {"success": False, "error": "Unsupported format"}

    def _to_markdown(self, battlecard: Battlecard) -> str:
        """Convert battlecard to markdown format."""
        lines = [
            f"# {battlecard.title}",
            "",
            f"**Type:** {battlecard.type.value}",
            f"**Status:** {battlecard.status.value}",
            f"**Version:** {battlecard.version}",
            "",
        ]

        if battlecard.description:
            lines.extend([battlecard.description, ""])

        content = battlecard.content

        if content.competitive:
            c = content.competitive
            lines.extend([
                "## Competitive Intelligence",
                "",
                f"### vs. {c.competitor_name}",
                "",
                c.competitor_overview,
                "",
                "### Our Positioning",
                c.our_positioning,
                "",
                "### Key Differentiators",
            ])
            for d in c.key_differentiators:
                lines.append(f"- {d}")
            lines.append("")

            lines.append("### Talking Points")
            for tp in c.talking_points:
                lines.append(f"- **{tp.category}:** {tp.point}")
            lines.append("")

            lines.append("### Landmine Questions")
            for lm in c.landmines:
                lines.append(f"- {lm}")
            lines.append("")

        if content.objection_handling:
            oh = content.objection_handling
            lines.extend([
                "## Objection Handling",
                "",
                f"**Context:** {oh.context}",
                "",
            ])
            for obj in oh.objections:
                lines.extend([
                    f"### \"{obj.objection}\"",
                    "",
                    f"**Category:** {obj.category} | **Severity:** {obj.severity}",
                    "",
                    f"**Root Cause:** {obj.root_cause}",
                    "",
                    "**Response:**",
                    f"- Acknowledge: {obj.response.acknowledge}",
                    f"- Clarify: {obj.response.clarify}",
                    f"- Respond: {obj.response.respond}",
                    f"- Redirect: {obj.response.redirect}",
                    "",
                ])

        if content.feature_comparison:
            fc = content.feature_comparison
            lines.extend([
                "## Feature Comparison",
                "",
                fc.summary,
                "",
                "### Key Advantages",
            ])
            for adv in fc.key_advantages:
                lines.append(f"- {adv}")
            lines.append("")

        if content.win_loss_analysis:
            wl = content.win_loss_analysis
            lines.extend([
                "## Win/Loss Analysis",
                "",
                f"**Period:** {wl.analysis_period}",
                f"**Deals Analyzed:** {wl.total_deals_analyzed}",
                f"**Win Rate:** {wl.win_rate}%",
                "",
                "### Top Win Factors",
            ])
            for f in wl.top_win_factors:
                lines.append(f"- **{f.factor}** ({f.impact}): {f.description}")
            lines.extend(["", "### Recommendations"])
            for r in wl.recommendations:
                lines.append(f"- {r}")
            lines.append("")

        return "\n".join(lines)

    def _to_html(self, battlecard: Battlecard) -> str:
        """Convert battlecard to HTML format (print-friendly)."""
        # Simple HTML conversion - in production would use templates
        md = self._to_markdown(battlecard)

        # Basic markdown to HTML conversion
        html_content = md
        html_content = html_content.replace("# ", "<h1>").replace("\n## ", "</h1>\n<h2>")
        html_content = html_content.replace("\n### ", "</h2>\n<h3>")
        html_content = html_content.replace("\n- ", "</h3>\n<li>")

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{battlecard.title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #1a1a1a; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 30px; }}
        h3 {{ color: #555; }}
        li {{ margin: 5px 0; }}
        .meta {{ color: #666; font-size: 0.9em; }}
        @media print {{
            body {{ padding: 20px; }}
            h2 {{ page-break-before: auto; }}
        }}
    </style>
</head>
<body>
    <div class="meta">
        <strong>Type:</strong> {battlecard.type.value} |
        <strong>Version:</strong> {battlecard.version} |
        <strong>Status:</strong> {battlecard.status.value}
    </div>
    {html_content}
</body>
</html>"""
