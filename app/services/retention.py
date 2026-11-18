"""保存年限策略（法规→策略常量）。"""
from __future__ import annotations

RETENTION_RULES = [
    {
        "key": "audit_log_years",
        "years": 2,
        "label": "操作/网络日志",
        "basis": "网安法（2025修正）第23条：留存不少于6个月，系统按2年留存",
    },
    {
        "key": "pia_years",
        "years": 3,
        "label": "个人信息保护影响评估（PIA）报告",
        "basis": "PIPL 第56条：评估报告和处理情况记录至少保存三年",
    },
    {
        "key": "study_abroad_contract_years",
        "years": 5,
        "label": "留学服务合同文本",
        "basis": "GF-2016-1002 示范文本说明：建议中介机构至少保存五年",
    },
    {
        "key": "contract_years",
        "years": 30,
        "label": "合同/会计凭证",
        "basis": "《会计档案管理办法》（财政部、国家档案局令第79号）：最低保管30年",
    },
]


def get_retention() -> dict:
    return {"rules": RETENTION_RULES}
