import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "refresh-data.yml"


class RefreshWorkflowTests(unittest.TestCase):
    def test_cloudflare_secrets_are_optional_for_data_refresh(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("Commit and push changes", workflow)
        self.assertIn("Deploy latest data to Cloudflare Pages", workflow)
        self.assertNotIn("exit \"$missing\"", workflow)
        self.assertRegex(
            workflow,
            re.compile(
                r"Deploy latest data to Cloudflare Pages.*?"
                r"if:.*steps\.cloudflare_deploy\.outputs\.has_secrets == 'true'",
                re.DOTALL,
            ),
        )

    def test_cloudflare_deploy_does_not_use_deprecated_node20_action(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertNotIn("cloudflare/wrangler-action@v3", workflow)
        self.assertRegex(workflow, r"node-version:\s*\"24\"")
        self.assertIn("npx --yes wrangler@4 pages deploy web", workflow)


if __name__ == "__main__":
    unittest.main()
