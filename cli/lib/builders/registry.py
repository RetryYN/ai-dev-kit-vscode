class BuilderRegistry:
    _builders: dict[str, type] = {}

    @classmethod
    def register(cls, builder_cls: type):
        builder_type = getattr(builder_cls, "BUILDER_TYPE", "")
        if not builder_type:
            raise ValueError("BUILDER_TYPE is required")
        cls._builders[str(builder_type)] = builder_cls

    @classmethod
    def get(cls, builder_type: str) -> type:
        if builder_type not in cls._builders:
            raise ValueError(f"Unknown builder type: {builder_type}")
        return cls._builders[builder_type]

    @classmethod
    def list_types(cls) -> list[str]:
        return sorted(cls._builders.keys())
