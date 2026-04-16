from modules.db import Database


class ConversationManager:
    """Manages multi-turn conversations with prospects."""

    def __init__(self, db: Database):
        self.db = db

    def start_conversation(self, lead_id, canal, initial_message):
        """Record the agent's first outreach message and update lead status.

        Args:
            lead_id: ID of the lead
            canal: Communication channel ("email", "linkedin", etc.)
            initial_message: Agent's initial outreach message
        """
        self.db.insert_conversation(
            lead_id=lead_id,
            canal=canal,
            role="agent",
            message=initial_message,
            score_maturite=0
        )
        self.db.update_lead_status(lead_id, "sent", mode="agent")

    def add_prospect_reply(self, lead_id, canal, message):
        """Record a prospect's reply.

        Args:
            lead_id: ID of the lead
            canal: Communication channel
            message: Prospect's message
        """
        self.db.insert_conversation(
            lead_id=lead_id,
            canal=canal,
            role="prospect",
            message=message,
            score_maturite=0
        )

    def add_agent_reply(self, lead_id, canal, message, score_maturite=0):
        """Record agent's follow-up message.

        Args:
            lead_id: ID of the lead
            canal: Communication channel
            message: Agent's follow-up message
            score_maturite: Maturity score (0-100)
        """
        self.db.insert_conversation(
            lead_id=lead_id,
            canal=canal,
            role="agent",
            message=message,
            score_maturite=score_maturite
        )

    def get_history(self, lead_id):
        """Returns full conversation history for a lead.

        Args:
            lead_id: ID of the lead

        Returns:
            List of conversation messages with metadata
        """
        return self.db.get_conversations(lead_id)

    def get_turn_count(self, lead_id):
        """Returns number of agent messages sent (outreach + follow-ups).

        Args:
            lead_id: ID of the lead

        Returns:
            Number of agent turns in the conversation
        """
        return sum(1 for h in self.get_history(lead_id) if h["role"] == "agent")

    def format_history_for_prompt(self, lead_id):
        """Format conversation history as text for AI context.

        Args:
            lead_id: ID of the lead

        Returns:
            Formatted conversation history string
        """
        history = self.get_history(lead_id)
        lines = []
        for msg in history:
            role_label = "CGP" if msg["role"] == "agent" else "Prospect"
            lines.append(f"{role_label}: {msg['message']}")
        return "\n\n".join(lines)
