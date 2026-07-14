"""关键缺陷的无数据库回归测试。"""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from app.models import FeedbackRequest, MemberUpdate, ProductCreate
from app.routers import drafts, history, members, products, templates


class _Cursor:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))


class RegressionTests(unittest.TestCase):
    def test_product_id_rejects_path_traversal(self):
        with self.assertRaises(ValidationError):
            ProductCreate(id="../../config", name="bad")

    def test_upload_paths_cannot_escape_upload_root(self):
        self.assertIsNone(products._stored_upload_path("/config.py"))
        self.assertIsNone(products._stored_upload_path("/uploads/products/../../config.py"))
        safe = products._stored_upload_path("/uploads/products/P001/manual.pdf")
        self.assertIsNotNone(safe)
        self.assertEqual(safe.name, "manual.pdf")
        self.assertTrue(Path(safe).is_relative_to(products.UPLOAD_ROOT.resolve()))

        with self.assertRaises(HTTPException) as ctx:
            products._safe_product_dir("../../outside")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_finalize_is_idempotent_after_history_created(self):
        now = datetime.now(timezone.utc)
        existing = {
            "id": "D1", "user_id": "U1", "product_id": "P1",
            "scenario_id": "S1", "history_id": "H1", "stage": "done",
            "created_at": now, "updated_at": now,
        }
        with patch.object(drafts, "_get_owned_draft", return_value=existing), \
             patch.object(drafts, "get_orchestrator") as get_orchestrator:
            result = drafts.finalize_draft("D1", {"id": "U1", "is_admin": False})
        self.assertEqual(result.history_id, "H1")
        get_orchestrator.assert_not_called()

    def test_feedback_updates_only_current_users_json_key(self):
        cursor = _Cursor()

        @contextmanager
        def fake_transaction():
            yield cursor

        with patch.object(history, "query_one", return_value={"id": "H1"}), \
             patch.object(history, "transaction", fake_transaction), \
             patch.object(history, "get_history", return_value={"id": "H1"}):
            history.set_feedback(
                "H1", FeedbackRequest(feedback="like"), {"id": "U1"}
            )

        sql, params = cursor.calls[0]
        self.assertIn("jsonb_build_object", sql)
        self.assertEqual(params, ("U1", "like", "H1"))

    def test_other_users_pending_template_is_not_visible(self):
        row = {
            "id": "T1", "scenario_id": "S1", "status": "pending",
            "created_by": "U2",
        }
        with patch.object(templates, "query_one", return_value=row):
            with self.assertRaises(HTTPException) as ctx:
                templates.get_template("S1", "T1", {"id": "U1", "is_admin": False})
        self.assertEqual(ctx.exception.status_code, 404)

    def test_last_admin_cannot_be_demoted(self):
        with patch.object(
            members,
            "query_one",
            side_effect=[{"id": "U1", "is_admin": True}, {"count": 1}],
        ):
            with self.assertRaises(HTTPException) as ctx:
                members.update_member(
                    "U1", MemberUpdate(is_admin=False), {"id": "U1", "is_admin": True}
                )
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
