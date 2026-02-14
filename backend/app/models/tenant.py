"""
NOCbRAIN Tenant Models
Multi-tenancy support for global SaaS architecture
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base


class Tenant(Base):
    """Tenant/Organization model for multi-tenancy"""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=True, index=True)
    
    # Tenant configuration
    settings = Column(JSON, default=dict)
    security_config = Column(JSON, default=dict)
    monitoring_config = Column(JSON, default=dict)
    
    # Subscription and limits
    plan = Column(String(50), default="free")  # free, pro, enterprise
    max_users = Column(Integer, default=5)
    max_collectors = Column(Integer, default=3)
    max_knowledge_docs = Column(Integer, default=1000)
    max_api_calls_per_hour = Column(Integer, default=1000)
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_trial = Column(Boolean, default=False)
    trial_ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="tenant")
    security_events = relationship("SecurityEvent", back_populates="tenant")
    collectors = relationship("Collector", back_populates="tenant")
    orchestration_jobs = relationship("OrchestrationJob", back_populates="tenant")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, slug={self.slug})>"


class TenantUser(Base):
    """Tenant-User relationship with roles"""
    __tablename__ = "tenant_users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Role and permissions
    role = Column(String(50), default="viewer")  # admin, operator, analyst, viewer
    permissions = Column(JSON, default=list)
    
    # Status
    is_active = Column(Boolean, default=True)
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    joined_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
    
    def __repr__(self):
        return f"<TenantUser(tenant_id={self.tenant_id}, user_id={self.user_id}, role={self.role})>"


class KnowledgeDocument(Base):
    """Knowledge documents with tenant isolation"""
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Document metadata
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, default=0)
    content_type = Column(String(100), default="text/markdown")
    
    # Classification
    knowledge_type = Column(String(50), nullable=False, index=True)
    tags = Column(JSON, default=list)
    category = Column(String(100), nullable=True)
    
    # Vector metadata
    vector_ids = Column(JSON, default=list)  # Store vector DB IDs
    embedding_model = Column(String(100), default="text-embedding-ada-002")
    chunk_count = Column(Integer, default=0)
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)  # Shared across tenants if enabled
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="knowledge_documents")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, tenant_id={self.tenant_id}, title={self.title})>"


class SecurityEvent(Base):
    """Security events with tenant isolation"""
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Event data
    event_id = Column(String(100), nullable=False, unique=True)
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    source_ip = Column(String(45), nullable=True, index=True)
    target_ip = Column(String(45), nullable=True)
    
    # Event details
    message = Column(Text, nullable=False)
    raw_log = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict)
    
    # Threat analysis
    threat_type = Column(String(50), nullable=True)
    confidence = Column(Integer, default=0)  # 0-100
    pattern_matches = Column(JSON, default=list)
    
    # Status and workflow
    status = Column(String(20), default="open")  # open, investigating, resolved, false_positive
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="security_events")
    assignee = relationship("User")
    
    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, tenant_id={self.tenant_id}, event_type={self.event_type})>"


class Collector(Base):
    """Collectors with tenant isolation"""
    __tablename__ = "collectors"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Collector metadata
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # snmp, ssh, api, agent
    protocol = Column(String(50), nullable=False)
    
    # Connection details (encrypted)
    connection_config = Column(JSON, default=dict)
    credentials = Column(JSON, default=dict)  # Encrypted credentials
    
    # Status and health
    status = Column(String(20), default="inactive")  # active, inactive, error
    last_seen = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metrics
    total_events = Column(Integer, default=0)
    events_per_hour = Column(Integer, default=0)
    last_event_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    collection_interval = Column(Integer, default=60)  # seconds
    enabled = Column(Boolean, default=True)
    
    # Metadata
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="collectors")
    
    def __repr__(self):
        return f"<Collector(id={self.id}, tenant_id={self.tenant_id}, name={self.name})>"


class OrchestrationJob(Base):
    """Orchestration jobs with tenant isolation"""
    __tablename__ = "orchestration_jobs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Job metadata
    job_id = Column(String(100), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # script, ansible, api_call
    
    # Trigger and context
    trigger_event_id = Column(String(100), nullable=True)
    trigger_type = Column(String(50), nullable=False)  # manual, alert, scheduled
    context = Column(JSON, default=dict)
    
    # Execution details
    script_path = Column(String(500), nullable=True)
    playbook_path = Column(String(500), nullable=True)
    api_endpoint = Column(String(500), nullable=True)
    parameters = Column(JSON, default=dict)
    
    # Approval workflow
    status = Column(String(20), default="pending")  # pending, approved, rejected, executing, completed, failed
    approval_required = Column(Boolean, default=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Execution results
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_log = Column(Text, nullable=True)
    result = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="orchestration_jobs")
    creator = relationship("User")
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<OrchestrationJob(id={self.id}, tenant_id={self.tenant_id}, name={self.name})>"


class TenantSettings(Base):
    """Per-tenant settings and configurations"""
    __tablename__ = "tenant_settings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True)
    
    # Security settings
    security_thresholds = Column(JSON, default=dict)
    alert_rules = Column(JSON, default=list)
    notification_settings = Column(JSON, default=dict)
    
    # Knowledge settings
    knowledge_settings = Column(JSON, default=dict)
    embedding_settings = Column(JSON, default=dict)
    
    # Orchestration settings
    orchestration_settings = Column(JSON, default=dict)
    approved_scripts = Column(JSON, default=list)
    
    # UI settings
    ui_settings = Column(JSON, default=dict)
    dashboard_config = Column(JSON, default=dict)
    
    # Integration settings
    integrations = Column(JSON, default=dict)
    api_keys = Column(JSON, default=dict)
    
    # Metadata
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    updater = relationship("User")
    
    def __repr__(self):
        return f"<TenantSettings(id={self.id}, tenant_id={self.tenant_id})>"
