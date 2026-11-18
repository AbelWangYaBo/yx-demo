/* 前端约束：数据严格来自后端接口；字段缺失显示半角「-」；不做防御性兜底。 */
const { createApp, ref, reactive } = Vue;

const STUDENT_STAGES = ['意向', '沟通中', '已报名', '在读', '已毕业'];
const STUDENT_LOST = '已流失';
const ENROLLMENT_STAGES = ['已报名', '材料准备', '已缴费', '已入学', '在读', '已毕业', '已终止'];
const ENROLLMENT_TERMINATED = '已终止';
const REFUND_PRESET_GF = [
  { stage: '未递交材料', ratio: '100' },
  { stage: '已递交未录取', ratio: '70' },
  { stage: '已获录取未递签', ratio: '50' },
  { stage: '已递签', ratio: '20' },
  { stage: '已出签', ratio: '0' },
];
const REFUND_PRESET_PH = [
  { stage: '开课前4周以上取消', ratio: '95' },
  { stage: '开课前2-4周取消', ratio: '70' },
  { stage: '开课前1-2周取消', ratio: '50' },
  { stage: '开课前1周内取消', ratio: '20' },
  { stage: '在读期间（重病等特例）', ratio: '40' },
  { stage: '开除/自行退学', ratio: '0' },
];
// 演示汇率（与后端 DEMO_FX_TO_CNY 一致，静态参考值）
const FX_TO_CNY = { CNY: 1, USD: 7.2, PHP: 0.125 };

// 静态快照回退（GitHub Pages 等无后端场景）：URL → 快照文件映射
const SNAPSHOT_MAP = [
  [/^\/api\/compliance\/overview$/, 'overview.json'],
  [/^\/api\/students\/paged/, 'students.json'],
  [/^\/api\/students\/([^/?]+)\/records$/, 'student-$1.json'],
  [/^\/api\/students$/, 'students-all.json'],
  [/^\/api\/schools$/, 'schools.json'],
  [/^\/api\/courses$/, 'courses.json'],
  [/^\/api\/programs$/, 'programs.json'],
  [/^\/api\/contracts$/, 'contracts.json'],
  [/^\/api\/payments$/, 'payments.json'],
  [/^\/api\/quotations/, 'quotations.json'],
  [/^\/api\/audit\/verify$/, 'audit-verify.json'],
  [/^\/api\/audit/, 'audit.json'],
  [/^\/api\/access-logs/, 'access-logs.json'],
  [/^\/api\/agency$/, 'agency.json'],
  [/^\/api\/meta\/retention$/, 'meta-retention.json'],
];
const STATIC_HINT = '当前为静态演示快照（只读）。完整交互请本地运行：uv run uvicorn app.main:app --port 8120';
function snapshotPath(url) {
  const path = url.split('?')[0];
  for (const [re, file] of SNAPSHOT_MAP) {
    const m = path.match(re);
    if (m) return 'api-snapshot/' + file.replace(/\$(\d)/g, (_, i) => m[Number(i)]);
  }
  return null;
}

const app = createApp({
  setup() {
    // ===== 导航 =====
    const tabs = [
      { key: 'overview', label: '合规总览' },
      { key: 'students', label: '学员' },
      { key: 'schools', label: '学校与课程' },
      { key: 'programs', label: '活动与行程' },
      { key: 'finance', label: '合同与缴费' },
      { key: 'audit', label: '审计与访问' },
      { key: 'agency', label: '机构信息' },
    ];
    const page = ref('overview');

    // ===== 数据 =====
    const overview = ref(null);
    const agency = ref(null);
    const studentPage = ref(null);
    const stuKeyword = ref('');
    const studentNo = ref(null);
    const detailTab = ref('summary');
    const records = ref(null);
    const accessLogs = ref([]);
    const programs = ref([]);
    const contracts = ref([]);
    const payments = ref([]);
    const allStudents = ref([]);
    const finTab = ref('contracts');
    const auditLogs = ref([]);
    const auditTab = ref('audit');
    const verifyResult = ref(null);
    const drawerLog = ref(null);
    const schoolStore = ref([]);
    const courseStore = ref([]);

    const detailTabs = [
      { key: 'summary', label: '概要' },
      { key: 'quotations', label: '报价单' },
      { key: 'enrollments', label: '报名与推进' },
      { key: 'reports', label: '在读周报' },
      { key: 'documents', label: '证件材料' },
      { key: 'communications', label: '沟通记录' },
      { key: 'consents', label: '同意书' },
      { key: 'contracts', label: '合同缴费' },
      { key: 'timeline', label: '服务时间线' },
      { key: 'access', label: '访问记录' },
    ];

    // ===== 表单状态 =====
    const newStudent = reactive({ student_no: '', name: '', birth_date: '', guardian_name: '', guardian_phone: '' });
    const newConsent = reactive({ consent_type: '敏感信息处理', signer_name: '', relation: '', individual_consent: true });
    const consentScope = ref(null);
    const newProgram = reactive({
      name: '', type: '境内研学', departure_date: '', return_date: '',
      filing_date: '', filing_status: '已备案', teacher_count: 1, student_count: 0,
      partner_school: '', school_verified: false,
      school_id: null, course_id: null, weeks: null, room_type: '',
    });
    const newDocument = reactive({ doc_type: '护照', doc_no: '', issued_date: '', expiry_date: '', file_ref: '', remark: '' });
    const pickedFile = ref(null);
    const newCommunication = reactive({ channel: '电话', direction: '呼出', occurred_at: '', operator: '', summary: '' });
    const newEnrollment = reactive({
      mode: 'group', program_id: null, course_name: '', accommodation: '', pickup_arranged: false,
      expected_start: '', health_proof: false, parent_notice_signed: false,
      school_id: null, course_id: null, weeks: null, room_type: '', start_date: '',
    });
    const newContract = reactive({ student_id: null, contract_no: '', total_fee: '', currency: 'USD', signed_date: '' });
    const contractScopeText = ref('选校咨询,代办报名,签证指导,行前服务');
    const refundPreset = ref('ph');
    const newPayment = reactive({ contract_id: null, type: '定金', amount: '', currency: 'CNY', voucher_no: '', payee: '', proof_file: '' });
    const stageCtx = reactive({ kind: 'student', id: null, no: null, current: '', target: '', options: [], remark: '' });
    const refundStage = reactive({});
    const refundResult = reactive({});
    const newSchool = reactive({
      name: '', region: '宿务', style: '半斯巴达', commission_rate: '20',
      registration_fee_usd: '100', cooperation_agreement: '', verified: false, notes: '',
    });
    const newCourse = reactive({ school_id: null, name: '', course_type: 'ESL', lessons: '', min_weeks: 4, r4: null, r3: null, r2: null, r1: null, guarantee: '' });
    const newQuote = reactive({ school_id: null, course_id: null, weeks: null, room_type: '', start_date: '' });
    const quotePreview = ref(null);
    const newReport = reactive({ enrollment_id: null, week_no: 0, level: '', test_score: '', attendance_pct: null, teacher_comment: '', parent_notified_at: '' });

    // ===== 表单弹窗框架 =====
    const formModal = reactive({ show: false, kind: '', title: '', err: '', fixedStudent: null });
    function openForm(kind, title) {
      formModal.show = true;
      formModal.kind = kind;
      formModal.title = title;
      formModal.err = '';
      formModal.fixedStudent = null;
    }
    function closeForm() {
      formModal.show = false;
      formModal.err = '';
      quotePreview.value = null;
    }

    // ===== 二次确认 =====
    const confirmBox = reactive({ show: false, text: '', onOk: null });
    function askConfirm(text, onOk) {
      confirmBox.show = true;
      confirmBox.text = text;
      confirmBox.onOk = onOk;
    }
    function doConfirm() {
      const fn = confirmBox.onOk;
      closeConfirm();
      if (fn) fn();
    }
    function closeConfirm() {
      confirmBox.show = false;
      confirmBox.onOk = null;
    }

    // ===== 展示工具 =====
    const dash = (v) => (v === null || v === undefined || v === '' ? '-' : v);
    const fmtTime = (v) => (v ? String(v).replace('T', ' ') : '-');
    const currencyMark = (c) => (c === 'USD' ? '$' : c === 'PHP' ? '₱' : '¥');
    const fxToCny = (amount, currency) => {
      const rate = FX_TO_CNY[currency];
      if (!rate || amount === null || amount === undefined || amount === '') return '-';
      return (parseFloat(amount) * rate).toFixed(2).replace(/\.00$/, '');
    };
    function goFollowUp(f) {
      if (f && f.student_no) openStudent(f.student_no);
    }
    const ACTION_LABELS = { create: '新增', update: '变更', revoke: '撤回', stage: '阶段推进', confirm: '确认转报名', void: '作废' };
    const ENTITY_LABELS = {
      agency: '机构档案', staff: '备案人员', student: '学员', consent: '同意书',
      program: '项目', enrollment: '报名', contract: '合同', payment: '缴费',
      service_event: '服务节点', document: '证件材料', communication: '沟通记录',
      attachment: '附件', school: '学校', course: '课程',
      quotation: '报价单', weekly_report: '在读周报',
    };
    const ACCESS_LABELS = { VIEW_STUDENT: '查看学员信息', DOWNLOAD_FILE: '下载附件' };
    const actionLabel = (l) => ACTION_LABELS[l.action] || l.action;
    const entityLabel = (e) => ENTITY_LABELS[e] || e;
    const accessLabel = (t) => ACCESS_LABELS[t] || t;

    const STAGE_CLASSES = {
      意向: 'warning', 沟通中: 'warning', 已流失: 'error',
      材料准备: 'warning', 已终止: 'error',
    };
    const stageClass = (s) => STAGE_CLASSES[s] || 'ok';

    function brief(l) {
      const p = l.payload || {};
      if (l.action === 'update' && p.before && p.after) {
        return Object.keys(p.after)
          .map((k) => `${k}: ${JSON.stringify(p.before[k])} → ${JSON.stringify(p.after[k])}`)
          .join('；');
      }
      if (l.action === 'stage' || l.action === 'confirm' || l.action === 'void') return `${p.before || ''} → ${p.after || p.status || ''}`;
      if (l.entity === 'student') return `${p.name || ''}（${p.student_no || l.entity_id}）`;
      if (l.entity === 'document') return `${p.doc_type || ''} ${p.doc_no || ''}`;
      if (l.entity === 'communication') return `${p.channel || ''} ${p.direction || ''} ${p.summary || ''}`;
      if (l.entity === 'attachment') return p.filename || '';
      if (l.entity === 'consent' && l.action === 'revoke') return '同意书撤回（不可逆）';
      if (l.entity === 'school') return `${p.name || ''}（${p.region || ''}·${p.style || ''}）`;
      if (l.entity === 'course') return `${p.name || ''}（最短${p.min_weeks || '?'}周）`;
      if (l.entity === 'quotation') return `${l.entity_id}（${(p.items || []).length} 项明细，合计 ${p.total_usd || '?'} USD）`;
      if (l.entity === 'weekly_report') return `第 ${p.week_no ?? '?'} 周（${p.level || ''}）`;
      return JSON.stringify(p);
    }

    function diffText(l) {
      const p = l.payload || {};
      if (p.before && p.after) {
        return Object.keys(p.after)
          .map((k) => `${k}: ${JSON.stringify(p.before[k])} → ${JSON.stringify(p.after[k])}`)
          .join('\n');
      }
      return '（非变更操作，无前后对照）';
    }

    function isPassportShort(d) {
      if (!d.expiry_date) return false;
      const limit = new Date();
      limit.setMonth(limit.getMonth() + 6);
      return new Date(d.expiry_date) < limit;
    }

    function isMinorByBirth(birth) {
      if (!birth) return false;
      const b = new Date(birth);
      const now = new Date();
      const age = now.getFullYear() - b.getFullYear()
        - ((now.getMonth() + 1) < (b.getMonth() + 1)
          || ((now.getMonth() + 1) === (b.getMonth() + 1) && now.getDate() < b.getDate()) ? 1 : 0);
      return age < 18;
    }

    // 学员详情：材料存在性（菲律宾行政链徽标）
    function hasDocType(docType) {
      return (records.value?.documents || []).some((d) => d.doc_type === docType);
    }
    function hasWegProof() {
      return hasDocType('WEG') || hasDocType('监护同行证明');
    }

    // ===== 静态快照只读模式（GitHub Pages 等无后端场景）=====
    const staticMode = ref(false);
    async function _loadSnapshot(url) {
      const path = snapshotPath(url);
      if (!path) return null;
      const s = await fetch(path);
      if (!s.ok) return null;
      staticMode.value = true;
      return s.json();
    }

    async function api(url, opts = {}) {
      if (staticMode.value && opts.method && opts.method !== 'GET') {
        throw new Error(STATIC_HINT);
      }
      let r;
      try {
        r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
      } catch (e) {
        // 网络不可达（Pages 上无后端）→ 尝试静态快照
        const snap = await _loadSnapshot(url);
        if (snap !== null) return snap;
        throw e;
      }
      if (r.ok) return r.status === 204 ? null : r.json();
      // 后端返回 404：本机未起后端（如静态托管）时回退快照；正常后端的业务 404 照常抛
      if (r.status === 404) {
        const snap = await _loadSnapshot(url);
        if (snap !== null) return snap;
      }
      const body = await r.json().catch(() => ({}));
      throw new Error(body.detail && typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail || r.status));
    }

    // ===== 页面路由 =====
    async function go(key) {
      page.value = key;
      studentNo.value = null;
      records.value = null;
      drawerLog.value = null;
      if (key === 'overview') overview.value = await api('/api/compliance/overview');
      if (key === 'students') { stuKeyword.value = ''; await loadStudentList(1); }
      if (key === 'schools') await loadSchools();
      if (key === 'programs') {
        programs.value = await api('/api/programs');
        if (!schoolStore.value.length) await loadSchools();
      }
      if (key === 'finance') await loadFinance();
      if (key === 'audit') await loadAuditTab('audit');
      if (key === 'agency') agency.value = await api('/api/agency');
    }

    async function loadSchools() {
      schoolStore.value = await api('/api/schools');
      courseStore.value = await api('/api/courses');
    }
    const schoolName = (id) => {
      const s = schoolStore.value.find((x) => x.id === id);
      return s ? s.name : id;
    };
    const coursesOfSchool = (schoolId) => courseStore.value.filter((c) => c.school_id === schoolId);
    const roomsOfCourse = (courseId) => {
      const c = courseStore.value.find((x) => x.id === courseId);
      return c ? c.room_prices : {};
    };

    async function loadFinance() {
      contracts.value = await api('/api/contracts');
      payments.value = await api('/api/payments');
      allStudents.value = await api('/api/students');
    }

    const studentName = (id) => {
      const s = allStudents.value.find((x) => x.id === id);
      return s ? s.name : id;
    };
    const contractNo = (id) => {
      const c = contracts.value.find((x) => x.id === id);
      return c ? c.contract_no : id;
    };

    // ===== 学员列表/详情 =====
    async function loadStudentList(p = 1) {
      const kw = stuKeyword.value.trim();
      const url = `/api/students/paged?page=${p}&size=20${kw ? `&keyword=${encodeURIComponent(kw)}` : ''}`;
      studentPage.value = await api(url);
    }

    async function openStudent(no) {
      studentNo.value = no;
      detailTab.value = 'summary';
      records.value = await api(`/api/students/${no}/records`);  // 后端写访问记录
    }

    function closeStudent() {
      studentNo.value = null;
      records.value = null;
      loadStudentList(studentPage.value ? studentPage.value.page : 1);
    }

    function switchDetailTab(key) {
      detailTab.value = key;
      if (key === 'access') {
        api(`/api/access-logs?student_no=${studentNo.value}`).then((d) => { accessLogs.value = d; });
      }
    }

    // ===== 学员生命周期阶段 =====
    function studentStageNext() {
      const cur = records.value.student.stage;
      const idx = STUDENT_STAGES.indexOf(cur);
      const out = idx >= 0 ? STUDENT_STAGES.slice(idx + 1) : [];
      if (cur !== STUDENT_LOST && cur !== '已毕业') out.push(STUDENT_LOST);
      return out;
    }

    function openStageForm(kind, enrollment) {
      let current; let options;
      if (kind === 'student') {
        current = records.value.student.stage;
        options = studentStageNext();
      } else {
        current = enrollment.stage;
        const idx = ENROLLMENT_STAGES.indexOf(current);
        options = idx >= 0 ? ENROLLMENT_STAGES.slice(idx + 1) : [];
        if (current !== ENROLLMENT_TERMINATED && current !== '已毕业') options.push(ENROLLMENT_TERMINATED);
      }
      if (!options.length) return;
      stageCtx.kind = kind;
      stageCtx.current = current;
      stageCtx.options = options;
      stageCtx.target = options[0];
      stageCtx.remark = '';
      stageCtx.id = kind === 'enrollment' ? enrollment.id : null;
      stageCtx.no = kind === 'student' ? records.value.student.student_no : null;
      openForm('stage', kind === 'student' ? '推进学员阶段' : '推进报名阶段');
    }

    async function submitStage() {
      try {
        if (stageCtx.kind === 'student') {
          await api(`/api/students/${stageCtx.no}/stage`, {
            method: 'POST',
            body: JSON.stringify({ stage: stageCtx.target, remark: stageCtx.remark || null }),
          });
          records.value = await api(`/api/students/${stageCtx.no}/records`);
        } else {
          await api(`/api/enrollments/${stageCtx.id}/stage`, {
            method: 'POST',
            body: JSON.stringify({ stage: stageCtx.target, remark: stageCtx.remark || null }),
          });
          records.value = await api(`/api/students/${studentNo.value}/records`);
        }
        closeForm();
      } catch (e) {
        formModal.err = e.message;
      }
    }

    // ===== 各表单提交 =====
    function submitStudent() {
      api('/api/students', { method: 'POST', body: JSON.stringify(newStudent) })
        .then(() => { closeForm(); loadStudentList(1); })
        .catch((e) => { formModal.err = e.message; });
    }

    function submitProgram() {
      const payload = { ...newProgram, filing_date: newProgram.filing_date || null };
      api('/api/programs', { method: 'POST', body: JSON.stringify(payload) })
        .then(async () => { closeForm(); programs.value = await api('/api/programs'); })
        .catch((e) => { formModal.err = `合规校验未通过：${e.message}`; });
    }

    // 语言研修计划表单联动
    async function onProgramSchoolChange() {
      newProgram.course_id = null;
      newProgram.room_type = '';
    }
    function onProgramCourseChange() {
      const rooms = Object.keys(roomsOfCourse(newProgram.course_id));
      newProgram.room_type = rooms[0] || '';
      const course = courseStore.value.find((c) => c.id === newProgram.course_id);
      if (course && (!newProgram.weeks || newProgram.weeks < course.min_weeks)) newProgram.weeks = course.min_weeks;
    }
    function onProgramStartChange() { /* 离校日期为只读展示 */ }
    function calcReturnDate() {
      if (!newProgram.departure_date || !newProgram.weeks) return '';
      const d = new Date(newProgram.departure_date);
      d.setDate(d.getDate() + newProgram.weeks * 7 - 1);
      return d.toISOString().slice(0, 10);
    }

    function submitSchool() {
      api('/api/schools', { method: 'POST', body: JSON.stringify(newSchool) })
        .then(async () => { closeForm(); await loadSchools(); })
        .catch((e) => { formModal.err = e.message; });
    }

    function openCourseCreate() {
      newCourse.school_id = schoolStore.value.length ? schoolStore.value[0].id : null;
      openForm('course', '新增课程价目');
    }
    function onCourseFormSchoolChange() { /* 学校切换仅影响展示 */ }
    function submitCourse() {
      const roomPrices = {};
      if (newCourse.r4) roomPrices['4人间'] = newCourse.r4;
      if (newCourse.r3) roomPrices['3人间'] = newCourse.r3;
      if (newCourse.r2) roomPrices['2人间'] = newCourse.r2;
      if (newCourse.r1) roomPrices['1人间'] = newCourse.r1;
      const payload = {
        school_id: newCourse.school_id, name: newCourse.name, course_type: newCourse.course_type,
        lessons: newCourse.lessons || null, min_weeks: newCourse.min_weeks,
        room_prices: roomPrices, guarantee: newCourse.guarantee || null,
      };
      api('/api/courses', { method: 'POST', body: JSON.stringify(payload) })
        .then(async () => { closeForm(); await loadSchools(); })
        .catch((e) => { formModal.err = e.message; });
    }

    // ===== 报价单 =====
    async function openQuoteCreate() {
      if (!schoolStore.value.length) await loadSchools();
      newQuote.school_id = null;
      newQuote.course_id = null;
      newQuote.weeks = null;
      newQuote.room_type = '';
      newQuote.start_date = '';
      quotePreview.value = null;
      openForm('quotation', `新建报价单（${records.value.student.name}）`);
    }
    function onQuoteSchoolChange() {
      newQuote.course_id = null;
      newQuote.room_type = '';
      quotePreview.value = null;
    }
    function onQuoteCourseChange() {
      const rooms = Object.keys(roomsOfCourse(newQuote.course_id));
      newQuote.room_type = rooms[0] || '';
      const course = courseStore.value.find((c) => c.id === newQuote.course_id);
      if (course) newQuote.weeks = course.min_weeks;
      refreshQuotePreview();
    }
    async function refreshQuotePreview() {
      if (!newQuote.school_id || !newQuote.course_id || !newQuote.weeks || !newQuote.room_type) return;
      try {
        quotePreview.value = await api('/api/quotations/preview', {
          method: 'POST',
          body: JSON.stringify({
            school_id: newQuote.school_id, course_id: newQuote.course_id,
            weeks: newQuote.weeks, room_type: newQuote.room_type,
          }),
        });
      } catch (e) {
        quotePreview.value = null;
        formModal.err = e.message;
      }
    }
    function submitQuotation() {
      const payload = {
        student_id: records.value.student.id,
        school_id: newQuote.school_id, course_id: newQuote.course_id,
        weeks: newQuote.weeks, room_type: newQuote.room_type,
        start_date: newQuote.start_date, status: '草稿',
      };
      api('/api/quotations', { method: 'POST', body: JSON.stringify(payload) })
        .then(async () => {
          closeForm();
          records.value = await api(`/api/students/${studentNo.value}/records`);
        })
        .catch((e) => { formModal.err = e.message; });
    }
    async function sendQuote(q) {
      // 系统不提供修改接口（追加写）：发送 = 作废当前草稿 + 生成同方案「已发送」新单
      askConfirm(`将报价单 ${q.quote_no} 标记为「已发送」？（追加写：作废当前单并生成同方案「已发送」新单）`, async () => {
        try {
          await api(`/api/quotations/${q.id}/void`, { method: 'POST' });
          await api('/api/quotations', {
            method: 'POST',
            body: JSON.stringify({
              student_id: records.value.student.id, school_id: q.school_id,
              course_id: q.course_id, weeks: q.weeks, room_type: q.room_type,
              start_date: q.start_date, status: '已发送',
            }),
          });
          records.value = await api(`/api/students/${studentNo.value}/records`);
        } catch (e) {
          alert(e.message);
        }
      });
    }
    function askConfirmQuote(q) {
      askConfirm(`确认报价单 ${q.quote_no} 并生成报名？（将创建语言研修计划 + 报名记录，全部合规校验生效，操作不可逆）`, async () => {
        try {
          await api(`/api/quotations/${q.id}/confirm`, { method: 'POST' });
          records.value = await api(`/api/students/${studentNo.value}/records`);
        } catch (e) {
          formModal.err = e.message;
        }
      });
    }
    async function voidQuote(q) {
      try {
        await api(`/api/quotations/${q.id}/void`, { method: 'POST' });
        records.value = await api(`/api/students/${studentNo.value}/records`);
      } catch (e) {
        alert(e.message);
      }
    }

    // ===== 在读周报 =====
    function openReportCreate() {
      newReport.enrollment_id = records.value.enrollments.length ? records.value.enrollments[0].id : null;
      newReport.week_no = 0;
      newReport.level = '';
      newReport.test_score = '';
      newReport.attendance_pct = null;
      newReport.teacher_comment = '';
      newReport.parent_notified_at = '';
      openForm('report', '录入周报/分班测试');
    }
    function submitReport() {
      const payload = {
        enrollment_id: newReport.enrollment_id, week_no: newReport.week_no,
        level: newReport.level || null, test_score: newReport.test_score || null,
        attendance_pct: newReport.attendance_pct, teacher_comment: newReport.teacher_comment || null,
        parent_notified_at: newReport.parent_notified_at
          ? newReport.parent_notified_at.replace('T', ' ') + ':00' : null,
      };
      api('/api/weekly-reports', { method: 'POST', body: JSON.stringify(payload) })
        .then(async () => {
          closeForm();
          records.value = await api(`/api/students/${studentNo.value}/records`);
        })
        .catch((e) => { formModal.err = e.message; });
    }

    function openEnrollmentCreate() {
      newEnrollment.mode = 'group';
      newEnrollment.program_id = null;
      newEnrollment.school_id = null;
      newEnrollment.course_id = null;
      newEnrollment.weeks = null;
      newEnrollment.room_type = '';
      newEnrollment.start_date = '';
      openForm('enrollment', '新增报名');
      api('/api/programs').then((d) => { programs.value = d; });
      if (!schoolStore.value.length) loadSchools();
    }
    function onEnrSchoolChange() {
      newEnrollment.course_id = null;
      newEnrollment.room_type = '';
    }
    function onEnrCourseChange() {
      const rooms = Object.keys(roomsOfCourse(newEnrollment.course_id));
      newEnrollment.room_type = rooms[0] || '';
      const course = courseStore.value.find((c) => c.id === newEnrollment.course_id);
      if (course) newEnrollment.weeks = course.min_weeks;
    }

    function submitEnrollment() {
      const stu = records.value.student;
      let payload;
      if (newEnrollment.mode === 'group') {
        payload = {
          student_id: stu.id, program_id: newEnrollment.program_id,
          course_name: newEnrollment.course_name || null,
          accommodation: newEnrollment.accommodation || null,
          pickup_arranged: newEnrollment.pickup_arranged,
          health_proof: newEnrollment.health_proof,
          parent_notice_signed: newEnrollment.parent_notice_signed,
          expected_start: newEnrollment.expected_start || null,
        };
      } else {
        payload = {
          student_id: stu.id,
          school_id: newEnrollment.school_id, course_id: newEnrollment.course_id,
          weeks: newEnrollment.weeks, room_type: newEnrollment.room_type,
          start_date: newEnrollment.start_date || null,
          pickup_arranged: newEnrollment.pickup_arranged,
          health_proof: newEnrollment.health_proof,
          parent_notice_signed: newEnrollment.parent_notice_signed,
        };
      }
      api('/api/enrollments', { method: 'POST', body: JSON.stringify(payload) })
        .then(async () => {
          closeForm();
          records.value = await api(`/api/students/${studentNo.value}/records`);
        })
        .catch((e) => { formModal.err = e.message; });
    }

    function onFilePick(ev) {
      pickedFile.value = ev.target.files[0] || null;
    }

    function submitDocument() {
      const stu = records.value.student;
      const run = async () => {
        const payload = { student_id: stu.id, ...newDocument };
        payload.issued_date = payload.issued_date || null;
        payload.expiry_date = payload.expiry_date || null;
        if (pickedFile.value) {
          const fd = new FormData();
          fd.append('file', pickedFile.value);
          const up = await fetch('/api/attachments', { method: 'POST', body: fd });
          if (!up.ok) throw new Error(`附件上传失败（${up.status}）`);
          payload.attachment_id = (await up.json()).id;
        }
        await api('/api/documents', { method: 'POST', body: JSON.stringify(payload) });
        pickedFile.value = null;
        records.value = await api(`/api/students/${studentNo.value}/records`);
        closeForm();
      };
      run().catch((e) => { formModal.err = e.message; });
    }

    function submitCommunication() {
      const payload = {
        student_id: records.value.student.id,
        ...newCommunication,
        occurred_at: newCommunication.occurred_at.replace('T', ' ') + ':00',
      };
      api('/api/communications', { method: 'POST', body: JSON.stringify(payload) })
        .then(async () => {
          closeForm();
          records.value = await api(`/api/students/${studentNo.value}/records`);
        })
        .catch((e) => { formModal.err = e.message; });
    }

    async function openConsentCreate() {
      if (!programs.value.length) programs.value = await api('/api/programs');
      consentScope.value = null;
      newConsent.consent_type = '敏感信息处理';
      newConsent.signer_name = records.value.student.guardian_name || '';
      newConsent.relation = '';
      newConsent.individual_consent = true;
      openForm('consent', '签署同意书');
    }

    function submitConsent() {
      const stu = records.value.student;
      api('/api/consents', {
        method: 'POST',
        body: JSON.stringify({ student_id: stu.id, program_id: consentScope.value, ...newConsent }),
      })
        .then(async () => {
          closeForm();
          records.value = await api(`/api/students/${studentNo.value}/records`);
        })
        .catch((e) => { formModal.err = e.message; });
    }

    function askRevokeConsent(c) {
      askConfirm(`确认撤回学员「${records.value.student.name}」的「${c.consent_type}」同意书？撤回后该学员报名将被拦截，操作不可逆。`, async () => {
        await api(`/api/consents/${c.id}/revoke`, { method: 'POST' });
        records.value = await api(`/api/students/${studentNo.value}/records`);
      });
    }

    function openContractCreate(fixedStudent) {
      newContract.student_id = fixedStudent ? fixedStudent.id : null;
      newContract.contract_no = '';
      newContract.total_fee = '';
      newContract.currency = 'USD';
      newContract.signed_date = '';
      contractScopeText.value = '选校咨询,代办报名,签证指导,行前服务';
      refundPreset.value = 'ph';
      if (!fixedStudent) api('/api/students').then((d) => { allStudents.value = d; });
      openForm('contract', '新增合同');
      formModal.fixedStudent = fixedStudent || null;
    }

    function submitContract() {
      const payload = {
        ...newContract,
        service_scope: contractScopeText.value.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
        signed_date: newContract.signed_date,
        refund_rules: refundPreset.value === 'ph' ? REFUND_PRESET_PH : REFUND_PRESET_GF,
        status: '履行中',
      };
      api('/api/contracts', { method: 'POST', body: JSON.stringify(payload) })
        .then(async () => {
          closeForm();
          contracts.value = await api('/api/contracts');
          if (studentNo.value) records.value = await api(`/api/students/${studentNo.value}/records`);
        })
        .catch((e) => { formModal.err = e.message; });
    }

    function openPaymentCreate() {
      if (!contracts.value.length) {
        loadFinance().then(() => { openForm('payment', '登记缴费'); });
      } else {
        openForm('payment', '登记缴费');
      }
      newPayment.contract_id = contracts.value.length ? contracts.value[0].id : null;
      newPayment.currency = 'CNY';
    }

    function submitPayment() {
      api('/api/payments', { method: 'POST', body: JSON.stringify(newPayment) })
        .then(async () => {
          closeForm();
          payments.value = await api('/api/payments');
          if (studentNo.value) records.value = await api(`/api/students/${studentNo.value}/records`);
        })
        .catch((e) => { formModal.err = e.message; });
    }

    async function quoteRefund(id, stage) {
      const out = await api(`/api/contracts/${id}/refund-quote`, {
        method: 'POST', body: JSON.stringify({ stage }),
      });
      refundResult[id] = out.refund_amount;
    }

    // ===== 审计与访问 =====
    async function loadAuditTab(tabKey) {
      auditTab.value = tabKey;
      drawerLog.value = null;
      verifyResult.value = null;
      if (tabKey === 'audit') {
        auditLogs.value = (await api('/api/audit?limit=200')).items;
      } else {
        accessLogs.value = await api('/api/access-logs?limit=200');
      }
    }

    async function verifyAudit() {
      verifyResult.value = await api('/api/audit/verify');
    }

    go('overview');

    return {
      tabs, page, go, staticMode, STATIC_HINT,
      overview, agency,
      studentPage, stuKeyword, loadStudentList, studentNo, detailTabs, detailTab,
      records, accessLogs, openStudent, closeStudent, switchDetailTab,
      programs, contracts, payments, allStudents, finTab, studentName, contractNo,
      auditLogs, auditTab, loadAuditTab, verifyResult, drawerLog,
      schoolStore, courseStore, schoolName, coursesOfSchool, roomsOfCourse,
      newStudent, newConsent, consentScope, newProgram, newDocument, pickedFile, onFilePick,
      newCommunication, newEnrollment, newContract, contractScopeText, refundPreset, newPayment,
      newSchool, newCourse, newQuote, quotePreview, newReport,
      stageCtx, refundStage, refundResult,
      formModal, openForm, closeForm, openEnrollmentCreate, openContractCreate, openPaymentCreate,
      openCourseCreate, openQuoteCreate, openReportCreate,
      onProgramSchoolChange, onProgramCourseChange, onProgramStartChange, calcReturnDate,
      onEnrSchoolChange, onEnrCourseChange,
      onQuoteSchoolChange, onQuoteCourseChange, refreshQuotePreview,
      onCourseFormSchoolChange,
      sendQuote, askConfirmQuote, voidQuote,
      openStageForm, submitStage, studentStageNext,
      confirmBox, askConfirm, doConfirm, closeConfirm, askRevokeConsent, openConsentCreate,
      dash, fmtTime, currencyMark, fxToCny, goFollowUp, actionLabel, entityLabel, accessLabel, brief, diffText,
      isPassportShort, isMinorByBirth, stageClass, hasDocType, hasWegProof,
      submitStudent, submitProgram, submitSchool, submitCourse, submitQuotation, submitReport,
      submitEnrollment, submitDocument,
      submitCommunication, submitConsent, submitContract, submitPayment,
      quoteRefund, verifyAudit,
    };
  },
});
app.mount('#app');
