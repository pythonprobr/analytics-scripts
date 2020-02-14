# coding: utf-8
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class AuthGroup(Base):
    __tablename__ = "auth_group"

    id = Column(
        Integer, primary_key=True, server_default=text("nextval('auth_group_id_seq'::regclass)"),
    )
    name = Column(String(150), nullable=False, unique=True)


class CohortsCohort(Base):
    __tablename__ = "cohorts_cohort"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('cohorts_cohort_id_seq'::regclass)"),
    )
    title = Column(String(50), nullable=False)
    slug = Column(String(50), nullable=False, index=True)
    image = Column(String(100), nullable=False)
    quote = Column(Text, nullable=False)
    mail_list = Column(String(200), nullable=False)
    forum_post = Column(String(200), nullable=False)
    start = Column(Date, nullable=False)
    end = Column(Date, nullable=False)


class CoreUser(Base):
    __tablename__ = "core_user"

    id = Column(
        Integer, primary_key=True, server_default=text("nextval('auth_user_id_seq'::regclass)"),
    )
    password = Column(String(128), nullable=False)
    last_login = Column(DateTime(True))
    is_superuser = Column(Boolean, nullable=False)
    first_name = Column(String(30), nullable=False)
    email = Column(String(254), nullable=False, unique=True)
    is_staff = Column(Boolean, nullable=False)
    is_active = Column(Boolean, nullable=False)
    date_joined = Column(DateTime(True), nullable=False)
    source = Column(String(255), nullable=False)


class DjangoContentType(Base):
    __tablename__ = "django_content_type"
    __table_args__ = (UniqueConstraint("app_label", "model"),)

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('django_content_type_id_seq'::regclass)"),
    )
    app_label = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)


class DjangoMigration(Base):
    __tablename__ = "django_migrations"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('django_migrations_id_seq'::regclass)"),
    )
    app = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    applied = Column(DateTime(True), nullable=False)


class DjangoSession(Base):
    __tablename__ = "django_session"

    session_key = Column(String(40), primary_key=True, index=True)
    session_data = Column(Text, nullable=False)
    expire_date = Column(DateTime(True), nullable=False, index=True)


class ModulesModule(Base):
    __tablename__ = "modules_module"
    __table_args__ = (CheckConstraint('"order" >= 0'),)

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('modules_module_id_seq'::regclass)"),
    )
    order = Column(Integer, nullable=False, index=True)
    title = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    slug = Column(String(50), nullable=False, unique=True)
    objective = Column(Text, nullable=False)
    target = Column(Text, nullable=False)


class AnalyticsUsersession(Base):
    __tablename__ = "analytics_usersession"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('analytics_usersession_id_seq'::regclass)"),
    )
    created = Column(DateTime(True), nullable=False)
    updated = Column(DateTime(True), nullable=False)
    uuid = Column(UUID, nullable=False)
    user_id = Column(ForeignKey("core_user.id", deferrable=True, initially="DEFERRED"), index=True)

    user = relationship("CoreUser")


class AuthPermission(Base):
    __tablename__ = "auth_permission"
    __table_args__ = (UniqueConstraint("content_type_id", "codename"),)

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('auth_permission_id_seq'::regclass)"),
    )
    name = Column(String(255), nullable=False)
    content_type_id = Column(
        ForeignKey("django_content_type.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )
    codename = Column(String(100), nullable=False)

    content_type = relationship("DjangoContentType")


class CohortsCohortstudent(Base):
    __tablename__ = "cohorts_cohortstudent"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('cohorts_cohortstudent_id_seq'::regclass)"),
    )
    cohort_id = Column(
        ForeignKey("cohorts_cohort.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        ForeignKey("core_user.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )
    added = Column(DateTime(True), nullable=False)

    cohort = relationship("CohortsCohort")
    user = relationship("CoreUser")


class CohortsLiveclas(Base):
    __tablename__ = "cohorts_liveclass"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('cohorts_liveclass_id_seq'::regclass)"),
    )
    start = Column(DateTime(True), nullable=False)
    vimeo_id = Column(String(11), nullable=False)
    cohort_id = Column(
        ForeignKey("cohorts_cohort.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )
    description = Column(Text, nullable=False)
    discourse_topic_id = Column(String(11))

    cohort = relationship("CohortsCohort")


class CohortsWebinar(Base):
    __tablename__ = "cohorts_webinar"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('cohorts_webinar_id_seq'::regclass)"),
    )
    title = Column(String(50), nullable=False)
    speaker = Column(String(50), nullable=False)
    speaker_title = Column(String(50), nullable=False)
    slug = Column(String(50), nullable=False, unique=True)
    vimeo_id = Column(String(11), nullable=False)
    start = Column(DateTime(True), nullable=False)
    cohort_id = Column(
        ForeignKey("cohorts_cohort.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )
    description = Column(Text, nullable=False)
    discourse_topic_id = Column(String(11), nullable=False)
    image = Column(String(100))

    cohort = relationship("CohortsCohort")


class CoreUserGroup(Base):
    __tablename__ = "core_user_groups"
    __table_args__ = (UniqueConstraint("user_id", "group_id"),)

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('auth_user_groups_id_seq'::regclass)"),
    )
    user_id = Column(
        ForeignKey("core_user.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )
    group_id = Column(
        ForeignKey("auth_group.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )

    group = relationship("AuthGroup")
    user = relationship("CoreUser")


class CoreUserinteraction(Base):
    __tablename__ = "core_userinteraction"
    __table_args__ = (
        Index("core_userin_user_id_6dabfb_idx", "user_id", "creation"),
        Index("core_userin_categor_d6027e_idx", "category", "creation"),
    )

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('core_userinteraction_id_seq'::regclass)"),
    )
    creation = Column(DateTime(True), nullable=False)
    category = Column(String(32), nullable=False)
    source = Column(String(32))
    user_id = Column(
        ForeignKey("core_user.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )

    user = relationship("CoreUser")


class DjangoAdminLog(Base):
    __tablename__ = "django_admin_log"
    __table_args__ = (CheckConstraint("action_flag >= 0"),)

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('django_admin_log_id_seq'::regclass)"),
    )
    action_time = Column(DateTime(True), nullable=False)
    object_id = Column(Text)
    object_repr = Column(String(200), nullable=False)
    action_flag = Column(SmallInteger, nullable=False)
    change_message = Column(Text, nullable=False)
    content_type_id = Column(
        ForeignKey("django_content_type.id", deferrable=True, initially="DEFERRED"), index=True,
    )
    user_id = Column(
        ForeignKey("core_user.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )

    content_type = relationship("DjangoContentType")
    user = relationship("CoreUser")


class ModulesSection(Base):
    __tablename__ = "modules_section"
    __table_args__ = (CheckConstraint('"order" >= 0'),)

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('sections_section_id_seq'::regclass)"),
    )
    order = Column(Integer, nullable=False, index=True)
    title = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    slug = Column(String(50), nullable=False, unique=True)
    module_id = Column(
        ForeignKey("modules_module.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )

    module = relationship("ModulesModule")


class AnalyticsPageview(Base):
    __tablename__ = "analytics_pageview"

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('analytics_pageview_id_seq'::regclass)"),
    )
    created = Column(DateTime(True), nullable=False)
    updated = Column(DateTime(True), nullable=False)
    meta = Column(JSONB(astext_type=Text()), nullable=False)
    session_id = Column(
        ForeignKey("analytics_usersession.id", deferrable=True, initially="DEFERRED"), index=True,
    )

    session = relationship("AnalyticsUsersession")


class AuthGroupPermission(Base):
    __tablename__ = "auth_group_permissions"
    __table_args__ = (UniqueConstraint("group_id", "permission_id"),)

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('auth_group_permissions_id_seq'::regclass)"),
    )
    group_id = Column(
        ForeignKey("auth_group.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )
    permission_id = Column(
        ForeignKey("auth_permission.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )

    group = relationship("AuthGroup")
    permission = relationship("AuthPermission")


class CoreUserUserPermission(Base):
    __tablename__ = "core_user_user_permissions"
    __table_args__ = (UniqueConstraint("user_id", "permission_id"),)

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('auth_user_user_permissions_id_seq'::regclass)"),
    )
    user_id = Column(
        ForeignKey("core_user.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )
    permission_id = Column(
        ForeignKey("auth_permission.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )

    permission = relationship("AuthPermission")
    user = relationship("CoreUser")


class ModulesChapter(Base):
    __tablename__ = "modules_chapter"
    __table_args__ = (CheckConstraint('"order" >= 0'),)

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('modules_chapter_id_seq'::regclass)"),
    )
    order = Column(Integer, nullable=False, index=True)
    title = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    slug = Column(String(50), nullable=False, unique=True)
    section_id = Column(
        ForeignKey("modules_section.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )

    section = relationship("ModulesSection")


class ModulesTopic(Base):
    __tablename__ = "modules_topic"
    __table_args__ = (CheckConstraint('"order" >= 0'),)

    id = Column(
        Integer, primary_key=True, server_default=text("nextval('modules_topic_id_seq'::regclass)"),
    )
    order = Column(Integer, nullable=False, index=True)
    title = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    slug = Column(String(50), nullable=False, unique=True)
    vimeo_id = Column(String(11), nullable=False)
    chapter_id = Column(
        ForeignKey("modules_chapter.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )
    discourse_topic_id = Column(String(11), nullable=False)
    duration = Column(Integer, nullable=False)

    chapter = relationship("ModulesChapter")


class DashboardTopicinteraction(Base):
    __tablename__ = "dashboard_topicinteraction"
    __table_args__ = (Index("dashboard_t_user_id_39ea24_idx", "user_id", "topic_id", "creation"),)

    id = Column(
        Integer,
        primary_key=True,
        server_default=text("nextval('dashboard_topicinteraction_id_seq'::regclass)"),
    )
    creation = Column(DateTime(True), nullable=False, index=True)
    topic_duration = Column(Integer, nullable=False)
    total_watched_time = Column(Integer, nullable=False)
    max_watched_time = Column(Integer, nullable=False)
    topic_id = Column(
        ForeignKey("modules_topic.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        ForeignKey("core_user.id", deferrable=True, initially="DEFERRED"),
        nullable=False,
        index=True,
    )

    topic = relationship("ModulesTopic")
    user = relationship("CoreUser")
