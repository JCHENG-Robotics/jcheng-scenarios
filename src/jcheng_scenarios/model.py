"""Validation report types shared by the CLI and the tests."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Issue:
    """One validation problem, addressed by code and document path."""

    code: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


@dataclass(frozen=True)
class ScenarioSummary:
    """A scenario that passed structural validation."""

    id: str
    version: str
    path: str
    delivery: str
    verification: str
    profiles: int

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "version": self.version,
            "path": self.path,
            "delivery": self.delivery,
            "verification": self.verification,
            "profiles": self.profiles,
        }


@dataclass
class ValidationReport:
    """Aggregate result for one catalog root."""

    root: str
    scenarios: list[ScenarioSummary] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def add(self, code: str, path: object, message: str) -> None:
        self.issues.append(Issue(code=code, path=str(path), message=message))

    def to_dict(self) -> dict[str, object]:
        return {
            "result": "pass" if self.ok else "fail",
            "root": self.root,
            "counts": {
                "scenarios": len(self.scenarios),
                "profiles": sum(item.profiles for item in self.scenarios),
                "errors": len(self.issues),
            },
            "scenarios": [item.to_dict() for item in self.scenarios],
            "issues": [item.to_dict() for item in self.issues],
        }
