from __future__ import annotations

from .store import BuilderStore


class BuilderBase:
    """全ビルダーの基底クラス"""

    BUILDER_TYPE: str = ""
    SCHEMA_VERSION: str = "1.0"

    def __init__(self, store: BuilderStore, project_root: str):
        self.store = store
        self.project_root = project_root
        self._execution_id: str | None = None

    # --- テンプレートメソッド ---
    def build(
        self,
        task_id: str,
        input_params: dict,
        seed_execution_id: str | None = None,
    ) -> dict:
        """メインエントリポイント"""
        self.start(task_id, input_params)
        try:
            validated = self.validate_input(input_params)
            self.step("validate_input", {"valid": True})

            seed = None
            if seed_execution_id:
                seed = self.store.get_execution(seed_execution_id)

            artifacts = self.generate(validated, seed)
            self.step("generate", {"artifact_count": len(artifacts)})

            validation = self.validate_output(artifacts)
            self.step("validate_output", validation)

            self.finish(success=True, artifacts=artifacts, validation=validation)
            return {"execution_id": self._execution_id, "artifacts": artifacts}
        except Exception as exc:
            self.finish(success=False, error=str(exc))
            raise

    # --- サブクラスが実装する抽象メソッド ---
    def validate_input(self, params: dict) -> dict:
        raise NotImplementedError

    def generate(self, params: dict, seed: dict | None) -> list[dict]:
        raise NotImplementedError

    def validate_output(self, artifacts: list[dict]) -> dict:
        raise NotImplementedError

    # --- ライフサイクル ---
    def start(self, task_id: str, input_params: dict):
        if not self.BUILDER_TYPE:
            raise ValueError("BUILDER_TYPE is required")

        self._execution_id = self.store.create_execution(
            builder_type=self.BUILDER_TYPE,
            task_id=task_id,
            input_params=input_params,
            schema_version=self.SCHEMA_VERSION,
        )

    def step(self, name: str, data: dict):
        if not self._execution_id:
            raise RuntimeError("Builder execution is not started")
        self.store.add_step(self._execution_id, name, data)

    def finish(
        self,
        success: bool,
        artifacts: list[dict] | None = None,
        validation: dict | None = None,
        error: str | None = None,
    ):
        if not self._execution_id:
            return
        self.store.finish_execution(
            self._execution_id,
            success=success,
            artifacts=artifacts or [],
            validation=validation or {},
            error=error,
        )
