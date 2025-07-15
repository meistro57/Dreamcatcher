from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

# Association table for user roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('granted_at', DateTime, default=func.now()),
    Column('granted_by', String, ForeignKey('users.id'))
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic user information
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    
    # Authentication
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Profile information
    avatar_url = Column(String)
    bio = Column(Text)
    timezone = Column(String, default='UTC')
    language = Column(String, default='en')
    
    # Account management
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    password_reset_token = Column(String)
    password_reset_expires = Column(DateTime)
    email_verification_token = Column(String)
    email_verification_expires = Column(DateTime)
    
    # Preferences
    preferences = Column(JSON, default=dict)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    ideas = relationship("Idea", back_populates="user")
    user_sessions = relationship("UserSession", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    
    # Permissions
    permissions = Column(JSON, default=dict)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"

class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    
    # Session information
    token_hash = Column(String, nullable=False, index=True)
    refresh_token_hash = Column(String)
    device_info = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Session lifecycle
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"

# Association table for idea-to-idea relationships
idea_relationships = Table(
    'idea_relationships',
    Base.metadata,
    Column('source_idea_id', String, ForeignKey('ideas.id'), primary_key=True),
    Column('target_idea_id', String, ForeignKey('ideas.id'), primary_key=True),
    Column('relationship_type', String, nullable=False),  # 'related', 'expanded_from', 'merged_into'
    Column('created_at', DateTime, default=func.now())
)

# Association table for idea tags
idea_tags = Table(
    'idea_tags',
    Base.metadata,
    Column('idea_id', String, ForeignKey('ideas.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Idea(Base):
    __tablename__ = 'ideas'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    content_raw = Column(Text, nullable=False)
    content_transcribed = Column(Text)
    content_processed = Column(Text)
    
    # Metadata
    source_type = Column(String, nullable=False)  # 'voice', 'text', 'dream', 'image'
    device_info = Column(JSON)
    location_data = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # AI Analysis
    category = Column(String)  # 'creative', 'business', 'personal', 'metaphysical', 'utility'
    urgency_score = Column(Float, default=0.0)
    novelty_score = Column(Float, default=0.0)
    viability_score = Column(Float, default=0.0)
    
    # Status
    processing_status = Column(String, default='pending')  # 'pending', 'processing', 'completed', 'failed'
    is_archived = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="ideas")
    tags = relationship("Tag", secondary=idea_tags, back_populates="ideas")
    related_ideas = relationship(
        "Idea", 
        secondary=idea_relationships,
        primaryjoin=id == idea_relationships.c.source_idea_id,
        secondaryjoin=id == idea_relationships.c.target_idea_id,
        back_populates="related_ideas"
    )
    expansions = relationship("IdeaExpansion", back_populates="idea")
    visuals = relationship("IdeaVisual", back_populates="idea")
    proposals = relationship("Proposal", back_populates="idea")
    agent_logs = relationship("AgentLog", back_populates="idea")

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    color = Column(String, default='#3B82F6')
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    ideas = relationship("Idea", secondary=idea_tags, back_populates="tags")

class IdeaExpansion(Base):
    __tablename__ = 'idea_expansions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_id = Column(String, ForeignKey('ideas.id'), nullable=False)
    
    # Expansion content
    expanded_content = Column(Text, nullable=False)
    expansion_type = Column(String, nullable=False)  # 'claude', 'gpt', 'combined'
    prompt_used = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    agent_version = Column(String)
    
    # Relationships
    idea = relationship("Idea", back_populates="expansions")

class IdeaVisual(Base):
    __tablename__ = 'idea_visuals'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_id = Column(String, ForeignKey('ideas.id'), nullable=False)
    
    # Visual data
    image_path = Column(String, nullable=False)
    prompt_used = Column(Text)
    style_config = Column(JSON)
    generation_params = Column(JSON)
    
    # Quality metrics
    quality_score = Column(Float, default=0.0)
    is_approved = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    generator_type = Column(String, default='comfyui')
    
    # Relationships
    idea = relationship("Idea", back_populates="visuals")

class Proposal(Base):
    __tablename__ = 'proposals'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    idea_id = Column(String, ForeignKey('ideas.id'), nullable=False)
    
    # Proposal content
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    problem_statement = Column(Text)
    solution_approach = Column(Text)
    implementation_plan = Column(JSON)
    
    # Status
    status = Column(String, default='pending')  # 'pending', 'approved', 'rejected', 'in_progress', 'completed'
    approval_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    generated_by = Column(String)  # agent name
    
    # Relationships
    idea = relationship("Idea", back_populates="proposals")
    tasks = relationship("ProposalTask", back_populates="proposal")

class ProposalTask(Base):
    __tablename__ = 'proposal_tasks'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    proposal_id = Column(String, ForeignKey('proposals.id'), nullable=False)
    
    # Task details
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(String, default='medium')  # 'low', 'medium', 'high', 'urgent'
    status = Column(String, default='todo')  # 'todo', 'in_progress', 'completed', 'blocked'
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    proposal = relationship("Proposal", back_populates="tasks")

class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(String, primary_key=True)  # agent name/identifier
    name = Column(String, nullable=False)
    description = Column(Text)
    version = Column(String, default='1.0.0')
    
    # Configuration
    config = Column(JSON)
    is_active = Column(Boolean, default=True)
    
    # Performance metrics
    total_processed = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_processing_time = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_active = Column(DateTime)
    
    # Relationships
    logs = relationship("AgentLog", back_populates="agent")

class AgentLog(Base):
    __tablename__ = 'agent_logs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey('agents.id'), nullable=False)
    idea_id = Column(String, ForeignKey('ideas.id'))
    
    # Log details
    action = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'started', 'completed', 'failed'
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    processing_time = Column(Float)
    
    # Relationships
    agent = relationship("Agent", back_populates="logs")
    idea = relationship("Idea", back_populates="agent_logs")

class SystemMetrics(Base):
    __tablename__ = 'system_metrics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Metrics
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_type = Column(String, nullable=False)  # 'counter', 'gauge', 'histogram'
    
    # Metadata
    timestamp = Column(DateTime, default=func.now())
    labels = Column(JSON)

class ScheduledTask(Base):
    __tablename__ = 'scheduled_tasks'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Task details
    name = Column(String, nullable=False)
    description = Column(Text)
    agent_id = Column(String, ForeignKey('agents.id'))
    
    # Scheduling
    schedule_type = Column(String, nullable=False)  # 'cron', 'interval', 'once'
    schedule_config = Column(JSON, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())