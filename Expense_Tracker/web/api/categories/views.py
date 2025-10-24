"""Category API views."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from Expense_Tracker.db.dependencies import get_db_session
from Expense_Tracker.db.models.categories import ExpenseCategory
from Expense_Tracker.web.api.auth import current_user
from Expense_Tracker.web.api.auth.schemas import UserRead

from .schema import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter()


@router.get("/", response_model=List[CategoryRead])
async def list_categories(
    skip: int = 0,
    limit: int = 100,
    current_user: UserRead = Depends(current_user(active=True)),
    db: AsyncSession = Depends(get_db_session),
) -> list[ExpenseCategory]:
    """List all categories for the current user with pagination.

    Args:
        skip: Number of categories to skip (for pagination)
        limit: Maximum number of categories to return (for pagination)
        current_user: The authenticated user making the request
        db: Database session dependency

    Returns:
        List of categories belonging to the user
    """
    query = (
        select(ExpenseCategory)
        .where(ExpenseCategory.user_id == current_user.id)
        .order_by(ExpenseCategory.name)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    current_user: UserRead = Depends(current_user(active=True)),
    db: AsyncSession = Depends(get_db_session),
) -> ExpenseCategory:
    """Create a new category.

    Args:
        category: The category data to create
        current_user: The authenticated user making the request
        db: Database session dependency

    Returns:
        The created category

    Raises:
        HTTPException: If category name is empty or already exists for the user
    """
    # Validate category name
    if not category.name or category.name.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name cannot be empty",
        )

    if len(category.name.strip()) > 50:  # reasonable limit for a category name
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name cannot be longer than 50 characters",
        )

    # Check for existing category with same name for this user
    query = select(ExpenseCategory).where(
        and_(
            ExpenseCategory.name == category.name,
            ExpenseCategory.user_id == current_user.id,
        ),
    )
    result = await db.execute(query)
    existing_category = result.scalar_one_or_none()

    if existing_category is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category with this name already exists",
        )

    db_category = ExpenseCategory(
        name=category.name.strip(),
        description=category.description.strip() if category.description else None,
        user_id=current_user.id,
    )

    try:
        db.add(db_category)
        await db.commit()
        await db.refresh(db_category)
        return db_category
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create category",
        ) from None


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: UUID,
    current_user: UserRead = Depends(current_user(active=True)),
    db: AsyncSession = Depends(get_db_session),
) -> ExpenseCategory:
    """Get a specific category.

    Args:
        category_id: The ID of the category to retrieve
        current_user: The authenticated user making the request
        db: Database session dependency

    Returns:
        The requested category

    Raises:
        HTTPException: If the category doesn't exist or user is not authorized
    """
    query = select(ExpenseCategory).where(
        ExpenseCategory.id == category_id,
        ExpenseCategory.user_id == current_user.id,
    )
    result = await db.execute(query)
    category = result.scalar_one_or_none()

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: UUID,
    category_update: CategoryUpdate,
    current_user: UserRead = Depends(current_user(active=True)),
    db: AsyncSession = Depends(get_db_session),
) -> CategoryRead:
    """Update a category.

    Args:
        category_id: The ID of the category to update
        category_update: The updated category data
        current_user: The authenticated user making the request
        db: Database session dependency

    Returns:
        The updated category

    Raises:
        HTTPException: If the category doesn't exist or user is not authorized
    """
    # First, verify the category exists and belongs to the user
    query = select(ExpenseCategory).where(
        ExpenseCategory.id == category_id,
        ExpenseCategory.user_id == current_user.id,
    )
    result = await db.execute(query)
    category = result.scalar_one_or_none()

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Validate and update fields
    update_data = category_update.model_dump(exclude_unset=True)

    if "name" in update_data:
        name = update_data["name"].strip()
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name cannot be empty",
            )
        if len(name) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name cannot be longer than 50 characters",
            )

        # Check for duplicate name
        existing = await db.execute(
            select(ExpenseCategory).where(
                and_(
                    ExpenseCategory.name == name,
                    ExpenseCategory.user_id == current_user.id,
                    ExpenseCategory.id != category_id,
                ),
            ),
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A category with this name already exists",
            )
        update_data["name"] = name

    # Update fields
    for key, value in update_data.items():
        setattr(category, key, value)

    await db.commit()
    await db.refresh(category)
    return CategoryRead.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    current_user: UserRead = Depends(current_user(active=True)),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a category.

    Args:
        category_id: The ID of the category to delete
        current_user: The authenticated user making the request
        db: Database session dependency

    Raises:
        HTTPException: If the category doesn't exist or user is not authorized
    """
    # First, verify the category exists and belongs to the user
    query = select(ExpenseCategory).where(
        ExpenseCategory.id == category_id,
        ExpenseCategory.user_id == current_user.id,
    )
    result = await db.execute(query)
    category = result.scalar_one_or_none()

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    await db.delete(category)
    await db.commit()
