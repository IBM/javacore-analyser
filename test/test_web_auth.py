#
# Copyright IBM Corp. 2025
# SPDX-License-Identifier: Apache-2.0
#
import os
import tempfile
import unittest

from javacore_analyser import javacore_analyser_web


class TestWebAuth(unittest.TestCase):
    """Tests that every application endpoint requires authentication (CWE-200 / CWE-306 fix)."""

    def setUp(self):
        """Configure the Flask test client with a fixed token and a temporary reports directory."""
        from javacore_analyser.constants import TEMP_DIR
        self.reports_tmp = tempfile.TemporaryDirectory()
        # Set global state the same way run_web() does, but without starting a server.
        javacore_analyser_web.reports_dir = self.reports_tmp.name
        javacore_analyser_web._access_token = "test-token-abc"
        javacore_analyser_web.app.secret_key = b"test-secret-key"
        javacore_analyser_web.app.config["TESTING"] = True
        self.client = javacore_analyser_web.app.test_client()
        # Create the temp staging directory that upload_file() expects to exist
        os.makedirs(os.path.join(self.reports_tmp.name, TEMP_DIR), exist_ok=True)

    def tearDown(self):
        self.reports_tmp.cleanup()

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def _login(self, token="test-token-abc"):
        return self.client.post("/login", data={"token": token}, follow_redirects=False)

    # ------------------------------------------------------------------
    # Unauthenticated access must be redirected to /login
    # ------------------------------------------------------------------
    def test_index_unauthenticated_redirects_to_login(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_reports_unauthenticated_redirects_to_login(self):
        resp = self.client.get("/reports/some_report/index.html")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_zip_unauthenticated_redirects_to_login(self):
        resp = self.client.get("/zip/some_report")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_delete_unauthenticated_redirects_to_login(self):
        resp = self.client.get("/delete/some_report")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_upload_unauthenticated_redirects_to_login(self):
        resp = self.client.post("/upload", data={})
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    # ------------------------------------------------------------------
    # /login endpoint is publicly accessible
    # ------------------------------------------------------------------
    def test_login_page_is_publicly_accessible(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)

    def test_login_with_wrong_token_stays_on_login_page(self):
        resp = self._login(token="wrong-token")
        # Should NOT redirect to index — stays on /login (200) or re-renders with error
        self.assertNotEqual(resp.status_code, 302)

    def test_login_with_wrong_token_shows_error(self):
        resp = self._login(token="wrong-token")
        self.assertIn(b"Invalid token", resp.data)

    def test_login_with_correct_token_redirects_to_index(self):
        resp = self._login(token="test-token-abc")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/", resp.headers["Location"])

    # ------------------------------------------------------------------
    # Authenticated session can reach protected endpoints
    # ------------------------------------------------------------------
    def test_index_accessible_after_login(self):
        # Create a fake completed report directory so index() has something to scan
        os.makedirs(os.path.join(self.reports_tmp.name, "my_report"))
        # Also create the TEMP_DIR that the application expects
        from javacore_analyser.constants import TEMP_DIR
        os.makedirs(os.path.join(self.reports_tmp.name, TEMP_DIR), exist_ok=True)
        self._login()
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    # ------------------------------------------------------------------
    # Logout clears the session
    # ------------------------------------------------------------------
    def test_logout_ends_session(self):
        self._login()
        self.client.get("/logout")
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    # ------------------------------------------------------------------
    # Token generation: empty/None token triggers random token generation
    # ------------------------------------------------------------------
    def test_run_web_generates_random_token_when_none_given(self):
        import secrets as _secrets
        # run_web assigns _access_token; we intercept the assignment.
        original = javacore_analyser_web._access_token
        try:
            # Patch the server calls so we don't actually start listening
            import unittest.mock as mock
            with mock.patch("javacore_analyser.javacore_analyser_web.serve"), \
                 mock.patch("javacore_analyser.javacore_analyser_web.create_temp_data_in_reports_dir"), \
                 mock.patch("javacore_analyser.javacore_analyser_web.create_file_logging"), \
                 mock.patch("javacore_analyser.javacore_analyser_web.create_console_logging"):
                javacore_analyser_web.run_web(
                    debug=False, port=9999,
                    reports_directory=self.reports_tmp.name,
                    token=None
                )
            token_after = javacore_analyser_web._access_token
            self.assertTrue(len(token_after) >= 32, "Generated token should be at least 32 chars")
        finally:
            javacore_analyser_web._access_token = original

    def test_run_web_uses_configured_token(self):
        original = javacore_analyser_web._access_token
        try:
            import unittest.mock as mock
            with mock.patch("javacore_analyser.javacore_analyser_web.serve"), \
                 mock.patch("javacore_analyser.javacore_analyser_web.create_temp_data_in_reports_dir"), \
                 mock.patch("javacore_analyser.javacore_analyser_web.create_file_logging"), \
                 mock.patch("javacore_analyser.javacore_analyser_web.create_console_logging"):
                javacore_analyser_web.run_web(
                    debug=False, port=9999,
                    reports_directory=self.reports_tmp.name,
                    token="my-configured-token"
                )
            self.assertEqual(javacore_analyser_web._access_token, "my-configured-token")
        finally:
            javacore_analyser_web._access_token = original

    # ------------------------------------------------------------------
    # Upload path-traversal (CWE-22 fix)
    # ------------------------------------------------------------------
    def _upload(self, filename, content=b"data"):
        """POST to /upload as an authenticated client with a single file."""
        self._login()
        from io import BytesIO
        return self.client.post(
            "/upload",
            data={
                "report_name": "test_report",
                "files": (BytesIO(content), filename),
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )

    def test_upload_traversal_dotdot_rejected(self):
        resp = self._upload("../../etc/passwd")
        # Must not be a 2xx success that wrote the file
        self.assertNotEqual(resp.status_code // 100, 2,
                            "Path traversal filename must not succeed")

    def test_upload_absolute_path_rejected(self):
        resp = self._upload("/etc/passwd")
        self.assertNotEqual(resp.status_code // 100, 2,
                            "Absolute path filename must not succeed")

    def test_upload_separator_only_rejected(self):
        """A filename of '/' or '../../' has an empty basename and must be rejected."""
        resp = self._upload("/")
        self.assertNotEqual(resp.status_code // 100, 2,
                            "Separator-only filename must not succeed")

    def test_upload_normal_filename_accepted(self):
        """A safe filename should be accepted (processing may fail for other reasons,
        but the path-traversal guard must not block it)."""
        import unittest.mock as mock
        with mock.patch(
            "javacore_analyser.javacore_analyser_batch.process_javacores_and_generate_report_data"
        ):
            resp = self._upload("javacore.20220606.114458.32888.0001.txt", b"content")
        # 302 redirect to the report page means the file was accepted and processing started
        self.assertEqual(resp.status_code, 302)

    def test_upload_traversal_does_not_write_outside_reports_dir(self):
        """Confirm no file is created outside the reports directory."""
        import tempfile, os
        # Use a filename that would escape to the system temp dir
        target = os.path.join(tempfile.gettempdir(), "traversal_test_canary.txt")
        if os.path.exists(target):
            os.remove(target)
        self._upload("../../../tmp/traversal_test_canary.txt", b"canary")
        self.assertFalse(os.path.exists(target),
                         "Path traversal must not write files outside the reports directory")


if __name__ == '__main__':
    unittest.main()
