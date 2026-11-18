"""philippines school course quotation report

Revision ID: a71c2f90d3e4
Revises: e54009b307e5
Create Date: 2026-11-18 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a71c2f90d3e4'
down_revision: Union[str, Sequence[str], None] = 'e54009b307e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 学校库 / 课程价目
    op.create_table(
        'schools',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False, unique=True),
        sa.Column('region', sa.String(length=20), nullable=False),
        sa.Column('country', sa.String(length=40), nullable=False, server_default='菲律宾'),
        sa.Column('style', sa.String(length=20), nullable=False),
        sa.Column('commission_rate', sa.String(length=8), nullable=False, server_default='0'),
        sa.Column('registration_fee_usd', sa.String(length=12), nullable=False, server_default='0'),
        sa.Column('cooperation_agreement', sa.Text(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False, index=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('course_type', sa.String(length=20), nullable=False),
        sa.Column('lessons', sa.String(length=100), nullable=True),
        sa.Column('min_weeks', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('room_prices', sa.JSON(), nullable=False),
        sa.Column('guarantee', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    # 报价单（先建表，enrollments 再挂 FK）
    op.create_table(
        'quotations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quote_no', sa.String(length=32), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id'), nullable=False, index=True),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id'), nullable=False),
        sa.Column('weeks', sa.Integer(), nullable=False),
        sa.Column('room_type', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('items', sa.JSON(), nullable=False),
        sa.Column('total_usd', sa.String(length=16), nullable=False),
        sa.Column('status', sa.String(length=12), nullable=False, server_default='草稿'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('quote_no', name='uq_quote_no'),
    )
    # 在读周报
    op.create_table(
        'weekly_reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('enrollment_id', sa.Integer(), sa.ForeignKey('enrollments.id'), nullable=False, index=True),
        sa.Column('week_no', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=True),
        sa.Column('test_score', sa.String(length=20), nullable=True),
        sa.Column('attendance_pct', sa.Integer(), nullable=True),
        sa.Column('teacher_comment', sa.Text(), nullable=True),
        sa.Column('parent_notified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    # 既有表扩展（SQLite 不支持 ALTER 加外键，FK 仅保留在 ORM 层）
    op.add_column('programs', sa.Column('school_id', sa.Integer(), nullable=True))
    op.add_column('programs', sa.Column('course_id', sa.Integer(), nullable=True))
    op.add_column('programs', sa.Column('weeks', sa.Integer(), nullable=True))
    op.add_column('programs', sa.Column('room_type', sa.String(length=20), nullable=True))
    op.add_column('enrollments', sa.Column('quotation_id', sa.Integer(), nullable=True))
    op.add_column('payments', sa.Column('currency', sa.String(length=8), nullable=False, server_default='CNY'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('payments', 'currency')
    op.drop_column('enrollments', 'quotation_id')
    op.drop_column('programs', 'room_type')
    op.drop_column('programs', 'weeks')
    op.drop_column('programs', 'course_id')
    op.drop_column('programs', 'school_id')
    op.drop_table('weekly_reports')
    op.drop_table('quotations')
    op.drop_table('courses')
    op.drop_table('schools')
