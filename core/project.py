@dataclass
class Project:
    name: str
    root: Path
    version: str = "0.1.0"
    template: str | None = None
    author: str | None = None
    python_version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path) -> "Project":
        ...

    def save(self) -> None:
        ...

    def validate(self) -> bool:
        ...

    def exists(self) -> bool:
        ...

    def to_dict(self) -> dict[str, Any]:
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        ...