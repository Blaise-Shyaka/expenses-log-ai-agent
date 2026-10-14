from collections.abc import Sequence
from datetime import datetime, timedelta
from uuid import UUID

from db.models import CategoryDB, ExpenseDB
from db.repositories import CategoryRepository, ExpensesRepository, UsersRepository
from db.unit_of_work import UnitOfWork
from exceptions.custom_exceptions import AlreadyExistsException, NotFoundException
from schemas.schema import CategoryCreate, CategoryWithTotal, ExpenseCreate, ExpenseTotalResponse


class CategoryServices:
    def __init__(
        self,
        category_repo: CategoryRepository,
        users_repo: UsersRepository,
        uow: UnitOfWork,
        user_id: bytes | None,
    ) -> None:
        self.category_repository = category_repo
        self.users_repository = users_repo
        self.uow = uow
        self.user_id = user_id

    async def read_category(self, id: UUID) -> CategoryDB:
        db_category = await self.category_repository.read_by_id(id)
        if db_category is None:
            raise NotFoundException("Category not found")
        return db_category

    async def read_category_by_name(self, name: str) -> CategoryDB:
        db_category = await self.category_repository.read_by_name(name)
        if db_category is None:
            raise NotFoundException("Category not found")
        return db_category

    async def read_categories(self, skip: int = 0, limit: int = 100) -> Sequence[CategoryDB]:
        return await self.category_repository.read_all(skip=skip, limit=limit)

    async def create_category(self, category: CategoryCreate) -> CategoryDB:
        if self.user_id is not None:
            await self.users_repository.ensure(self.user_id)

        if await self.category_repository.read_by_name(category.name) is not None:
            raise AlreadyExistsException("Category already exists")

        category.name = category.name.lower()
        new_category = await self.category_repository.create(
            CategoryDB(**category.model_dump(), user_id=self.user_id or b"")
        )
        await self.uow.commit()
        return new_category


class ExpensesServices:
    def __init__(
        self,
        category_repo: CategoryRepository,
        expenses_repo: ExpensesRepository,
        users_repo: UsersRepository,
        uow: UnitOfWork,
        user_id: bytes | None,
    ) -> None:
        self.categories_repository = category_repo
        self.expenses_repository = expenses_repo
        self.users_repository = users_repo
        self.uow = uow
        self.user_id = user_id

    async def create_expense(self, expense: ExpenseCreate) -> ExpenseDB:
        if self.user_id is not None:
            await self.users_repository.ensure(self.user_id)

        db_category = await self.categories_repository.read_by_name(expense.category_name)
        if db_category is None:
            db_category = await self.categories_repository.create(
                CategoryDB(name=expense.category_name, user_id=self.user_id or b"")
            )

        db_expense = await self.expenses_repository.create(
            ExpenseDB(
                amount=expense.amount,
                description=expense.description,
                date=expense.date,
                category_id=db_category.id,
                user_id=self.user_id or b"",
            )
        )
        await self.uow.commit()
        return db_expense

    async def read_by_id(self, id: UUID) -> ExpenseDB:
        db_expense = await self.expenses_repository.read_by_id(id)
        if db_expense is None:
            raise NotFoundException("Expense not found")
        return db_expense

    async def read_expenses(
        self, category_name: str | None = None, skip: int = 0, limit: int = 100
    ) -> Sequence[ExpenseDB]:
        return await self.expenses_repository.read_all(
            skip=skip, limit=limit, category_name=category_name
        )

    async def read_totals_by_category(self) -> list[CategoryWithTotal]:
        results = await self.expenses_repository.read_totals_by_category()
        return [
            CategoryWithTotal.model_validate(
                {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "total_expenses": total or 0.0,
                }
            )
            for category, total in results
        ]

    async def read_totals_since(
        self,
        start_date: datetime | None = None,
        days: int | None = None,
        category_name: str | None = None,
    ) -> ExpenseTotalResponse:
        if days is not None and start_date is None:
            start_date = datetime.now() - timedelta(days=days)
        elif start_date is None:
            # Default to last 30 days if neither is provided
            days = 30
            start_date = datetime.now() - timedelta(days=days)

        total = await self.expenses_repository.read_totals_since(
            start_date=start_date, category_name=category_name
        )
        return ExpenseTotalResponse(
            total=total,
            start_date=start_date,
            days=days,
            category_name=category_name,
        )
