from unittest.mock import MagicMock
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.assessment_service import save_assessment


def test_save_assessment_commits_and_returns_record():
    db = MagicMock()

    result = save_assessment(
        db=db,
        input_data={"Age": 21},
        predicted_score=6.08,
        model_version="rf-student-mental-health-v1",
    )

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(db.add.call_args.args[0])

    assert result is db.add.call_args.args[0]


def test_save_assessment_rolls_back_on_failure():
    db = MagicMock()
    db.commit.side_effect = RuntimeError("Database failure")

    with pytest.raises(RuntimeError):
        save_assessment(
            db=db,
            input_data={"Age": 21},
            predicted_score=6.08,
            model_version="rf-student-mental-health-v1",
        )

    db.rollback.assert_called_once()


def test_get_assessments_orders_newest_first():
    from sqlalchemy.dialects import postgresql

    from app.services.assessment_service import get_assessments

    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    get_assessments(db=db, skip=10, limit=5)

    statement = db.scalars.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())

    sql = str(compiled)

    assert (
        "ORDER BY assessments.created_at DESC, assessments.id DESC"
        in sql
    )
    assert compiled.params["param_1"] == 5
    assert compiled.params["param_2"] == 10
