"""add image support to questions

Revision ID: add_image_support
Revises: 
Create Date: 2024-01-15 10:00:00.000000

This migration adds image support fields to the questions table,
enabling medical entrance exam questions with images attached to
questions, options, and explanations.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'add_image_support'
down_revision = None  # Update this to your last migration ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add image support columns to questions table."""
    
    # Add question_images column (JSON array of image URLs)
    op.add_column(
        'questions',
        sa.Column(
            'question_images',
            JSONB,
            nullable=True,
            server_default=sa.text('\'[]\'::jsonb'),
            comment='List of image URLs attached to the question'
        )
    )
    
    # Add explanation_images column (JSON array of image URLs)
    op.add_column(
        'questions',
        sa.Column(
            'explanation_images',
            JSONB,
            nullable=True,
            server_default=sa.text('\'[]\'::jsonb'),
            comment='List of image URLs for the explanation'
        )
    )
    
    # Add audio_url column
    op.add_column(
        'questions',
        sa.Column(
            'audio_url',
            sa.String(500),
            nullable=True,
            comment='Audio explanation URL'
        )
    )
    
    # Add video_url column
    op.add_column(
        'questions',
        sa.Column(
            'video_url',
            sa.String(500),
            nullable=True,
            comment='Video explanation URL'
        )
    )
    
    # Update metadata_json default to empty dict
    op.alter_column(
        'questions',
        'metadata_json',
        server_default=sa.text('\'{}\'::jsonb')
    )
    
    # Create index on question_images for faster JSON queries
    op.create_index(
        'ix_questions_question_images',
        'questions',
        ['question_images'],
        postgresql_using='gin'
    )
    
    # Create index on explanation_images for faster JSON queries
    op.create_index(
        'ix_questions_explanation_images',
        'questions',
        ['explanation_images'],
        postgresql_using='gin'
    )


def downgrade() -> None:
    """Remove image support columns from questions table."""
    
    # Drop indexes
    op.drop_index('ix_questions_explanation_images', table_name='questions')
    op.drop_index('ix_questions_question_images', table_name='questions')
    
    # Drop columns
    op.drop_column('questions', 'video_url')
    op.drop_column('questions', 'audio_url')
    op.drop_column('questions', 'explanation_images')
    op.drop_column('questions', 'question_images')
