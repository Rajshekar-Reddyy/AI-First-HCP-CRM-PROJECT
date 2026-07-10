import json
from datetime import date, datetime
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import ChatHistory, HCP, Interaction, Product, Reminder, Sentiment, ToolLog
from app.schemas.interaction import InteractionCreate, InteractionUpdate
from app.schemas.reminder import ReminderCreate


class CRMRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_hcp(self, name: str, hospital: str | None, specialization: str | None) -> HCP:
        statement = select(HCP).where(func.lower(HCP.name) == name.lower())
        if hospital:
            statement = statement.where(func.lower(HCP.hospital) == hospital.lower())
        hcp = self.db.scalar(statement)
        if hcp:
            if specialization and not hcp.specialization:
                hcp.specialization = specialization
            return hcp
        hcp = HCP(name=name, hospital=hospital, specialization=specialization)
        self.db.add(hcp)
        self.db.flush()
        return hcp

    def create_interaction(self, data: InteractionCreate) -> Interaction:
        hcp = self.get_or_create_hcp(data.hcp_name, data.hospital, data.specialization)
        interaction = Interaction(
            hcp_id=hcp.id,
            interaction_type=data.interaction_type,
            interaction_date=data.interaction_date,
            interaction_time=data.interaction_time,
            attendees=data.attendees,
            topics_discussed=data.topics_discussed,
            voice_summary=data.voice_summary,
            materials_shared=data.materials_shared,
            samples_distributed=data.samples_distributed,
            sentiment=data.sentiment,
            outcome=data.outcome,
            follow_up=data.follow_up,
            notes=data.notes,
        )
        self.db.add(interaction)
        self.db.commit()
        return self.get_interaction(interaction.id)

    def update_interaction(self, interaction_id: int, data: InteractionUpdate) -> Interaction:
        interaction = self.get_interaction(interaction_id)
        update_data = data.model_dump(exclude_unset=True)
        hcp_fields = {key: update_data.pop(key) for key in ["hcp_name", "hospital", "specialization"] if key in update_data}
        if hcp_fields:
            interaction.hcp.name = hcp_fields.get("hcp_name", interaction.hcp.name)
            if "hospital" in hcp_fields:
                interaction.hcp.hospital = hcp_fields["hospital"]
            if "specialization" in hcp_fields:
                interaction.hcp.specialization = hcp_fields["specialization"]
        for key, value in update_data.items():
            setattr(interaction, key, value)
        self.db.commit()
        return self.get_interaction(interaction_id)

    def get_interaction(self, interaction_id: int) -> Interaction:
        interaction = self.db.scalar(
            select(Interaction).options(joinedload(Interaction.hcp)).where(Interaction.id == interaction_id)
        )
        if interaction is None:
            raise ValueError(f"Interaction {interaction_id} was not found")
        return interaction

    def latest_interaction(self) -> Interaction | None:
        return self.db.scalar(
            select(Interaction).options(joinedload(Interaction.hcp)).order_by(desc(Interaction.created_at)).limit(1)
        )

    def search_hcp_history(self, hcp_name: str, limit: int = 8) -> list[Interaction]:
        return list(
            self.db.scalars(
                select(Interaction)
                .options(joinedload(Interaction.hcp))
                .join(HCP)
                .where(func.lower(HCP.name).contains(hcp_name.lower()))
                .order_by(desc(Interaction.interaction_date), desc(Interaction.created_at))
                .limit(limit)
            )
        )

    def search_products(self, query: str | None, limit: int = 8) -> list[Product]:
        statement = select(Product)

        if query:
            query = query.strip().replace(".", "").replace('"', "").lower()
            pattern = f"%{query}%"

            statement = statement.where(
                or_(
                    func.lower(Product.name).like(pattern),
                    func.lower(Product.benefits).like(pattern),
                    func.lower(Product.clinical_notes).like(pattern),
                )
            )

        statement = statement.order_by(Product.name).limit(limit)

        return list(self.db.scalars(statement))

    def create_reminder(self, data: ReminderCreate) -> Reminder:
        reminder = Reminder(**data.model_dump())
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        return reminder

    def add_chat_message(self, session_id: str, role: str, content: str) -> ChatHistory:
        message = ChatHistory(session_id=session_id, role=role, content=content)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def chat_history(self, session_id: str, limit: int = 20) -> list[ChatHistory]:
        rows = list(
            self.db.scalars(
                select(ChatHistory).where(ChatHistory.session_id == session_id).order_by(desc(ChatHistory.created_at)).limit(limit)
            )
        )
        return list(reversed(rows))

    def log_tool(self, session_id: str, tool_name: str, input_data: dict[str, Any], output_data: dict[str, Any], status: str) -> ToolLog:
        row = ToolLog(
            session_id=session_id,
            tool_name=tool_name,
            input_json=json.dumps(input_data, default=str),
            output_json=json.dumps(output_data, default=str),
            status=status,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def tool_history(self, session_id: str | None = None, limit: int = 20) -> list[ToolLog]:
        statement = select(ToolLog).order_by(desc(ToolLog.created_at)).limit(limit)
        if session_id:
            statement = select(ToolLog).where(ToolLog.session_id == session_id).order_by(desc(ToolLog.created_at)).limit(limit)
        return list(self.db.scalars(statement))

    def dashboard_counts(self) -> dict[str, int]:
        today = date.today()
        return {
            "today_interactions": self.db.scalar(select(func.count()).select_from(Interaction).where(Interaction.interaction_date == today)) or 0,
            "pending_follow_ups": self.db.scalar(select(func.count()).select_from(Reminder).where(Reminder.status == "pending")) or 0,
            "positive_sentiment": self.db.scalar(select(func.count()).select_from(Interaction).where(Interaction.sentiment == Sentiment.positive)) or 0,
            "negative_sentiment": self.db.scalar(select(func.count()).select_from(Interaction).where(Interaction.sentiment == Sentiment.negative)) or 0,
        }

    def recent_interactions(self, limit: int = 6) -> list[Interaction]:
        return list(
            self.db.scalars(
                select(Interaction).options(joinedload(Interaction.hcp)).order_by(desc(Interaction.created_at)).limit(limit)
            )
        )

    def pending_reminders(self, limit: int = 6) -> list[Reminder]:
        return list(
            self.db.scalars(
                select(Reminder).where(Reminder.status == "pending").order_by(Reminder.due_at).limit(limit)
            )
        )

    def seed_products_if_empty(self) -> None:
        if self.db.scalar(select(func.count()).select_from(Product)):
            return
        products = [
            Product(
                name="CardioMet XR",
                benefits="Supports glycemic control in adults with type 2 diabetes and high cardiovascular risk.",
                dosage="Once daily extended-release tablet with evening meal; adjust per prescribing information.",
                side_effects="Gastrointestinal discomfort, nausea, and rare lactic acidosis risk in susceptible patients.",
                clinical_notes="Discuss renal function monitoring and adherence counseling for eligible patients.",
            ),
            Product(
                name="RespiraClear",
                benefits="Maintenance therapy support for adults with persistent asthma symptoms.",
                dosage="One inhalation twice daily using approved inhaler technique.",
                side_effects="Throat irritation, oral candidiasis, headache, and cough.",
                clinical_notes="Reinforce mouth rinsing after use and document rescue inhaler frequency.",
            ),
            Product(
                name="NeuroCalm",
                benefits="Adjunctive support for neuropathic pain management in indicated adult patients.",
                dosage="Start low at night and titrate according to tolerability and approved guidance.",
                side_effects="Somnolence, dizziness, peripheral edema, and fatigue.",
                clinical_notes="Review fall risk, renal adjustment, and patient-reported pain scores.",
            ),
        ]
        self.db.add_all(products)
        self.db.commit()
