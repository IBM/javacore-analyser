#
# Copyright IBM Corp. 2025
# SPDX-License-Identifier: Apache-2.0
#
import os
import shutil
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
        # Keep TESTING=True for routing but let Flask convert unhandled exceptions into
        # 500 responses so tests can assert on status codes rather than catching exceptions.
        javacore_analyser_web.app.config["PROPAGATE_EXCEPTIONS"] = False
        self.client = javacore_analyser_web.app.test_client()
        # Create the temp staging directory that upload_file() expects to exist
        os.makedirs(os.path.join(self.reports_tmp.name, TEMP_DIR), exist_ok=True)

    def tearDown(self):
        self.reports_tmp.cleanup()
        # Restore propagation default so other test modules are not affected
        javacore_analyser_web.app.config["PROPAGATE_EXCEPTIONS"] = True


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
    # Path traversal protection for /zip and /delete
    # ------------------------------------------------------------------
    def _create_outside_secret(self):
        """Create a file beside the reports dir (in its parent) that must never be exposed."""
        parent = os.path.dirname(os.path.realpath(self.reports_tmp.name))
        secret = os.path.join(parent, "secret-%s.txt" % os.path.basename(self.reports_tmp.name))
        with open(secret, "w") as f:
            f.write("TOP-SECRET")
        self.addCleanup(os.remove, secret)
        return secret

    def test_zip_valid_report_returns_archive(self):
        report = os.path.join(self.reports_tmp.name, "my_report")
        os.makedirs(report)
        with open(os.path.join(report, "index.html"), "w") as f:
            f.write("<html/>")
        self._login()
        resp = self.client.get("/zip/my_report")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data.startswith(b"PK"))
        resp.close()

    def test_zip_path_traversal_is_rejected(self):
        self._create_outside_secret()
        self._login()
        for path in ["..", "%2e%2e", "../", "my_report/..", "../../etc", "%2e%2e/%2e%2e"]:
            resp = self.client.get("/zip/" + path)
            self.assertIn(resp.status_code, (301, 308, 404), path)
            self.assertNotIn(b"TOP-SECRET", resp.data, path)
            self.assertFalse(resp.data.startswith(b"PK"), path)

    def test_zip_reports_dir_itself_is_rejected(self):
        self._login()
        self.assertEqual(self.client.get("/zip/.").status_code, 404)

    def test_zip_symlink_escaping_reports_dir_is_rejected(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        with open(os.path.join(outside.name, "secret.txt"), "w") as f:
            f.write("TOP-SECRET")
        os.symlink(outside.name, os.path.join(self.reports_tmp.name, "link"))
        self._login()
        resp = self.client.get("/zip/link")
        self.assertEqual(resp.status_code, 404)

    def test_zip_nonexistent_report_returns_404(self):
        self._login()
        self.assertEqual(self.client.get("/zip/does_not_exist").status_code, 404)

    def test_delete_path_traversal_is_rejected(self):
        secret = self._create_outside_secret()
        parent = os.path.dirname(secret)
        self._login()
        for path in ["..", "%2e%2e", "../" + os.path.basename(parent)]:
            resp = self.client.get("/delete/" + path)
            self.assertNotEqual(resp.status_code, 302, path)
        self.assertTrue(os.path.exists(secret))

    def test_delete_sibling_directory_with_same_prefix_is_rejected(self):
        sibling = self.reports_tmp.name + "_evil"
        os.makedirs(sibling)
        self.addCleanup(shutil.rmtree, sibling, True)
        self._login()
        resp = self.client.get("/delete/../" + os.path.basename(sibling))
        self.assertEqual(resp.status_code, 503)
        self.assertTrue(os.path.isdir(sibling))

    def test_delete_valid_report(self):
        report = os.path.join(self.reports_tmp.name, "my_report")
        os.makedirs(report)
        self._login()
        resp = self.client.get("/delete/my_report")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(os.path.exists(report))

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
