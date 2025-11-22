"""
Deal Room Service

Core business logic for managing digital deal rooms.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from backend.app.models.dealroom import (
    DealRoom, DealRoomSection, DealRoomContent, ActionPlanItem,
    DealRoomStatus, ContentType, AccessLevel, ActionPlanItemStatus,
    DealRoomCreateRequest, DealRoomUpdateRequest, DealRoomResponse,
    SectionCreateRequest, SectionUpdateRequest, SectionResponse,
    ContentCreateRequest, ContentUpdateRequest, ContentResponse,
    ActionPlanItemCreateRequest, ActionPlanItemUpdateRequest, ActionPlanItemResponse,
    DealRoomBrandingSchema, DealRoomSettingsSchema,
    PublicDealRoomResponse, PublicSectionResponse, PublicContentResponse,
    PublicActionPlanItemResponse,
)
from backend.app.services.dealroom.utils import (
    generate_slug, hash_password, is_expired, get_content_type_icon
)

logger = logging.getLogger(__name__)


class DealRoomService:
    """
    Service for managing deal rooms and their contents.
    """

    def __init__(self, db: Session):
        """
        Initialize the deal room service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # =========================================================================
    # DEAL ROOM CRUD
    # =========================================================================

    def create_deal_room(
        self,
        request: DealRoomCreateRequest,
        owner_id: UUID,
        team_id: Optional[UUID] = None
    ) -> DealRoom:
        """
        Create a new deal room.

        Args:
            request: Creation request with deal room details
            owner_id: UUID of the user creating the deal room
            team_id: Optional team ID for team-based access

        Returns:
            Created DealRoom instance
        """
        # Generate unique slug
        slug = generate_slug(request.title, request.deal_id)

        # Ensure slug is unique
        existing = self.db.query(DealRoom).filter(DealRoom.slug == slug).first()
        if existing:
            slug = generate_slug(request.title)  # Regenerate with new random suffix

        # Create deal room
        deal_room = DealRoom(
            slug=slug,
            title=request.title,
            description=request.description,
            deal_id=request.deal_id,
            deal_name=request.deal_name,
            deal_value=request.deal_value,
            prospect_company=request.prospect_company,
            prospect_name=request.prospect_name,
            prospect_email=request.prospect_email,
            owner_id=owner_id,
            team_id=team_id,
            status=DealRoomStatus.DRAFT,
        )

        # Apply branding if provided
        if request.branding:
            deal_room.logo_url = request.branding.logo_url
            deal_room.primary_color = request.branding.primary_color
            deal_room.secondary_color = request.branding.secondary_color
            deal_room.custom_css = request.branding.custom_css
            deal_room.favicon_url = request.branding.favicon_url

        # Apply settings if provided
        if request.settings:
            deal_room.show_action_plan = request.settings.show_action_plan
            deal_room.show_timeline = request.settings.show_timeline
            deal_room.enable_comments = request.settings.enable_comments
            deal_room.notify_on_view = request.settings.notify_on_view
            deal_room.require_nda = request.settings.require_nda

        # Apply access control if provided
        if request.access_control:
            deal_room.access_level = request.access_control.access_level
            if request.access_control.password:
                deal_room.password_hash = hash_password(request.access_control.password)
            deal_room.expires_at = request.access_control.expires_at
            deal_room.max_views = request.access_control.max_views
            deal_room.allowed_emails = request.access_control.allowed_emails

        self.db.add(deal_room)
        self.db.commit()
        self.db.refresh(deal_room)

        logger.info(f"Created deal room: {deal_room.id} - {deal_room.title}")
        return deal_room

    def get_deal_room(self, deal_room_id: UUID) -> Optional[DealRoom]:
        """
        Get a deal room by ID.

        Args:
            deal_room_id: UUID of the deal room

        Returns:
            DealRoom instance or None
        """
        return self.db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()

    def get_deal_room_by_slug(self, slug: str) -> Optional[DealRoom]:
        """
        Get a deal room by its slug.

        Args:
            slug: URL slug of the deal room

        Returns:
            DealRoom instance or None
        """
        return self.db.query(DealRoom).filter(DealRoom.slug == slug).first()

    def list_deal_rooms(
        self,
        owner_id: Optional[UUID] = None,
        team_id: Optional[UUID] = None,
        status: Optional[DealRoomStatus] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[DealRoom], int]:
        """
        List deal rooms with optional filtering.

        Args:
            owner_id: Filter by owner
            team_id: Filter by team
            status: Filter by status
            search: Search in title/description
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (list of deal rooms, total count)
        """
        query = self.db.query(DealRoom)

        # Apply filters
        if owner_id:
            query = query.filter(DealRoom.owner_id == owner_id)
        if team_id:
            query = query.filter(DealRoom.team_id == team_id)
        if status:
            query = query.filter(DealRoom.status == status)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    DealRoom.title.ilike(search_pattern),
                    DealRoom.description.ilike(search_pattern),
                    DealRoom.prospect_company.ilike(search_pattern),
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        deal_rooms = query.order_by(DealRoom.created_at.desc()) \
                         .offset(offset) \
                         .limit(page_size) \
                         .all()

        return deal_rooms, total

    def update_deal_room(
        self,
        deal_room_id: UUID,
        request: DealRoomUpdateRequest,
    ) -> Optional[DealRoom]:
        """
        Update a deal room.

        Args:
            deal_room_id: UUID of the deal room to update
            request: Update request with new values

        Returns:
            Updated DealRoom or None if not found
        """
        deal_room = self.get_deal_room(deal_room_id)
        if not deal_room:
            return None

        # Update basic fields
        if request.title is not None:
            deal_room.title = request.title
        if request.description is not None:
            deal_room.description = request.description
        if request.deal_id is not None:
            deal_room.deal_id = request.deal_id
        if request.deal_name is not None:
            deal_room.deal_name = request.deal_name
        if request.deal_value is not None:
            deal_room.deal_value = request.deal_value
        if request.prospect_company is not None:
            deal_room.prospect_company = request.prospect_company
        if request.prospect_name is not None:
            deal_room.prospect_name = request.prospect_name
        if request.prospect_email is not None:
            deal_room.prospect_email = request.prospect_email
        if request.status is not None:
            deal_room.status = request.status
            if request.status == DealRoomStatus.ACTIVE and not deal_room.published_at:
                deal_room.published_at = datetime.utcnow()

        # Update branding
        if request.branding:
            deal_room.logo_url = request.branding.logo_url
            deal_room.primary_color = request.branding.primary_color
            deal_room.secondary_color = request.branding.secondary_color
            deal_room.custom_css = request.branding.custom_css
            deal_room.favicon_url = request.branding.favicon_url

        # Update settings
        if request.settings:
            deal_room.show_action_plan = request.settings.show_action_plan
            deal_room.show_timeline = request.settings.show_timeline
            deal_room.enable_comments = request.settings.enable_comments
            deal_room.notify_on_view = request.settings.notify_on_view
            deal_room.require_nda = request.settings.require_nda

        # Update access control
        if request.access_control:
            deal_room.access_level = request.access_control.access_level
            if request.access_control.password:
                deal_room.password_hash = hash_password(request.access_control.password)
            deal_room.expires_at = request.access_control.expires_at
            deal_room.max_views = request.access_control.max_views
            deal_room.allowed_emails = request.access_control.allowed_emails

        deal_room.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(deal_room)

        logger.info(f"Updated deal room: {deal_room.id}")
        return deal_room

    def delete_deal_room(self, deal_room_id: UUID) -> bool:
        """
        Delete a deal room and all its contents.

        Args:
            deal_room_id: UUID of the deal room to delete

        Returns:
            True if deleted, False if not found
        """
        deal_room = self.get_deal_room(deal_room_id)
        if not deal_room:
            return False

        self.db.delete(deal_room)
        self.db.commit()

        logger.info(f"Deleted deal room: {deal_room_id}")
        return True

    def publish_deal_room(self, deal_room_id: UUID) -> Optional[DealRoom]:
        """
        Publish a deal room, making it accessible via its share link.

        Args:
            deal_room_id: UUID of the deal room

        Returns:
            Updated DealRoom or None
        """
        deal_room = self.get_deal_room(deal_room_id)
        if not deal_room:
            return None

        deal_room.status = DealRoomStatus.ACTIVE
        deal_room.published_at = datetime.utcnow()
        deal_room.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(deal_room)

        logger.info(f"Published deal room: {deal_room_id}")
        return deal_room

    def archive_deal_room(self, deal_room_id: UUID) -> Optional[DealRoom]:
        """
        Archive a deal room.

        Args:
            deal_room_id: UUID of the deal room

        Returns:
            Updated DealRoom or None
        """
        deal_room = self.get_deal_room(deal_room_id)
        if not deal_room:
            return None

        deal_room.status = DealRoomStatus.ARCHIVED
        deal_room.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(deal_room)

        logger.info(f"Archived deal room: {deal_room_id}")
        return deal_room

    def duplicate_deal_room(
        self,
        deal_room_id: UUID,
        new_title: str,
        owner_id: UUID,
    ) -> Optional[DealRoom]:
        """
        Duplicate a deal room with all its contents.

        Args:
            deal_room_id: UUID of the deal room to duplicate
            new_title: Title for the new deal room
            owner_id: UUID of the new owner

        Returns:
            New DealRoom or None if original not found
        """
        original = self.get_deal_room(deal_room_id)
        if not original:
            return None

        # Create new deal room
        new_room = DealRoom(
            slug=generate_slug(new_title),
            title=new_title,
            description=original.description,
            deal_id=None,  # Don't copy deal association
            prospect_company=original.prospect_company,
            logo_url=original.logo_url,
            primary_color=original.primary_color,
            secondary_color=original.secondary_color,
            custom_css=original.custom_css,
            favicon_url=original.favicon_url,
            show_action_plan=original.show_action_plan,
            show_timeline=original.show_timeline,
            enable_comments=original.enable_comments,
            notify_on_view=original.notify_on_view,
            require_nda=original.require_nda,
            access_level=original.access_level,
            owner_id=owner_id,
            team_id=original.team_id,
            status=DealRoomStatus.DRAFT,
        )
        self.db.add(new_room)
        self.db.flush()  # Get the new ID

        # Map old section IDs to new ones
        section_map = {}

        # Duplicate sections (handle hierarchy)
        for section in original.sections:
            if section.parent_id is None:  # Top-level sections first
                new_section = self._duplicate_section(section, new_room.id, None, section_map)
                section_map[section.id] = new_section.id

        # Handle nested sections
        for section in original.sections:
            if section.parent_id is not None and section.parent_id in section_map:
                new_section = self._duplicate_section(
                    section, new_room.id, section_map[section.parent_id], section_map
                )
                section_map[section.id] = new_section.id

        # Duplicate contents
        for content in original.contents:
            new_section_id = section_map.get(content.section_id) if content.section_id else None
            self._duplicate_content(content, new_room.id, new_section_id)

        # Duplicate action plan items
        for item in original.action_plan_items:
            self._duplicate_action_plan_item(item, new_room.id)

        self.db.commit()
        self.db.refresh(new_room)

        logger.info(f"Duplicated deal room {deal_room_id} to {new_room.id}")
        return new_room

    def _duplicate_section(
        self,
        section: DealRoomSection,
        new_room_id: UUID,
        new_parent_id: Optional[UUID],
        section_map: dict,
    ) -> DealRoomSection:
        """Duplicate a section."""
        new_section = DealRoomSection(
            deal_room_id=new_room_id,
            parent_id=new_parent_id,
            name=section.name,
            description=section.description,
            icon=section.icon,
            order_index=section.order_index,
            is_collapsed=section.is_collapsed,
        )
        self.db.add(new_section)
        self.db.flush()
        return new_section

    def _duplicate_content(
        self,
        content: DealRoomContent,
        new_room_id: UUID,
        new_section_id: Optional[UUID],
    ) -> DealRoomContent:
        """Duplicate content item."""
        new_content = DealRoomContent(
            deal_room_id=new_room_id,
            section_id=new_section_id,
            title=content.title,
            description=content.description,
            content_type=content.content_type,
            file_url=content.file_url,
            file_name=content.file_name,
            file_size=content.file_size,
            file_mime_type=content.file_mime_type,
            external_link=content.external_link,
            embed_code=content.embed_code,
            thumbnail_url=content.thumbnail_url,
            order_index=content.order_index,
            is_featured=content.is_featured,
            is_pinned=content.is_pinned,
            metadata=content.metadata.copy() if content.metadata else {},
        )
        self.db.add(new_content)
        return new_content

    def _duplicate_action_plan_item(
        self,
        item: ActionPlanItem,
        new_room_id: UUID,
    ) -> ActionPlanItem:
        """Duplicate an action plan item."""
        new_item = ActionPlanItem(
            deal_room_id=new_room_id,
            title=item.title,
            description=item.description,
            status=ActionPlanItemStatus.PENDING,
            owner=item.owner,
            assignee_name=item.assignee_name,
            assignee_email=item.assignee_email,
            due_date=item.due_date,
            order_index=item.order_index,
            is_milestone=item.is_milestone,
        )
        self.db.add(new_item)
        return new_item

    # =========================================================================
    # SECTIONS
    # =========================================================================

    def create_section(
        self,
        deal_room_id: UUID,
        request: SectionCreateRequest,
    ) -> Optional[DealRoomSection]:
        """
        Create a new section in a deal room.

        Args:
            deal_room_id: UUID of the deal room
            request: Section creation request

        Returns:
            Created section or None if deal room not found
        """
        deal_room = self.get_deal_room(deal_room_id)
        if not deal_room:
            return None

        section = DealRoomSection(
            deal_room_id=deal_room_id,
            parent_id=request.parent_id,
            name=request.name,
            description=request.description,
            icon=request.icon,
            order_index=request.order_index,
        )

        self.db.add(section)
        self.db.commit()
        self.db.refresh(section)

        return section

    def get_section(self, section_id: UUID) -> Optional[DealRoomSection]:
        """Get a section by ID."""
        return self.db.query(DealRoomSection).filter(
            DealRoomSection.id == section_id
        ).first()

    def list_sections(self, deal_room_id: UUID) -> List[DealRoomSection]:
        """List all sections in a deal room."""
        return self.db.query(DealRoomSection).filter(
            DealRoomSection.deal_room_id == deal_room_id
        ).order_by(DealRoomSection.order_index).all()

    def update_section(
        self,
        section_id: UUID,
        request: SectionUpdateRequest,
    ) -> Optional[DealRoomSection]:
        """Update a section."""
        section = self.get_section(section_id)
        if not section:
            return None

        if request.name is not None:
            section.name = request.name
        if request.description is not None:
            section.description = request.description
        if request.icon is not None:
            section.icon = request.icon
        if request.parent_id is not None:
            section.parent_id = request.parent_id
        if request.order_index is not None:
            section.order_index = request.order_index
        if request.is_collapsed is not None:
            section.is_collapsed = request.is_collapsed

        section.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(section)

        return section

    def delete_section(self, section_id: UUID) -> bool:
        """Delete a section and move its contents to unsectioned."""
        section = self.get_section(section_id)
        if not section:
            return False

        # Move contents to no section
        for content in section.contents:
            content.section_id = None

        # Move child sections to parent
        for child in section.children:
            child.parent_id = section.parent_id

        self.db.delete(section)
        self.db.commit()

        return True

    def reorder_sections(
        self,
        deal_room_id: UUID,
        section_ids: List[UUID],
    ) -> bool:
        """
        Reorder sections in a deal room.

        Args:
            deal_room_id: UUID of the deal room
            section_ids: List of section IDs in new order

        Returns:
            True if successful
        """
        for index, section_id in enumerate(section_ids):
            section = self.get_section(section_id)
            if section and section.deal_room_id == deal_room_id:
                section.order_index = index

        self.db.commit()
        return True

    # =========================================================================
    # CONTENTS
    # =========================================================================

    def add_content(
        self,
        deal_room_id: UUID,
        request: ContentCreateRequest,
        uploaded_by: Optional[UUID] = None,
    ) -> Optional[DealRoomContent]:
        """
        Add content to a deal room.

        Args:
            deal_room_id: UUID of the deal room
            request: Content creation request
            uploaded_by: UUID of the uploader

        Returns:
            Created content or None
        """
        deal_room = self.get_deal_room(deal_room_id)
        if not deal_room:
            return None

        content = DealRoomContent(
            deal_room_id=deal_room_id,
            section_id=request.section_id,
            title=request.title,
            description=request.description,
            content_type=request.content_type,
            file_url=request.file_url,
            file_name=request.file_name,
            file_size=request.file_size,
            file_mime_type=request.file_mime_type,
            external_link=request.external_link,
            embed_code=request.embed_code,
            thumbnail_url=request.thumbnail_url,
            order_index=request.order_index,
            is_featured=request.is_featured,
            is_pinned=request.is_pinned,
            metadata=request.metadata,
            uploaded_by=uploaded_by,
        )

        self.db.add(content)
        self.db.commit()
        self.db.refresh(content)

        logger.info(f"Added content to deal room {deal_room_id}: {content.title}")
        return content

    def get_content(self, content_id: UUID) -> Optional[DealRoomContent]:
        """Get content by ID."""
        return self.db.query(DealRoomContent).filter(
            DealRoomContent.id == content_id
        ).first()

    def list_contents(
        self,
        deal_room_id: UUID,
        section_id: Optional[UUID] = None,
        content_type: Optional[ContentType] = None,
    ) -> List[DealRoomContent]:
        """List contents in a deal room with optional filters."""
        query = self.db.query(DealRoomContent).filter(
            DealRoomContent.deal_room_id == deal_room_id,
            DealRoomContent.is_hidden == False,
        )

        if section_id is not None:
            query = query.filter(DealRoomContent.section_id == section_id)
        if content_type:
            query = query.filter(DealRoomContent.content_type == content_type)

        return query.order_by(
            DealRoomContent.is_pinned.desc(),
            DealRoomContent.order_index
        ).all()

    def update_content(
        self,
        content_id: UUID,
        request: ContentUpdateRequest,
    ) -> Optional[DealRoomContent]:
        """Update content."""
        content = self.get_content(content_id)
        if not content:
            return None

        if request.title is not None:
            content.title = request.title
        if request.description is not None:
            content.description = request.description
        if request.section_id is not None:
            content.section_id = request.section_id
        if request.file_url is not None:
            content.file_url = request.file_url
            content.version += 1
        if request.external_link is not None:
            content.external_link = request.external_link
        if request.thumbnail_url is not None:
            content.thumbnail_url = request.thumbnail_url
        if request.order_index is not None:
            content.order_index = request.order_index
        if request.is_featured is not None:
            content.is_featured = request.is_featured
        if request.is_pinned is not None:
            content.is_pinned = request.is_pinned
        if request.is_hidden is not None:
            content.is_hidden = request.is_hidden
        if request.metadata is not None:
            content.metadata = request.metadata

        content.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(content)

        return content

    def delete_content(self, content_id: UUID) -> bool:
        """Delete content."""
        content = self.get_content(content_id)
        if not content:
            return False

        self.db.delete(content)
        self.db.commit()

        return True

    def reorder_contents(
        self,
        deal_room_id: UUID,
        content_ids: List[UUID],
    ) -> bool:
        """Reorder contents in a deal room."""
        for index, content_id in enumerate(content_ids):
            content = self.get_content(content_id)
            if content and content.deal_room_id == deal_room_id:
                content.order_index = index

        self.db.commit()
        return True

    # =========================================================================
    # ACTION PLAN
    # =========================================================================

    def add_action_plan_item(
        self,
        deal_room_id: UUID,
        request: ActionPlanItemCreateRequest,
    ) -> Optional[ActionPlanItem]:
        """Add an action plan item."""
        deal_room = self.get_deal_room(deal_room_id)
        if not deal_room:
            return None

        item = ActionPlanItem(
            deal_room_id=deal_room_id,
            title=request.title,
            description=request.description,
            owner=request.owner,
            assignee_name=request.assignee_name,
            assignee_email=request.assignee_email,
            due_date=request.due_date,
            order_index=request.order_index,
            is_milestone=request.is_milestone,
        )

        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        return item

    def get_action_plan_item(self, item_id: UUID) -> Optional[ActionPlanItem]:
        """Get an action plan item by ID."""
        return self.db.query(ActionPlanItem).filter(
            ActionPlanItem.id == item_id
        ).first()

    def list_action_plan_items(self, deal_room_id: UUID) -> List[ActionPlanItem]:
        """List action plan items in a deal room."""
        return self.db.query(ActionPlanItem).filter(
            ActionPlanItem.deal_room_id == deal_room_id
        ).order_by(ActionPlanItem.order_index).all()

    def update_action_plan_item(
        self,
        item_id: UUID,
        request: ActionPlanItemUpdateRequest,
    ) -> Optional[ActionPlanItem]:
        """Update an action plan item."""
        item = self.get_action_plan_item(item_id)
        if not item:
            return None

        if request.title is not None:
            item.title = request.title
        if request.description is not None:
            item.description = request.description
        if request.status is not None:
            item.status = request.status
            if request.status == ActionPlanItemStatus.COMPLETED:
                item.completed_at = datetime.utcnow()
        if request.owner is not None:
            item.owner = request.owner
        if request.assignee_name is not None:
            item.assignee_name = request.assignee_name
        if request.assignee_email is not None:
            item.assignee_email = request.assignee_email
        if request.due_date is not None:
            item.due_date = request.due_date
        if request.order_index is not None:
            item.order_index = request.order_index
        if request.is_milestone is not None:
            item.is_milestone = request.is_milestone

        item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)

        return item

    def delete_action_plan_item(self, item_id: UUID) -> bool:
        """Delete an action plan item."""
        item = self.get_action_plan_item(item_id)
        if not item:
            return False

        self.db.delete(item)
        self.db.commit()

        return True

    # =========================================================================
    # PUBLIC VIEW HELPERS
    # =========================================================================

    def get_public_deal_room(self, slug: str) -> Optional[PublicDealRoomResponse]:
        """
        Get a deal room for public viewing.

        Args:
            slug: URL slug of the deal room

        Returns:
            Public deal room data or None
        """
        deal_room = self.get_deal_room_by_slug(slug)
        if not deal_room:
            return None

        # Check if room is accessible
        if deal_room.status != DealRoomStatus.ACTIVE:
            return None

        if is_expired(deal_room.expires_at):
            return None

        # Build section hierarchy
        sections = self._build_public_sections(deal_room.id)

        # Get action plan
        action_plan = [
            PublicActionPlanItemResponse(
                id=item.id,
                title=item.title,
                description=item.description,
                status=item.status,
                owner=item.owner,
                due_date=item.due_date,
                is_milestone=item.is_milestone,
                order_index=item.order_index,
            )
            for item in self.list_action_plan_items(deal_room.id)
        ]

        return PublicDealRoomResponse(
            slug=deal_room.slug,
            title=deal_room.title,
            description=deal_room.description,
            prospect_company=deal_room.prospect_company,
            branding=DealRoomBrandingSchema(
                logo_url=deal_room.logo_url,
                primary_color=deal_room.primary_color,
                secondary_color=deal_room.secondary_color,
                custom_css=deal_room.custom_css,
                favicon_url=deal_room.favicon_url,
            ),
            show_action_plan=deal_room.show_action_plan,
            show_timeline=deal_room.show_timeline,
            enable_comments=deal_room.enable_comments,
            sections=sections,
            action_plan=action_plan if deal_room.show_action_plan else [],
        )

    def _build_public_sections(self, deal_room_id: UUID) -> List[PublicSectionResponse]:
        """Build the public section hierarchy with contents."""
        sections = self.list_sections(deal_room_id)
        contents = self.list_contents(deal_room_id)

        # Map contents to sections
        section_contents = {}
        unsectioned = []
        for content in contents:
            if content.section_id:
                if content.section_id not in section_contents:
                    section_contents[content.section_id] = []
                section_contents[content.section_id].append(content)
            else:
                unsectioned.append(content)

        # Build section response objects
        section_map = {}
        for section in sections:
            section_map[section.id] = PublicSectionResponse(
                id=section.id,
                name=section.name,
                description=section.description,
                icon=section.icon,
                order_index=section.order_index,
                contents=[
                    PublicContentResponse(
                        id=c.id,
                        title=c.title,
                        description=c.description,
                        content_type=c.content_type,
                        file_url=c.file_url,
                        external_link=c.external_link,
                        thumbnail_url=c.thumbnail_url,
                        order_index=c.order_index,
                        is_featured=c.is_featured,
                    )
                    for c in section_contents.get(section.id, [])
                ],
                children=[],
            )

        # Build hierarchy
        root_sections = []
        for section in sections:
            if section.parent_id and section.parent_id in section_map:
                section_map[section.parent_id].children.append(section_map[section.id])
            else:
                root_sections.append(section_map[section.id])

        # Add unsectioned content to a virtual section if exists
        if unsectioned:
            root_sections.insert(0, PublicSectionResponse(
                id=UUID('00000000-0000-0000-0000-000000000000'),
                name="Documents",
                description=None,
                icon="folder",
                order_index=-1,
                contents=[
                    PublicContentResponse(
                        id=c.id,
                        title=c.title,
                        description=c.description,
                        content_type=c.content_type,
                        file_url=c.file_url,
                        external_link=c.external_link,
                        thumbnail_url=c.thumbnail_url,
                        order_index=c.order_index,
                        is_featured=c.is_featured,
                    )
                    for c in unsectioned
                ],
                children=[],
            ))

        return root_sections

    # =========================================================================
    # UTILITIES
    # =========================================================================

    def get_share_url(self, deal_room: DealRoom, base_url: str) -> str:
        """
        Generate the shareable URL for a deal room.

        Args:
            deal_room: The deal room
            base_url: Base URL of the application

        Returns:
            Full shareable URL
        """
        return f"{base_url}/room/{deal_room.slug}"

    def to_response(
        self,
        deal_room: DealRoom,
        base_url: Optional[str] = None,
    ) -> DealRoomResponse:
        """
        Convert a deal room to response schema.

        Args:
            deal_room: The deal room ORM object
            base_url: Optional base URL for share link

        Returns:
            DealRoomResponse schema
        """
        # Calculate view stats
        total_views = len(deal_room.view_events) if deal_room.view_events else 0
        unique_viewers = len(set(
            e.viewer_email for e in deal_room.view_events
            if e.viewer_email
        )) if deal_room.view_events else 0

        return DealRoomResponse(
            id=deal_room.id,
            slug=deal_room.slug,
            title=deal_room.title,
            description=deal_room.description,
            deal_id=deal_room.deal_id,
            deal_name=deal_room.deal_name,
            deal_value=deal_room.deal_value,
            prospect_company=deal_room.prospect_company,
            prospect_name=deal_room.prospect_name,
            prospect_email=deal_room.prospect_email,
            status=deal_room.status,
            access_level=deal_room.access_level,
            expires_at=deal_room.expires_at,
            branding=DealRoomBrandingSchema(
                logo_url=deal_room.logo_url,
                primary_color=deal_room.primary_color,
                secondary_color=deal_room.secondary_color,
                custom_css=deal_room.custom_css,
                favicon_url=deal_room.favicon_url,
            ),
            settings=DealRoomSettingsSchema(
                show_action_plan=deal_room.show_action_plan,
                show_timeline=deal_room.show_timeline,
                enable_comments=deal_room.enable_comments,
                notify_on_view=deal_room.notify_on_view,
                require_nda=deal_room.require_nda,
            ),
            owner_id=deal_room.owner_id,
            team_id=deal_room.team_id,
            created_at=deal_room.created_at,
            updated_at=deal_room.updated_at,
            published_at=deal_room.published_at,
            last_viewed_at=deal_room.last_viewed_at,
            share_url=self.get_share_url(deal_room, base_url) if base_url else None,
            total_views=total_views,
            unique_viewers=unique_viewers,
        )
