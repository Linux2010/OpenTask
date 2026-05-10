"""
Bot Configuration Service

CRUD operations for managing available bots.
"""

from typing import List, Optional, Dict, Any
from app.utils.db import execute_query, execute_insert, execute_update


class BotService:
    """Service for bot configuration management"""

    @staticmethod
    async def list_bots(active_only: bool = False) -> List[Dict[str, Any]]:
        """Get list of all bots"""
        if active_only:
            query = "SELECT * FROM bot_config WHERE is_active = 1 ORDER BY id"
        else:
            query = "SELECT * FROM bot_config ORDER BY id"
        return execute_query(query)

    @staticmethod
    async def get_bot(bot_name: str) -> Optional[Dict[str, Any]]:
        """Get a single bot by name"""
        query = "SELECT * FROM bot_config WHERE bot_name = %s"
        return execute_query(query, (bot_name,))

    @staticmethod
    async def create_bot(
        bot_name: str,
        display_name: str = None,
        description: str = None
    ) -> Dict[str, Any]:
        """Create a new bot"""
        query = """
            INSERT INTO bot_config (bot_name, display_name, description)
            VALUES (%s, %s, %s)
        """
        bot_id = execute_insert(query, (
            bot_name,
            display_name or bot_name,
            description
        ))

        return {
            "id": bot_id,
            "bot_name": bot_name,
            "display_name": display_name or bot_name,
            "description": description,
            "is_active": True
        }

    @staticmethod
    async def update_bot(
        bot_name: str,
        display_name: str = None,
        description: str = None,
        is_active: bool = None
    ) -> Optional[Dict[str, Any]]:
        """Update bot configuration"""
        updates = []
        params = []

        if display_name is not None:
            updates.append("display_name = %s")
            params.append(display_name)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)

        if not updates:
            return await BotService.get_bot(bot_name)

        params.append(bot_name)
        query = f"UPDATE bot_config SET {', '.join(updates)} WHERE bot_name = %s"
        execute_update(query, tuple(params))

        return await BotService.get_bot(bot_name)

    @staticmethod
    async def toggle_bot_status(bot_name: str) -> Optional[Dict[str, Any]]:
        """Toggle bot active status"""
        bot = await BotService.get_bot(bot_name)
        if not bot:
            return None

        new_status = not bot[0]["is_active"]
        return await BotService.update_bot(bot_name, is_active=new_status)

    @staticmethod
    async def delete_bot(bot_name: str) -> bool:
        """Delete a bot"""
        query = "DELETE FROM bot_config WHERE bot_name = %s"
        rows = execute_update(query, (bot_name,))
        return rows > 0

    @staticmethod
    async def get_active_bot_names() -> List[str]:
        """Get list of active bot names for dropdowns"""
        bots = await BotService.list_bots(active_only=True)
        return [bot["bot_name"] for bot in bots]