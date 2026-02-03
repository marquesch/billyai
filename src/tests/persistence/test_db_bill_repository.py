import datetime
from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from domain.entities import Bill
from domain.exceptions import BillNotFoundException
from domain.exceptions import CategoryNotFoundException
from domain.exceptions import FutureDateException
from domain.exceptions import TenantNotFoundException
from infrastructure.persistence.database.models import DBBill
from infrastructure.persistence.database.models import DBCategory
from infrastructure.persistence.database.models import DBTenant
from infrastructure.persistence.database.repositories.bill_repository import DBBillRepository


class TestDBBillRepositoryCreate:
    def test_create_bill_successfully(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_category: DBCategory,
    ):
        date = datetime.date(2025, 1, 20)
        value = 250.75
        category_id = db_category.id

        bill = db_bill_repository.create(
            tenant_id=db_tenant.id,
            date=date,
            value=value,
            category_id=category_id,
        )

        assert isinstance(bill, Bill)
        assert bill.date == date
        assert bill.value == value
        assert bill.category_id == category_id
        assert bill.tenant_id == db_tenant.id
        assert bill.id is not None

    def test_create_bill_with_nonexistent_tenant(self, db_bill_repository: DBBillRepository, db_category: DBCategory):
        date = datetime.date(2025, 1, 20)
        value = 100.00

        with pytest.raises(TenantNotFoundException):
            db_bill_repository.create(
                tenant_id=99999,
                date=date,
                value=value,
                category_id=db_category.id,
            )

    def test_create_bill_with_nonexistent_category(self, db_bill_repository: DBBillRepository, db_tenant: DBTenant):
        date = datetime.date(2025, 1, 20)
        value = 100.00

        with pytest.raises(CategoryNotFoundException):
            db_bill_repository.create(
                tenant_id=db_tenant.id,
                date=date,
                value=value,
                category_id=99999,
            )

    def test_create_bill_with_zero_value(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_category: DBCategory,
    ):
        date = datetime.date(2025, 1, 20)
        value = 0.0

        bill = db_bill_repository.create(
            tenant_id=db_tenant.id,
            date=date,
            value=value,
            category_id=db_category.id,
        )

        assert bill.value == 0.0

    def test_create_bill_with_negative_value(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_category: DBCategory,
    ):
        date = datetime.date(2025, 1, 20)
        value = -50.00

        with pytest.raises(ValueError):
            db_bill_repository.create(
                tenant_id=db_tenant.id,
                date=date,
                value=value,
                category_id=db_category.id,
            )


class TestDBBillRepositoryGetById:
    def test_get_existing_bill(self, db_bill_repository: DBBillRepository, db_tenant: DBTenant, db_sample_bill: DBBill):
        bill = db_bill_repository.get_by_id(tenant_id=db_tenant.id, bill_id=db_sample_bill.id)

        assert isinstance(bill, Bill)
        assert bill.id == db_sample_bill.id
        assert bill.tenant_id == db_tenant.id
        assert bill.date == db_sample_bill.date
        assert bill.value == db_sample_bill.value
        assert bill.category_id == db_sample_bill.category_id

    def test_get_nonexistent_bill(self, db_bill_repository: DBBillRepository, db_tenant: DBTenant):
        with pytest.raises(BillNotFoundException):
            db_bill_repository.get_by_id(tenant_id=db_tenant.id, bill_id=99999)

    def test_get_bill_from_different_tenant(
        self,
        db_bill_repository: DBBillRepository,
        session: Session,
        db_sample_bill: DBBill,
        another_db_tenant: DBTenant,
    ):
        with pytest.raises(BillNotFoundException):
            db_bill_repository.get_by_id(tenant_id=another_db_tenant.id, bill_id=db_sample_bill.id)


class TestDBBillRepositoryGetMany:
    def test_get_all_bills_for_tenant(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_bills: list[DBBill],
    ):
        bills = list(db_bill_repository.get_many(tenant_id=db_tenant.id))

        assert len(bills) == 4
        assert all(isinstance(bill, Bill) for bill in bills)
        assert all(bill.tenant_id == db_tenant.id for bill in bills)

    def test_get_bills_with_date_range_filter(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_bills: list[DBBill],
    ):
        date_range = (datetime.date(2025, 1, 12), datetime.date(2025, 1, 18))
        bills = list(db_bill_repository.get_many(tenant_id=db_tenant.id, date_range=date_range))

        assert len(bills) == 1
        assert bills[0].date == datetime.date(2025, 1, 15)

    def test_get_bills_with_category_filter(
        self,
        db_bill_repository: DBBillRepository,
        session: Session,
        db_tenant: DBTenant,
        db_category: DBCategory,
        another_category: DBCategory,
        another_bill: DBBill,
        db_bills: list[DBBill],
    ):
        bills = list(
            db_bill_repository.get_many(tenant_id=db_tenant.id, category_id=db_category.id),
        )

        assert len(bills) == 4
        assert all(bill.category_id == db_category.id for bill in bills)

    def test_get_bills_with_value_range_filter(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_bills: list[DBBill],
    ):
        value_range = (150.00, 250.00)
        bills = list(db_bill_repository.get_many(tenant_id=db_tenant.id, value_range=value_range))

        assert len(bills) == 2
        assert all(150.00 <= bill.value <= 250.00 for bill in bills)

    def test_get_bills_with_multiple_filters(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_bills: list[DBBill],
    ):
        date_range = (datetime.date(2025, 1, 1), datetime.date(2025, 1, 31))
        value_range = (150.00, 300.00)

        bills = list(
            db_bill_repository.get_many(
                tenant_id=db_tenant.id,
                date_range=date_range,
                value_range=value_range,
            ),
        )

        assert len(bills) == 2
        assert all(bill.date.month == 1 for bill in bills)
        assert all(150.00 <= bill.value <= 300.00 for bill in bills)

    def test_get_bills_with_no_results(self, db_bill_repository: DBBillRepository, db_tenant: DBTenant):
        date_range = (datetime.date(2020, 1, 1), datetime.date(2020, 12, 31))
        bills = list(db_bill_repository.get_many(tenant_id=db_tenant.id, date_range=date_range))

        assert len(bills) == 0

    def test_get_bills_returns_generator(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_bills: list[DBBill],
    ):
        result = db_bill_repository.get_many(tenant_id=db_tenant.id)

        assert isinstance(result, Generator)
        bills = list(result)
        assert len(bills) == 4


class TestDBBillRepositoryUpdate:
    def test_update_bill_date(self, db_bill_repository: DBBillRepository, db_tenant: DBTenant, db_sample_bill: DBBill):
        new_date = datetime.date(2025, 2, 1)
        original_value = db_sample_bill.value
        original_category_id = db_sample_bill.category_id

        updated_bill = db_bill_repository.update(
            tenant_id=db_tenant.id,
            bill_id=db_sample_bill.id,
            date=new_date,
        )

        assert updated_bill.date == new_date
        assert updated_bill.value == original_value
        assert updated_bill.category_id == original_category_id

    def test_update_bill_value(self, db_bill_repository: DBBillRepository, db_tenant: DBTenant, db_sample_bill: DBBill):
        new_value = 999.99
        original_date = db_sample_bill.date
        original_category_id = db_sample_bill.category_id

        updated_bill = db_bill_repository.update(
            tenant_id=db_tenant.id,
            bill_id=db_sample_bill.id,
            value=new_value,
        )

        assert updated_bill.value == new_value
        assert updated_bill.date == original_date
        assert updated_bill.category_id == original_category_id

    def test_update_bill_category(
        self,
        db_bill_repository: DBBillRepository,
        session: Session,
        db_tenant: DBTenant,
        db_sample_bill: DBBill,
        another_category: DBCategory,
    ):
        original_date = db_sample_bill.date
        original_value = db_sample_bill.value

        updated_bill = db_bill_repository.update(
            tenant_id=db_tenant.id,
            bill_id=db_sample_bill.id,
            category_id=another_category.id,
        )

        assert updated_bill.category_id == another_category.id
        assert updated_bill.date == original_date
        assert updated_bill.value == original_value

    def test_update_bill_multiple_fields(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_sample_bill: DBBill,
    ):
        new_date = datetime.date(2025, 3, 1)
        new_value = 500.00

        updated_bill = db_bill_repository.update(
            tenant_id=db_tenant.id,
            bill_id=db_sample_bill.id,
            date=new_date,
            value=new_value,
        )

        assert updated_bill.date == new_date
        assert updated_bill.value == new_value

    def test_update_bill_with_none_values(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_sample_bill: DBBill,
    ):
        original_date = db_sample_bill.date
        original_value = db_sample_bill.value
        original_category_id = db_sample_bill.category_id

        updated_bill = db_bill_repository.update(
            tenant_id=db_tenant.id,
            bill_id=db_sample_bill.id,
            date=None,
            value=None,
            category_id=None,
        )

        assert updated_bill.date == original_date
        assert updated_bill.value == original_value
        assert updated_bill.category_id == original_category_id

    def test_update_nonexistent_bill(self, db_bill_repository: DBBillRepository, db_tenant: DBTenant):
        with pytest.raises(BillNotFoundException):
            db_bill_repository.update(
                tenant_id=db_tenant.id,
                bill_id=99999,
                value=100.00,
            )

    def test_update_bill_from_different_tenant(
        self,
        db_bill_repository: DBBillRepository,
        session: Session,
        db_sample_bill: DBBill,
        another_tenant: DBTenant,
    ):
        with pytest.raises(BillNotFoundException):
            db_bill_repository.update(
                tenant_id=another_tenant.id,
                bill_id=db_sample_bill.id,
                value=100.00,
            )


class TestDBBillRepositoryEdgeCases:
    def test_create_bill_with_very_large_value(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_category: DBCategory,
    ):
        date = datetime.date(2025, 1, 20)
        value = 999999999.99

        bill = db_bill_repository.create(
            tenant_id=db_tenant.id,
            date=date,
            value=value,
            category_id=db_category.id,
        )

        assert bill.value == value

    def test_create_bill_with_future_date(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_category: DBCategory,
    ):
        future_date = datetime.date(2030, 12, 31)

        with pytest.raises(FutureDateException):
            db_bill_repository.create(
                tenant_id=db_tenant.id,
                date=future_date,
                value=100.00,
                category_id=db_category.id,
            )

    def test_create_bill_with_past_date(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_category: DBCategory,
    ):
        past_date = datetime.date(1900, 1, 1)

        bill = db_bill_repository.create(
            tenant_id=db_tenant.id,
            date=past_date,
            value=100.00,
            category_id=db_category.id,
        )

        assert bill.date == past_date

    def test_get_many_with_same_start_and_end_date(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_sample_bill: DBBill,
    ):
        date_range = (db_sample_bill.date, db_sample_bill.date)
        bills = list(db_bill_repository.get_many(tenant_id=db_tenant.id, date_range=date_range))

        assert len(bills) == 1
        assert bills[0].id == db_sample_bill.id

    def test_get_many_with_inverted_value_range(
        self,
        db_bill_repository: DBBillRepository,
        db_tenant: DBTenant,
        db_sample_bill: DBBill,
    ):
        value_range = (1000.00, 1.00)
        bills = list(db_bill_repository.get_many(tenant_id=db_tenant.id, value_range=value_range))

        assert len(bills) == 0
