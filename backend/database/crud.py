from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from .models import (
    Idea, Tag, IdeaExpansion, IdeaVisual, Proposal, ProposalTask,
    Agent, AgentLog, SystemMetrics, ScheduledTask
)

class IdeaCRUD:
    """CRUD operations for Ideas"""
    
    @staticmethod
    def create_idea(db: Session, content: str, source_type: str, **kwargs) -> Idea:
        """Create a new idea"""
        idea = Idea(
            content_raw=content,
            source_type=source_type,
            **kwargs
        )
        db.add(idea)
        db.commit()
        db.refresh(idea)
        return idea
    
    @staticmethod
    def get_idea(db: Session, idea_id: str) -> Optional[Idea]:
        """Get idea by ID"""
        return db.query(Idea).filter(Idea.id == idea_id).first()
    
    @staticmethod
    def get_ideas(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        source_type: Optional[str] = None,
        min_urgency: Optional[float] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[Idea]:
        """Get ideas with filtering"""
        query = db.query(Idea)
        
        if category:
            query = query.filter(Idea.category == category)
        
        if source_type:
            query = query.filter(Idea.source_type == source_type)
        
        if min_urgency is not None:
            query = query.filter(Idea.urgency_score >= min_urgency)
        
        if tags:
            query = query.join(Idea.tags).filter(Tag.name.in_(tags))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Idea.content_raw.ilike(search_term),
                    Idea.content_transcribed.ilike(search_term),
                    Idea.content_processed.ilike(search_term)
                )
            )
        
        return query.order_by(desc(Idea.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_idea(db: Session, idea_id: str, **kwargs) -> Optional[Idea]:
        """Update an idea"""
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if idea:
            for key, value in kwargs.items():
                setattr(idea, key, value)
            idea.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(idea)
        return idea
    
    @staticmethod
    def delete_idea(db: Session, idea_id: str) -> bool:
        """Delete an idea"""
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if idea:
            db.delete(idea)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_related_ideas(db: Session, idea_id: str) -> List[Idea]:
        """Get ideas related to a specific idea"""
        idea = db.query(Idea).filter(Idea.id == idea_id).first()
        if idea:
            return idea.related_ideas
        return []
    
    @staticmethod
    def get_ideas_by_urgency(db: Session, min_score: float = 80.0) -> List[Idea]:
        """Get high-urgency ideas"""
        return db.query(Idea).filter(
            and_(
                Idea.urgency_score >= min_score,
                Idea.is_archived == False
            )
        ).order_by(desc(Idea.urgency_score)).all()
    
    @staticmethod
    def get_stale_ideas(db: Session, days: int = 7) -> List[Idea]:
        """Get ideas that haven't been updated recently"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return db.query(Idea).filter(
            and_(
                Idea.updated_at < cutoff_date,
                Idea.is_archived == False,
                Idea.urgency_score > 50.0
            )
        ).all()

class TagCRUD:
    """CRUD operations for Tags"""
    
    @staticmethod
    def create_tag(db: Session, name: str, color: str = '#3B82F6', description: str = '') -> Tag:
        """Create a new tag"""
        tag = Tag(name=name, color=color, description=description)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag
    
    @staticmethod
    def get_or_create_tag(db: Session, name: str) -> Tag:
        """Get existing tag or create new one"""
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = TagCRUD.create_tag(db, name)
        return tag
    
    @staticmethod
    def get_all_tags(db: Session) -> List[Tag]:
        """Get all tags"""
        return db.query(Tag).all()

class ExpansionCRUD:
    """CRUD operations for Idea Expansions"""
    
    @staticmethod
    def create_expansion(
        db: Session, 
        idea_id: str, 
        content: str, 
        expansion_type: str,
        prompt_used: str = '',
        agent_version: str = '1.0.0'
    ) -> IdeaExpansion:
        """Create a new idea expansion"""
        expansion = IdeaExpansion(
            idea_id=idea_id,
            expanded_content=content,
            expansion_type=expansion_type,
            prompt_used=prompt_used,
            agent_version=agent_version
        )
        db.add(expansion)
        db.commit()
        db.refresh(expansion)
        return expansion
    
    @staticmethod
    def get_expansions_for_idea(db: Session, idea_id: str) -> List[IdeaExpansion]:
        """Get all expansions for an idea"""
        return db.query(IdeaExpansion).filter(IdeaExpansion.idea_id == idea_id).all()

class VisualCRUD:
    """CRUD operations for Idea Visuals"""
    
    @staticmethod
    def create_visual(
        db: Session,
        idea_id: str,
        image_path: str,
        prompt_used: str = '',
        style_config: Optional[Dict] = None,
        generation_params: Optional[Dict] = None
    ) -> IdeaVisual:
        """Create a new idea visual"""
        visual = IdeaVisual(
            idea_id=idea_id,
            image_path=image_path,
            prompt_used=prompt_used,
            style_config=style_config or {},
            generation_params=generation_params or {}
        )
        db.add(visual)
        db.commit()
        db.refresh(visual)
        return visual
    
    @staticmethod
    def get_visuals_for_idea(db: Session, idea_id: str) -> List[IdeaVisual]:
        """Get all visuals for an idea"""
        return db.query(IdeaVisual).filter(IdeaVisual.idea_id == idea_id).all()
    
    @staticmethod
    def approve_visual(db: Session, visual_id: str, quality_score: float = 85.0) -> Optional[IdeaVisual]:
        """Approve a visual"""
        visual = db.query(IdeaVisual).filter(IdeaVisual.id == visual_id).first()
        if visual:
            visual.is_approved = True
            visual.quality_score = quality_score
            db.commit()
            db.refresh(visual)
        return visual

class ProposalCRUD:
    """CRUD operations for Proposals"""
    
    @staticmethod
    def create_proposal(
        db: Session,
        idea_id: str,
        title: str,
        description: str,
        problem_statement: str = '',
        solution_approach: str = '',
        implementation_plan: Optional[Dict] = None,
        generated_by: str = 'system'
    ) -> Proposal:
        """Create a new proposal"""
        proposal = Proposal(
            idea_id=idea_id,
            title=title,
            description=description,
            problem_statement=problem_statement,
            solution_approach=solution_approach,
            implementation_plan=implementation_plan or {},
            generated_by=generated_by
        )
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        return proposal
    
    @staticmethod
    def get_pending_proposals(db: Session) -> List[Proposal]:
        """Get all pending proposals"""
        return db.query(Proposal).filter(Proposal.status == 'pending').all()
    
    @staticmethod
    def approve_proposal(db: Session, proposal_id: str, notes: str = '') -> Optional[Proposal]:
        """Approve a proposal"""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if proposal:
            proposal.status = 'approved'
            proposal.approval_notes = notes
            proposal.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(proposal)
        return proposal

class AgentCRUD:
    """CRUD operations for Agents"""
    
    @staticmethod
    def create_or_update_agent(
        db: Session,
        agent_id: str,
        name: str,
        description: str = '',
        version: str = '1.0.0',
        config: Optional[Dict] = None
    ) -> Agent:
        """Create or update an agent"""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            agent = Agent(
                id=agent_id,
                name=name,
                description=description,
                version=version,
                config=config or {}
            )
            db.add(agent)
        else:
            agent.name = name
            agent.description = description
            agent.version = version
            agent.config = config or {}
            agent.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(agent)
        return agent
    
    @staticmethod
    def log_agent_activity(
        db: Session,
        agent_id: str,
        action: str,
        status: str,
        idea_id: Optional[str] = None,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None
    ) -> AgentLog:
        """Log agent activity"""
        log = AgentLog(
            agent_id=agent_id,
            idea_id=idea_id,
            action=action,
            status=status,
            input_data=input_data,
            output_data=output_data,
            error_message=error_message,
            started_at=started_at or datetime.utcnow(),
            completed_at=completed_at
        )
        
        if started_at and completed_at:
            log.processing_time = (completed_at - started_at).total_seconds()
        
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_agent_performance(db: Session, agent_id: str, days: int = 30) -> Dict[str, Any]:
        """Get agent performance metrics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        logs = db.query(AgentLog).filter(
            and_(
                AgentLog.agent_id == agent_id,
                AgentLog.started_at >= cutoff_date
            )
        ).all()
        
        total_tasks = len(logs)
        successful_tasks = len([log for log in logs if log.status == 'completed'])
        failed_tasks = len([log for log in logs if log.status == 'failed'])
        
        avg_processing_time = 0
        if logs:
            processing_times = [log.processing_time for log in logs if log.processing_time]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
        
        return {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': (successful_tasks / total_tasks) if total_tasks > 0 else 0,
            'avg_processing_time': avg_processing_time
        }