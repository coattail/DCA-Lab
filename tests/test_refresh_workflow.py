import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "refresh-data.yml"
PAGES_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "deploy-pages.yml"


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

    def test_refresh_deploys_pages_before_pushing_new_commit(self) -> None:
        refresh_workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        pages_workflow = PAGES_WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertRegex(refresh_workflow, r"pages:\s*write")
        self.assertRegex(refresh_workflow, r"id-token:\s*write")
        self.assertIn("actions/configure-pages@v6", refresh_workflow)
        self.assertIn("actions/upload-pages-artifact@v5", refresh_workflow)
        self.assertIn("actions/deploy-pages@v5", refresh_workflow)
        self.assertLess(
            refresh_workflow.index("Deploy latest data to GitHub Pages"),
            refresh_workflow.index("Commit and push changes"),
        )

        self.assertRegex(pages_workflow, r"branches:\s*\n\s*- main")
        self.assertRegex(pages_workflow, r"pages:\s*write")
        self.assertRegex(pages_workflow, r"id-token:\s*write")
        self.assertIn("actions/configure-pages@v6", pages_workflow)
        self.assertIn("actions/upload-pages-artifact@v5", pages_workflow)
        self.assertIn("actions/deploy-pages@v5", pages_workflow)


if __name__ == "__main__":
    unittest.main()
