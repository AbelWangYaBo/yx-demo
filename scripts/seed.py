"""种子数据（虚构示例，幂等）：已存在学校库时直接跳过。

演示故事线（菲律宾游学中介）：
  - 小雨（14岁·亲子）：QQ English Family 8周，报价确认→报名→材料准备中
  - 小航（21岁）：EV IELTS 保分班 12周，完整闭环（报价→确认→LOA→签证→缴费
    （CNY定金/USD学费/PHP当地费）→行前→入学→SSP+ACR→在读含分班测试与周报）
  - 小澈（14岁）：CIA Junior Camp 团体营（出境游学备案+师生比+WEG）
  - 小澄（28岁）：SMEAG ESL 4周，开课前2周取消 → 退费案例（已终止）
  - 小汐（23岁）：意向学员，免费CEFR测试 + 两份报价单比价中
学校名为公开信息，价格为演示虚构值。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal  # noqa: E402
from app.models import Agency, School  # noqa: E402
from app.services import crud_helpers as ch  # noqa: E402

ACTOR = "种子脚本"

AGENCY = {
    "name": "示例远航国际游学（虚构）",
    "uscc": "91370000DEMO2026XYZ1",
    "travel_license_no": "L-SD-DEMO2026001",
    "outbound_licensed": True,
    "license_expiry": "2028-06-30",
    "filing_status": "已备案",
    "filing_no": "BA-2026-DEMO-0841-001",
    "filing_date": "2026-10-20",
    "premise_proof": "办公场所租赁合同（虚构示例）.pdf",
    "policy_documents": [
        "人员管理制度", "教育培训制度", "资料保存制度", "数据安全管理制度", "合规管理制度",
    ],
}

STAFF = [
    {"name": "负责人甲（虚构）", "role": "法定代表人", "id_card_masked": "3701**********0011",
     "no_crime_declaration": True, "filing_status": "已备案", "filing_date": "2026-10-20",
     "expiry_date": "2027-10-20"},
    {"name": "顾问乙（虚构）", "role": "顾问", "id_card_masked": "3701**********0022",
     "no_crime_declaration": True, "filing_status": "已备案", "filing_date": "2026-10-20",
     "expiry_date": "2027-10-20"},
    {"name": "顾问丙（虚构）", "role": "顾问", "id_card_masked": "3701**********0033",
     "no_crime_declaration": False, "filing_status": "未备案"},
]

# 学校库（价格为演示虚构值）+ 课程价目（USD/周，含食宿，按房型）
SCHOOLS = [
    {"name": "EV Academy", "region": "宿务", "style": "斯巴达", "commission_rate": "25",
     "registration_fee_usd": "100", "verified": True,
     "cooperation_agreement": "2026合作协议（虚构示例）.pdf",
     "notes": "雅思强化标杆校，每日词汇测验+每周四全真模考（虚构演示）",
     "courses": [
         {"name": "IELTS 保分班", "course_type": "IELTS保分", "lessons": "1对1×4 + 团体×3",
          "min_weeks": 12, "room_prices": {"4人间": 310, "3人间": 330, "2人间": 365, "1人间": 430},
          "guarantee": "未达目标分免费延长就读（免学费，食宿自理）；要求出勤≥97%且模考全勤（虚构演示）"},
         {"name": "密集 ESL", "course_type": "密集ESL", "lessons": "1对1×5 + 团体×2 + 夜课×2",
          "min_weeks": 4, "room_prices": {"4人间": 255, "3人间": 275, "2人间": 310, "1人间": 380}},
     ]},
    {"name": "SMEAG", "region": "宿务", "style": "半斯巴达", "commission_rate": "20",
     "registration_fee_usd": "100", "verified": True,
     "cooperation_agreement": "2026合作协议（虚构示例）.pdf",
     "notes": "宿务唯一雅思+托业+托福官方考场，Capital校区前4周强制斯巴达（虚构演示）",
     "courses": [
         {"name": "ESL 一般英文", "course_type": "ESL", "lessons": "1对1×4 + 团体×2 + 选修×4",
          "min_weeks": 4, "room_prices": {"4人间": 180, "3人间": 205, "2人间": 240, "1人间": 310}},
         {"name": "TOEIC 保分班", "course_type": "TOEIC保分", "lessons": "1对1×4 + 团体×3",
          "min_weeks": 8, "room_prices": {"4人间": 230, "3人间": 255, "2人间": 290, "1人间": 360}},
     ]},
    {"name": "Philinter", "region": "宿务", "style": "半斯巴达", "commission_rate": "20",
     "registration_fee_usd": "150", "verified": True,
     "cooperation_agreement": "2026合作协议（虚构示例）.pdf",
     "notes": "Mactan岛老牌校，距机场10分钟，商务英语见长（虚构演示）",
     "courses": [
         {"name": "商务英语", "course_type": "商务英语", "lessons": "1对1×4 + 团体×3",
          "min_weeks": 4, "room_prices": {"3人间": 240, "2人间": 275, "1人间": 350}},
     ]},
    {"name": "QQ English", "region": "宿务", "style": "自律型", "commission_rate": "15",
     "registration_fee_usd": "150", "verified": True,
     "cooperation_agreement": "2026合作协议（虚构示例）.pdf",
     "notes": "Callan教学法官方认证校，每周一开课，可自选排课（虚构演示）",
     "courses": [
         {"name": "Family 亲子 ESL", "course_type": "亲子", "lessons": "1对1×4 + 团体×2",
          "min_weeks": 4, "room_prices": {"4人间": 200, "3人间": 225, "2人间": 260, "1人间": 330},
          "notes": "15岁以下学员须家长同校上课（虚构演示）"},
     ]},
    {"name": "PINES", "region": "碧瑶", "style": "斯巴达", "commission_rate": "25",
     "registration_fee_usd": "100", "verified": True,
     "cooperation_agreement": "2026合作协议（虚构示例）.pdf",
     "notes": "碧瑶老牌斯巴达，气候凉爽、学费最低，雅思口碑强（虚构演示）",
     "courses": [
         {"name": "密集 ESL", "course_type": "密集ESL", "lessons": "1对1×4 + 团体×4",
          "min_weeks": 4, "room_prices": {"4人间": 170, "3人间": 195, "2人间": 230, "1人间": 300}},
     ]},
    {"name": "CIA", "region": "宿务", "style": "度假村型", "commission_rate": "15",
     "registration_fee_usd": "100", "verified": True,
     "cooperation_agreement": "2026合作协议（虚构示例）.pdf",
     "notes": "度假村式校园，青少年营地管理成熟（虚构演示）",
     "courses": [
         {"name": "Junior Camp 寒假营", "course_type": "冬夏令营",
          "lessons": "1对1×2 + 团体×4 + 营地活动", "min_weeks": 3,
          "room_prices": {"4人间": 520, "3人间": 560},
          "notes": "9-15岁，含SSP/WEG/接机/活动/保险，领队师生比1:10（虚构演示）"},
     ]},
]

STUDENTS = [
    {"student_no": "STU-2027-101", "name": "学员小雨（虚构）", "birth_date": "2012-08-20",
     "guardian_name": "陈女士（虚构）", "guardian_phone": "13800000101",
     "guardian_id_masked": "3701**********0101", "notes": "妈妈计划陪同赴菲上亲子课程（虚构）"},
    {"student_no": "STU-2027-102", "name": "学员小航（虚构）", "birth_date": "2005-03-02",
     "notes": "大三学生，考研英语转雅思，目标6.0（虚构）"},
    {"student_no": "STU-2027-103", "name": "学员小澈（虚构）", "birth_date": "2012-05-30",
     "guardian_name": "刘先生（虚构）", "guardian_phone": "13800000103",
     "guardian_id_masked": "3701**********0103"},
    {"student_no": "STU-2027-104", "name": "学员小澄（虚构）", "birth_date": "1998-07-15",
     "notes": "职场学员，年假充电（虚构）"},
    {"student_no": "STU-2027-105", "name": "学员小汐（虚构）", "birth_date": "2003-01-22",
     "notes": "大四学生，寒假短期提升口语，比价中（虚构）"},
]

# 菲律宾学校退费梯度（I.BREEZE 式条款折算，前端合同预设同源）
PH_REFUND_RULES = [
    {"stage": "开课前4周以上取消", "ratio": "95"},
    {"stage": "开课前2-4周取消", "ratio": "70"},
    {"stage": "开课前1-2周取消", "ratio": "50"},
    {"stage": "开课前1周内取消", "ratio": "20"},
    {"stage": "在读期间（重病等特例）", "ratio": "40"},
    {"stage": "开除/自行退学", "ratio": "0"},
]


def _doc(session, student_id, **kw):
    ch.create_document(session, {"student_id": student_id, **kw}, actor=ACTOR)


def _comm(session, student_id, **kw):
    ch.create_communication(session, {"student_id": student_id, **kw}, actor=ACTOR)


def _event(session, student_id, **kw):
    ch.create_service_event(session, {"student_id": student_id, **kw}, actor=ACTOR)


def _quote(session, student_id, school, course, weeks, room_type, start, status="已发送"):
    from app.services.quotation import create_quotation

    return create_quotation(session, {
        "student_id": student_id, "school_id": school.id, "course_id": course.id,
        "weeks": weeks, "room_type": room_type, "start_date": start, "status": status,
    }, actor=ACTOR)


def main() -> None:
    session = SessionLocal()
    try:
        if session.query(School).first() is not None:
            print("种子数据已存在，跳过（幂等）")
            return

        # 机构 + 人员 + 学校课程库
        agency = ch.create_agency(session, AGENCY, actor=ACTOR)
        for s in STAFF:
            ch.create_staff(session, {**s, "agency_id": agency.id}, actor=ACTOR)
        schools, courses = {}, {}
        for s in SCHOOLS:
            school = ch.create_school(session, {
                k: v for k, v in s.items() if k != "courses"
            }, actor=ACTOR)
            schools[s["name"]] = school
            for c in s["courses"]:
                courses[(s["name"], c["name"])] = ch.create_course(
                    session, {"school_id": school.id, **c}, actor=ACTOR
                )

        students = {s["student_no"]: ch.create_student(session, s, actor=ACTOR) for s in STUDENTS}

        # ============ 小航（21岁）：EV IELTS 保分班 12周，完整闭环 ============
        hang = students["STU-2027-102"]
        ev = schools["EV Academy"]
        ielts = courses[("EV Academy", "IELTS 保分班")]
        _comm(session, hang.id, channel="微信", direction="呼入", occurred_at="2026-07-20 14:20:00",
              operator="顾问乙（虚构）", summary="咨询菲律宾雅思保分班，对比宿务/碧瑶（虚构）")
        _comm(session, hang.id, channel="电话", direction="呼出", occurred_at="2026-07-22 10:00:00",
              operator="顾问乙（虚构）", summary="免费在线测试：CEFR B1+，摸底约雅思4.0（虚构）")
        _doc(session, hang.id, doc_type="护照", doc_no="E88001021（虚构）", expiry_date="2033-03-02")
        q = _quote(session, hang.id, ev, ielts, weeks=12, room_type="4人间", start="2026-09-13")
        from app.services.quotation import confirm_quotation

        confirm_quotation(session, q.id, actor=ACTOR)
        from sqlalchemy import select

        from app.models import Enrollment
        enr_hang = session.scalars(
            select(Enrollment).where(Enrollment.student_id == hang.id)
        ).first()
        _event(session, hang.id, contract_id=None, event_type="报名材料递交", occurred_at="2026-07-29 10:30:00",
               operator="顾问乙（虚构）", remark="报名表+护照复印件递交 EV（虚构）")
        _doc(session, hang.id, doc_type="录取通知书", doc_no="LOA-EV-2026-0913（虚构）",
             issued_date="2026-08-01", remark="学校1个工作日出 LOA+INVOICE（虚构）")
        _event(session, hang.id, event_type="LOA接收", occurred_at="2026-08-01 15:00:00",
               operator="顾问乙（虚构）", remark="床位锁定，2026-09-13 入学（虚构）")
        contract_hang = ch.create_contract(session, {
            "contract_no": "CT-2026-102", "student_id": hang.id,
            "service_scope": ["选校咨询", "代办报名", "签证指导", "机票协助", "行前服务", "在读跟踪"],
            "total_fee": "3820", "currency": "USD", "signed_date": "2026-08-05",
            "refund_rules": PH_REFUND_RULES, "status": "履行中",
        }, actor=ACTOR)
        ch.create_payment(session, {
            "contract_id": contract_hang.id, "type": "定金", "amount": "3000", "currency": "CNY",
            "voucher_no": "INV-102-D", "payee": agency.name,
        }, actor=ACTOR)
        ch.create_payment(session, {
            "contract_id": contract_hang.id, "type": "代收代缴-学费", "amount": "3720", "currency": "USD",
            "voucher_no": "INV-102-T", "payee": "EV Academy（虚构）",
            "proof_file": "学校INVOICE+电汇回单（虚构示例）.pdf",
        }, actor=ACTOR)
        ch.create_payment(session, {
            "contract_id": contract_hang.id, "type": "代收代缴-注册费", "amount": "100", "currency": "USD",
            "voucher_no": "INV-102-R", "payee": "EV Academy（虚构）",
            "proof_file": "学校INVOICE（虚构示例）.pdf",
        }, actor=ACTOR)
        _event(session, hang.id, contract_id=contract_hang.id, event_type="签证办理",
               occurred_at="2026-08-08 09:00:00", operator="顾问乙（虚构)",
               remark="凭LOA办9(a)旅游签（虚构）")
        _doc(session, hang.id, doc_type="签证", doc_no="PH9A-2026-88120（虚构）",
             issued_date="2026-08-15", expiry_date="2026-11-11", remark="59天停留，入学后学校代办延签")
        _doc(session, hang.id, doc_type="机票", doc_no="MU5017 2026-09-12（虚构）",
             issued_date="2026-08-20", remark="周日入学·周六离校口径（虚构）")
        _event(session, hang.id, contract_id=contract_hang.id, event_type="行前说明会",
               occurred_at="2026-09-10 19:00:00", operator="顾问乙（虚构）",
               remark="eTravel登记/电话卡/换汇/入境文件（虚构）")
        _doc(session, hang.id, doc_type="保险单", doc_no="INS-PH-2026-102（虚构）",
             issued_date="2026-09-05", expiry_date="2026-12-10",
             remark="含海外医疗与紧急救援（虚构）")
        # 阶段推进：材料准备 → 已缴费 → 已入学
        from app.services.pipeline import advance_enrollment_stage, advance_student_stage

        for stu_no, to in (("STU-2027-102", "沟通中"), ("STU-2027-102", "已报名"),
                           ("STU-2027-102", "在读")):
            advance_student_stage(session, stu_no, to, actor=ACTOR)
        advance_enrollment_stage(session, enr_hang.id, "材料准备", remark="护照/LOA/签证齐备",
                                 actor=ACTOR)
        advance_enrollment_stage(session, enr_hang.id, "已缴费", remark="定金+学费+注册费到账",
                                 actor=ACTOR)
        advance_enrollment_stage(session, enr_hang.id, "已入学", remark="9-13接机到校（虚构）",
                                 actor=ACTOR)
        _event(session, hang.id, contract_id=contract_hang.id, event_type="接机",
               occurred_at="2026-09-13 21:30:00", operator="学校学生经理（虚构）",
               remark="宿务机场接机，费用含在当地费（虚构）")
        ch.create_payment(session, {
            "contract_id": contract_hang.id, "type": "代收代缴-当地费", "amount": "58200",
            "currency": "PHP", "voucher_no": "INV-102-L", "payee": "EV Academy（虚构）",
            "proof_file": "学校当地费收据（虚构示例）.pdf",
        }, actor=ACTOR)
        # 菲律宾行政链：SSP + ACR I-Card（12周=84天>59天）+ 延签
        _doc(session, hang.id, doc_type="SSP", doc_no="SSP-EV-2026-1042（虚构）",
             issued_date="2026-09-14", expiry_date="2026-12-05",
             remark="特殊学习许可，有效期=课程周数；含SSP E-Card（虚构）")
        _event(session, hang.id, event_type="SSP办理", occurred_at="2026-09-14 11:00:00",
               operator="学校学生经理（虚构）", remark="学校代办，披索现付（虚构）")
        _doc(session, hang.id, doc_type="ACR I-Card", doc_no="ACR-2026-00871（虚构）",
             issued_date="2026-10-20", expiry_date="2027-10-20",
             remark="停留超59天办理，随第一次延签（虚构）")
        _event(session, hang.id, event_type="延签办理", occurred_at="2026-10-20 10:00:00",
               operator="学校学生经理（虚构）", remark="第一次延签+30天（虚构）")
        advance_enrollment_stage(session, enr_hang.id, "在读", remark="分班测试完成，正式开课",
                                 actor=ACTOR)
        # 在读周报：分班测试（W0）+ 每周模考
        for wk in (
            {"week_no": 0, "level": "IELTS 4.0", "test_score": "4.0", "attendance_pct": None,
             "teacher_comment": "分班测试：入中级班，口语偏弱（虚构）",
             "parent_notified_at": "2026-09-14 20:00:00"},
            {"week_no": 2, "level": "IELTS 4.0", "test_score": "4.5", "attendance_pct": 100,
             "teacher_comment": "词汇量明显提升，周四模考4.5（虚构）",
             "parent_notified_at": "2026-09-25 20:00:00"},
            {"week_no": 4, "level": "IELTS 4.5", "test_score": "5.0", "attendance_pct": 100,
             "teacher_comment": "写作结构进步，模考5.0（虚构）", "parent_notified_at": "2026-10-09 20:00:00"},
            {"week_no": 6, "level": "IELTS 5.0", "test_score": "5.0", "attendance_pct": 98,
             "teacher_comment": "平台期，教师建议加练口语（虚构）", "parent_notified_at": "2026-10-23 20:00:00"},
            {"week_no": 8, "level": "IELTS 5.0", "test_score": "5.5", "attendance_pct": 100,
             "teacher_comment": "模考5.5，保分条款生效在望（虚构）", "parent_notified_at": "2026-11-06 20:00:00"},
        ):
            ch.create_weekly_report(session, {
                "enrollment_id": enr_hang.id, **wk,
            }, actor=ACTOR)

        # ============ 小雨（14岁·亲子）：QQ English Family 8周，材料准备中 ============
        yu = students["STU-2027-101"]
        qq = schools["QQ English"]
        family = courses[("QQ English", "Family 亲子 ESL")]
        _comm(session, yu.id, channel="微信", direction="呼入", occurred_at="2026-11-02 09:40:00",
              operator="顾问丙（虚构）", summary="妈妈咨询寒假亲子游学，孩子六年级（虚构）")
        _comm(session, yu.id, channel="电话", direction="呼出", occurred_at="2026-11-05 15:00:00",
              operator="顾问丙（虚构）", summary="孩子在线测试A2，推荐Family课程8周（虚构）")
        _doc(session, yu.id, doc_type="护照", doc_no="E88001101（虚构）", expiry_date="2032-06-30")
        # 未满15岁亲子同行：监护同行证明（家长同校）+ 机构级通用监护人同意
        _doc(session, yu.id, doc_type="监护同行证明", doc_no="同行-2026-1101（虚构）",
             issued_date="2026-11-10", remark="母亲同校 Family 课程，免 WEG（虚构）")
        ch.create_consent(session, {
            "student_id": yu.id, "program_id": None, "consent_type": "敏感信息处理",
            "individual_consent": True, "signer_name": "陈女士（虚构）", "relation": "母亲",
        }, actor=ACTOR)
        q = _quote(session, yu.id, qq, family, weeks=8, room_type="2人间", start="2027-01-10")
        confirm_quotation(session, q.id, actor=ACTOR)
        for to in ("沟通中", "已报名"):
            advance_student_stage(session, "STU-2027-101", to, actor=ACTOR)
        enr_yu = session.scalars(
            select(Enrollment).where(Enrollment.student_id == yu.id)
        ).first()
        advance_enrollment_stage(session, enr_yu.id, "材料准备", remark="已收护照，待LOA（虚构）",
                                 actor=ACTOR)
        _doc(session, yu.id, doc_type="录取通知书", doc_no="LOA-QQ-2027-0110（虚构）",
             issued_date="2026-11-16", remark="2027-01-10 入学，母子同校（虚构）")
        contract_yu = ch.create_contract(session, {
            "contract_no": "CT-2026-101", "student_id": yu.id,
            "service_scope": ["选校咨询", "代办报名", "签证指导", "行前服务"],
            "total_fee": "2230", "currency": "USD", "signed_date": "2026-11-15",
            "refund_rules": PH_REFUND_RULES, "status": "履行中",
        }, actor=ACTOR)
        ch.create_payment(session, {
            "contract_id": contract_yu.id, "type": "定金", "amount": "3000", "currency": "CNY",
            "voucher_no": "INV-101-D", "payee": agency.name,
        }, actor=ACTOR)

        # ============ 小澈（14岁）：CIA Junior Camp 团体营（出境游学备案线）============
        che = students["STU-2027-103"]
        camp_program = ch.create_program(session, {
            "name": "2027寒假宿务CIA少儿英语冬令营（虚构）", "type": "出境游学",
            "departure_date": "2027-01-17", "return_date": "2027-02-06",
            "filing_date": "2026-12-10", "filing_status": "已备案", "status": "筹备中",
            "dest_country_count": 1, "max_cities_per_country": 1,
            "student_age_group": "小学", "teacher_count": 2, "student_count": 16,
            "insurance": {"policy_no": "INS-CAMP-2027", "coverage_per_person_wan": 80,
                          "coverage_per_accident_wan": 1200, "includes_global_rescue": True},
            "emergency_plan": True,
            "partner_school": "CIA（虚构演示）", "school_verified": True,
        }, actor=ACTOR)
        _comm(session, che.id, channel="微信", direction="呼入", occurred_at="2026-11-06 20:10:00",
              operator="顾问乙（虚构）", summary="家长咨询寒假宿务营地，关心安全与手机管理（虚构）")
        _comm(session, che.id, channel="电话", direction="呼出", occurred_at="2026-11-09 11:00:00",
              operator="顾问乙（虚构）", summary="说明1:10领队/每日家长群报/手机统一保管（虚构）")
        ch.create_consent(session, {
            "student_id": che.id, "program_id": camp_program.id, "consent_type": "敏感信息处理",
            "individual_consent": True, "signer_name": "刘先生（虚构）", "relation": "父亲",
        }, actor=ACTOR)
        _doc(session, che.id, doc_type="护照", doc_no="E88001103（虚构）", expiry_date="2033-05-30")
        _doc(session, che.id, doc_type="WEG", doc_no="WEG-2027-103（虚构）",
             issued_date="2026-11-25", remark="未满15岁无父母同行，领队统一办理公证（虚构）")
        _doc(session, che.id, doc_type="保险单", doc_no="INS-CAMP-2027-103（虚构）",
             issued_date="2026-12-20", expiry_date="2027-02-07")
        ch.create_enrollment(session, {
            "student_id": che.id, "program_id": camp_program.id,
            "health_proof": True, "parent_notice_signed": True,
            "course_name": "Junior Camp 寒假营", "accommodation": "4人间（营地宿舍）",
            "pickup_arranged": True, "expected_start": "2027-01-17",
        }, actor=ACTOR)
        for to in ("沟通中", "已报名"):
            advance_student_stage(session, "STU-2027-103", to, actor=ACTOR)
        contract_che = ch.create_contract(session, {
            "contract_no": "CT-2026-103", "student_id": che.id,
            "service_scope": ["营地报名", "签证指导", "行前服务", "领队随营"],
            "total_fee": "26800", "currency": "CNY", "signed_date": "2026-11-12",
            "refund_rules": PH_REFUND_RULES, "status": "履行中",
        }, actor=ACTOR)
        ch.create_payment(session, {
            "contract_id": contract_che.id, "type": "定金", "amount": "5000", "currency": "CNY",
            "voucher_no": "INV-103-D", "payee": agency.name,
        }, actor=ACTOR)

        # ============ 小澄（28岁）：SMEAG ESL 4周，开课前2周取消 → 退费案例 ============
        cheng = students["STU-2027-104"]
        smeag = schools["SMEAG"]
        esl = courses[("SMEAG", "ESL 一般英文")]
        _comm(session, cheng.id, channel="微信", direction="呼入", occurred_at="2026-09-28 12:00:00",
              operator="顾问乙（虚构）", summary="年假4周想强化口语，预算1.5万（虚构）")
        _doc(session, cheng.id, doc_type="护照", doc_no="E88001104（虚构）", expiry_date="2031-08-01")
        q = _quote(session, cheng.id, smeag, esl, weeks=4, room_type="4人间", start="2026-11-15")
        confirm_quotation(session, q.id, actor=ACTOR)
        for to in ("沟通中", "已报名"):
            advance_student_stage(session, "STU-2027-104", to, actor=ACTOR)
        enr_cheng = session.scalars(
            select(Enrollment).where(Enrollment.student_id == cheng.id)
        ).first()
        advance_enrollment_stage(session, enr_cheng.id, "材料准备", actor=ACTOR)
        contract_cheng = ch.create_contract(session, {
            "contract_no": "CT-2026-104", "student_id": cheng.id,
            "service_scope": ["选校咨询", "代办报名", "签证指导"],
            "total_fee": "820", "currency": "USD", "signed_date": "2026-10-10",
            "refund_rules": PH_REFUND_RULES, "status": "履行中",
        }, actor=ACTOR)
        ch.create_payment(session, {
            "contract_id": contract_cheng.id, "type": "定金", "amount": "2000", "currency": "CNY",
            "voucher_no": "INV-104-D", "payee": agency.name,
        }, actor=ACTOR)
        advance_enrollment_stage(session, enr_cheng.id, "已缴费", remark="定金已缴，尾款待缴（虚构）",
                                 actor=ACTOR)
        _comm(session, cheng.id, channel="电话", direction="呼入", occurred_at="2026-11-01 16:30:00",
              operator="顾问乙（虚构）", summary="公司项目突发，申请取消（开课前2周）（虚构）")
        _event(session, cheng.id, contract_id=contract_cheng.id, event_type="取消申请",
               occurred_at="2026-11-01 16:35:00", operator="顾问乙（虚构）",
               remark="开课前14天取消，按梯度退70%（注册费不退）；退款协议待签（虚构）")
        contract_cheng.status = "已解除"
        from app.services.audit import record_audit

        session.flush()
        record_audit(session, ACTOR, "update", "contract", contract_cheng.contract_no,
                     {"before": {"status": "履行中"}, "after": {"status": "已解除"},
                      "reason": "学员开课前取消（虚构）"})
        advance_enrollment_stage(session, enr_cheng.id, "已终止",
                                 remark="开课前2周取消，进入退费流程（虚构）", actor=ACTOR)
        advance_student_stage(session, "STU-2027-104", "已流失", remark="取消游学（虚构）",
                              actor=ACTOR)

        # ============ 小汐（23岁）：意向学员，双报价比价中 ============
        xi = students["STU-2027-105"]
        pines = schools["PINES"]
        pines_esl = courses[("PINES", "密集 ESL")]
        _comm(session, xi.id, channel="微信", direction="呼入", occurred_at="2026-11-14 21:00:00",
              operator="顾问丙（虚构）", summary="寒假4周，口语冲刺，预算有限（虚构）")
        _comm(session, xi.id, channel="电话", direction="呼出", occurred_at="2026-11-15 10:00:00",
              operator="顾问丙（虚构）", summary="免费CEFR测试B1；宿务性价比 vs 碧瑶低价（虚构）")
        advance_student_stage(session, "STU-2027-105", "沟通中", remark="比价中（虚构）",
                              actor=ACTOR)
        _quote(session, xi.id, smeag, esl, weeks=4, room_type="2人间", start="2027-01-10", status="已发送")
        _quote(session, xi.id, pines, pines_esl, weeks=4, room_type="2人间", start="2027-01-10",
               status="草稿")

        # 保留一个境内研学营（备案展示，无报名）
        ch.create_program(session, {
            "name": "春季曲阜文化研学营（虚构）", "type": "境内研学",
            "departure_date": "2027-04-15", "return_date": "2027-04-17",
            "filing_date": "2027-03-10", "filing_status": "已备案", "status": "筹备中",
            "student_age_group": "中学", "teacher_count": 1, "student_count": 20,
            "insurance": None, "emergency_plan": False,
        }, actor=ACTOR)

        print(
            f"种子完成：机构1、人员{len(STAFF)}、学校{len(SCHOOLS)}、课程"
            f"{sum(len(s['courses']) for s in SCHOOLS)}、学员{len(STUDENTS)}（5条故事线）"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
