"""服务层异常：API 层统一映射为 HTTP 状态码。"""


class ComplianceError(Exception):
    """合规校验不通过 → 422。"""


class ConsentRequired(ComplianceError):
    """未成年人缺少有效监护人单独同意。"""


class ProgramViolation(ComplianceError):
    """活动备案/配置存在 error 级违规。

    - violations: list[dict]，每项 {code, message, level}
    """

    def __init__(self, violations: list[dict]):
        self.violations = violations
        super().__init__("; ".join(v["message"] for v in violations))


class StudentNotFound(Exception):
    """学员主索引查无此人 → 404。"""


class NotFound(Exception):
    """通用资源不存在 → 404。"""
