"""Expense API views."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from Expense_Tracker.db.dependencies import get_db_session
from Expense_Tracker.db.models.expenses import Expense
from Expense_Tracker.web.api.auth import current_user
from Expense_Tracker.web.api.auth.schemas import UserRead
from Expense_Tracker.web.middleware.ratelimiter.limiter import RateLimiter
from Expense_Tracker.web.middleware.ratelimiter.middleware import RateLimitConfig

from .schema import ExpenseCreate, ExpenseRead, ExpenseUpdate

router = APIRouter()

# Configure rate limits for expense endpoints
expense_rate_limit = RateLimiter(
    RateLimitConfig(
        requests_limit=50,  # 50 requests per minute for unauthenticated users
        auth_requests_limit=200,  # 200 requests per minute for authenticated users
        window_size=60,  # 1 minute window
    ),
)


@router.get(
    "/",
    response_model=List[ExpenseRead],
    dependencies=[Depends(expense_rate_limit.is_allowed)],
)
async def list_expenses(
    skip: int = 0,
    limit: int = 100,
    current_user: UserRead = Depends(current_user(active=True)),
    db: AsyncSession = Depends(get_db_session),
) -> list[Expense]:
    """List all expenses for the current user with pagination.

    Args:
        skip: Number of expenses to skip (for pagination)
        limit: Maximum number of expenses to return (for pagination)
        current_user: The authenticated user making the request
        db: Database session dependency

    Returns:
        List of expenses belonging to the user
    """
    query = (
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.expense_date.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post(
    "/",
    response_model=ExpenseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(expense_rate_limit.is_allowed)],
)
async def create_expense(
    expense: ExpenseCreate,
    current_user: UserRead = Depends(current_user(active=True)),
    db: AsyncSession = Depends(get_db_session),
) -> Expense:
    """Create a new expense.

    Args:
        expense: The expense data to create
        current_user: The authenticated user making the request
        db: Database session dependency

    Returns:
        The created expense

    Raises:
        HTTPException: If the category doesn't exist or user is not authorized
    """
    # Verify the category exists and belongs to the user
    from Expense_Tracker.db.models.categories import ExpenseCategory

    query = select(ExpenseCategory).where(
        and_(
            ExpenseCategory.id == expense.category_id,
            ExpenseCategory.user_id == current_user.id,
        ),
    )
    result = await db.execute(query)
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or doesn't belong to user",
        )

    db_expense = Expense(
        name=expense.name,
        description=expense.description,
        amount=expense.amount,
        expense_date=expense.expense_date,
        is_recurring=expense.is_recurring,
        category_id=expense.category_id,
        user_id=current_user.id,
    )

    try:
        db.add(db_expense)
        await db.commit()
        await db.refresh(db_expense)
        return db_expense
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create expense",
        ) from None


@router.get(
    "/{expense_id}",
    response_model=ExpenseRead,
    dependencies=[Depends(expense_rate_limit.is_allowed)],
)
async def get_expense(
    expense_id: UUID,
    current_user: UserRead = Depends(current_user(active=True)),
    db: AsyncSession = Depends(get_db_session),
) -> Expense:
    """Get a specific expense.

    Args:
        expense_id: The ID of the expense to retrieve
        current_user: The authenticated user making the request
        db: Database session dependency

    Returns:
        The requested expense

    Raises:
        HTTPException: If the expense doesn't exist or user is not authorized
    """
    query = select(Expense).where(
        Expense.id == expense_id,
        Expense.user_id == current_user.id,
    )
    result = await db.execute(query)
    expense = result.scalar_one_or_none()

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    return expense


@router.patch(
    "/{expense_id}",
    response_model=ExpenseRead,
    dependencies=[Depends(expense_rate_limit.is_allowed)],
)
async def update_expense(
    expense_id: UUID,
    expense_update: ExpenseUpdate,
    current_user: UserRead = Depends(current_user(active=True)),
    db: AsyncSession = Depends(get_db_session),
) -> Expense:
    """Update an expense.

    Args:
        expense_id: The ID of the expense to update
        expense_update: The updated expense data
        current_user: The authenticated user making the request
        db: Database session dependency

    Returns:
        The updated expense

    Raises:
        HTTPException: If the expense doesn't exist or user is not authorized
    """
    # First, verify the expense exists and belongs to the user
    query = select(Expense).where(
        Expense.id == expense_id,
        Expense.user_id == current_user.id,
    )
    result = await db.execute(query)
    expense = result.scalar_one_or_none()

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    # If category_id is being updated, verify it exists and belongs to user
    if expense_update.category_id is not None:
        from Expense_Tracker.db.models.categories import ExpenseCategory

        category_query = select(ExpenseCategory).where(
            and_(
                ExpenseCategory.id == expense_update.category_id,
                ExpenseCategory.user_id == current_user.id,
            ),
        )
        category_result = await db.execute(category_query)
        if category_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or doesn't belong to user",
            )

    # Update fields
    update_data = expense_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(expense, key, value)

    await db.commit()
    await db.refresh(expense)
    return expense


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(expense_rate_limit.is_allowed)],
)
async def delete_expense(
    expense_id: UUID,
    current_user: UserRead = Depends(current_user(active=True)),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete an expense.

    Args:
        expense_id: The ID of the expense to delete
        current_user: The authenticated user making the request
        db: Database session dependency

    Raises:
        HTTPException: If the expense doesn't exist or user is not authorized
    """
    # First, verify the expense exists and belongs to the user
    query = select(Expense).where(
        Expense.id == expense_id,
        Expense.user_id == current_user.id,
    )
    result = await db.execute(query)
    expense = result.scalar_one_or_none()

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    await db.delete(expense)
    await db.commit()
