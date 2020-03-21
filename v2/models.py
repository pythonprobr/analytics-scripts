import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class User(Base):
    __tablename__ = "user"

    id = sa.Column(sa.Integer, primary_key=True)
    email = sa.Column(sa.String(254), nullable=False, unique=True)


class Session(Base):
    __tablename__ = "session"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.ForeignKey("user.id"), index=True)


class Lead(Base):
    __tablename__ = "lead"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.ForeignKey("user.id"), index=True)
    created = sa.Column(sa.DateTime(True), nullable=False)


class UserProgress(Base):
    __tablename__ = "progress"

    user_id = sa.Column(sa.ForeignKey("user.id"), index=True, primary_key=True)
    last_interaction = sa.Column(sa.DateTime(True), nullable=False)
    progress = sa.Column(sa.Numeric(3, 2))


class PageView(Base):
    __tablename__ = "page_view"

    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime(True), nullable=False)
    session_id = sa.Column(sa.ForeignKey("session.id"), index=True)
    path_info = sa.Column(sa.String(1016))
    query_string = sa.Column(sa.String(1016))
    utm_source = sa.Column(sa.String(254))
    utm_medium = sa.Column(sa.String(254))
    utm_campaign = sa.Column(sa.String(254))
    utm_term = sa.Column(sa.String(254))
    utm_content = sa.Column(sa.String(254))


class Transaction(Base):
    __tablename__ = "transaction"

    tid = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime(True), nullable=False)
    user_id = sa.Column(sa.ForeignKey("user.id"), index=True)
    paid_amount = sa.Column(sa.Numeric(10, 2))
    cost = sa.Column(sa.Numeric(10, 2))
    final_amount = sa.Column(sa.Numeric(10, 2))
    is_boleto = sa.Column(sa.Boolean, nullable=False)
    offer = sa.Column(sa.String(254))


class CampaignSource(Base):
    __tablename__ = "campaign_source"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(254))


class CampaignType(Base):
    __tablename__ = "campaign_type"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(254))


class CampaignPerformance(Base):
    __tablename__ = "campaign_performance"
    __table_args__ = (
        sa.UniqueConstraint(
            "campaign_id", "source_id", "created", name="unique_component_commit"
        ),
    )

    id = sa.Column(sa.Integer, primary_key=True)
    campaign_id = sa.Column(sa.BigInteger, index=True)
    source_id = sa.Column(sa.ForeignKey("campaign_source.id"), index=True)
    created = sa.Column(sa.DateTime(True), nullable=False)
    name = sa.Column(sa.String(254))
    type_id = sa.Column(sa.ForeignKey("campaign_type.id"), index=True)
    cost = sa.Column(sa.Numeric(10, 2))
