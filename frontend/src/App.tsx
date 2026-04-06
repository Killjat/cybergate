import React, { useState, useEffect, useCallback } from 'react';
import { Layout, Button, Table, Modal, Form, Input, Select, message, Tag, Progress, Tabs, Popconfirm, Transfer } from 'antd';
import { PlusOutlined, ThunderboltOutlined, LoadingOutlined, LogoutOutlined, GlobalOutlined, SafetyOutlined, RocketOutlined, TeamOutlined, ApiOutlined } from '@ant-design/icons';
import './App.css';
import axios from 'axios';

const { Header, Content } = Layout;
const { Option } = Select;
const API = (process.env.REACT_APP_API_URL || 'http://localhost:8080') + '/api';

interface Account { id: number; platform: string; username: string; password: string; two_factor_secret?: string; notes?: string; }
interface LoginState { status: 'idle' | 'running' | 'success' | 'failed'; message: string; }
interface CyberUser { id: number; username: string; role: string; account_ids: number[]; }

axios.interceptors.request.use(cfg => {
  const token = localStorage.getItem('cg_token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// ── 首页 Landing Page ────────────────────────────────────────────
function LandingPage({ onEnter }: { onEnter: () => void }) {
  return (
    <div style={{ minHeight: '100vh', background: '#000', color: '#fff', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' }}>
      {/* Nav */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 48px', borderBottom: '1px solid #111' }}>
        <span style={{ fontSize: 20, fontWeight: 700, letterSpacing: 2, color: '#fff' }}>⚡ CYBERGATE</span>
        <Button onClick={onEnter} style={{ background: '#fff', color: '#000', border: 'none', fontWeight: 600, borderRadius: 6 }}>
          进入系统 →
        </Button>
      </div>

      {/* Hero */}
      <div style={{ textAlign: 'center', padding: '100px 48px 80px' }}>
        <div style={{ display: 'inline-block', background: '#111', border: '1px solid #333', borderRadius: 20, padding: '6px 16px', fontSize: 12, color: '#888', marginBottom: 32, letterSpacing: 1 }}>
          AI INTELLIGENCE INFRASTRUCTURE
        </div>
        <h1 style={{ fontSize: 'clamp(40px, 6vw, 80px)', fontWeight: 800, lineHeight: 1.1, margin: '0 0 24px', letterSpacing: -2 }}>
          给每一个 AI Agent<br />
          <span style={{ background: 'linear-gradient(90deg, #4f8ef7, #a855f7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            一个真实的数字身份
          </span>
        </h1>
        <p style={{ fontSize: 18, color: '#888', maxWidth: 600, margin: '0 auto 48px', lineHeight: 1.8 }}>
          互联网上最有价值的情报，藏在登录墙后面。<br />
          CyberGate 让你的情报系统以真实用户身份穿透它。
        </p>
        <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button size="large" onClick={onEnter}
            style={{ background: 'linear-gradient(90deg, #4f8ef7, #a855f7)', border: 'none', color: '#fff', fontWeight: 600, height: 48, padding: '0 32px', borderRadius: 8, fontSize: 16 }}>
            立即使用
          </Button>
          <Button size="large" href="https://github.com/Killjat/cybergate" target="_blank"
            style={{ background: 'transparent', border: '1px solid #333', color: '#fff', height: 48, padding: '0 32px', borderRadius: 8, fontSize: 16 }}>
            GitHub →
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 64, padding: '40px 48px', borderTop: '1px solid #111', borderBottom: '1px solid #111' }}>
        {[['反检测登录', '绕过 Google 风控'], ['Session 持久化', '登录一次永久有效'], ['分布式部署', '一键分发到全球节点'], ['API 优先', '情报系统直接集成']].map(([title, desc]) => (
          <div key={title} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#fff', marginBottom: 4 }}>{title}</div>
            <div style={{ fontSize: 13, color: '#555' }}>{desc}</div>
          </div>
        ))}
      </div>

      {/* Features */}
      <div style={{ maxWidth: 1100, margin: '80px auto', padding: '0 48px' }}>
        <h2 style={{ textAlign: 'center', fontSize: 36, fontWeight: 700, marginBottom: 64, color: '#fff' }}>
          为情报行动而设计
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 24 }}>
          {[
            { icon: <SafetyOutlined style={{ fontSize: 28, color: '#4f8ef7' }} />, title: '反检测登录引擎', desc: '完整模拟人类行为：从空白地址栏输入网址、随机浏览停留、逐字符输入、自然鼠标轨迹。对 Google 风控系统来说，这就是一个普通用户。' },
            { icon: <RocketOutlined style={{ fontSize: 28, color: '#a855f7' }} />, title: '身份即资产', desc: '每个账号对应独立的 Chrome Profile，包含完整的 Cookies、Session、浏览历史。打包传输，在任意机器上 30 秒内复活。' },
            { icon: <TeamOutlined style={{ fontSize: 28, color: '#22c55e' }} />, title: '分布式身份调度', desc: '在一台机器完成登录，将 Profile 分发到全球不同节点。每个 Agent 拿到的是一个活的数字身份，打开即用。' },
            { icon: <ApiOutlined style={{ fontSize: 28, color: '#f59e0b' }} />, title: 'API 优先集成', desc: '情报系统直接调用 REST API 触发登录、获取 Session、下载 Profile。全程自动化，无需人工干预。' },
          ].map(f => (
            <div key={f.title} style={{ background: '#0a0a0a', border: '1px solid #1a1a1a', borderRadius: 12, padding: 28 }}>
              <div style={{ marginBottom: 16 }}>{f.icon}</div>
              <div style={{ fontSize: 17, fontWeight: 600, color: '#fff', marginBottom: 10 }}>{f.title}</div>
              <div style={{ fontSize: 14, color: '#666', lineHeight: 1.7 }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Architecture */}
      <div style={{ maxWidth: 800, margin: '0 auto 80px', padding: '0 48px', textAlign: 'center' }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32, color: '#fff' }}>工作流程</h2>
        <div style={{ background: '#0a0a0a', border: '1px solid #1a1a1a', borderRadius: 12, padding: 32, fontFamily: 'monospace', fontSize: 13, color: '#888', textAlign: 'left', lineHeight: 2 }}>
          <span style={{ color: '#4f8ef7' }}>CyberGate</span> 完成登录 → Session 固化为 Profile<br />
          &nbsp;&nbsp;&nbsp;&nbsp;↓<br />
          Profile 打包分发到 <span style={{ color: '#a855f7' }}>Server-A</span> / <span style={{ color: '#a855f7' }}>Server-B</span> / <span style={{ color: '#a855f7' }}>Server-C</span><br />
          &nbsp;&nbsp;&nbsp;&nbsp;↓<br />
          各节点 <span style={{ color: '#22c55e' }}>AI Agent</span> 以真实身份并发执行情报任务
        </div>
      </div>

      {/* CTA */}
      <div style={{ textAlign: 'center', padding: '80px 48px', borderTop: '1px solid #111' }}>
        <h2 style={{ fontSize: 32, fontWeight: 700, marginBottom: 16, color: '#fff' }}>准备好了吗？</h2>
        <p style={{ color: '#666', marginBottom: 32 }}>注册账号或以游客身份试用</p>
        <Button size="large" onClick={onEnter}
          style={{ background: 'linear-gradient(90deg, #4f8ef7, #a855f7)', border: 'none', color: '#fff', fontWeight: 600, height: 48, padding: '0 48px', borderRadius: 8, fontSize: 16 }}>
          进入 CyberGate →
        </Button>
      </div>

      <div style={{ textAlign: 'center', padding: '24px', color: '#333', fontSize: 12 }}>
        MIT License · Open Source · <a href="https://github.com/Killjat/cybergate" style={{ color: '#444' }}>github.com/Killjat/cybergate</a>
      </div>
    </div>
  );
}

// ── 登录/注册页 ─────────────────────────────────────────────────
function AuthPage({ onLogin }: { onLogin: (token: string, role: string, username: string) => void }) {
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/auth/${tab === 'login' ? 'login' : 'register'}`, values);
      localStorage.setItem('cg_token', res.data.token);
      onLogin(res.data.token, res.data.role, res.data.username);
      message.success(tab === 'login' ? '登录成功' : '注册成功');
    } catch (e: any) {
      message.error(e.response?.data?.detail || '操作失败');
    } finally { setLoading(false); }
  };

  const handleGuest = async () => {
    const res = await axios.get(`${API}/auth/guest-token`);
    localStorage.setItem('cg_token', res.data.token);
    onLogin(res.data.token, 'guest', '游客');
  };

  return (
    <div style={{ minHeight: '100vh', background: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#0a0a0a', border: '1px solid #1a1a1a', borderRadius: 16, padding: '40px 48px', width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 24, fontWeight: 800, color: '#fff', letterSpacing: 2 }}>⚡ CYBERGATE</div>
          <div style={{ fontSize: 13, color: '#555', marginTop: 6 }}>AI 情报身份管理网关</div>
        </div>
        <Tabs activeKey={tab} onChange={k => { setTab(k as any); form.resetFields(); }} centered
          items={[{ key: 'login', label: <span style={{ color: '#888' }}>登录</span> }, { key: 'register', label: <span style={{ color: '#888' }}>注册</span> }]}
          style={{ marginBottom: 24 }} />
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item name="username" rules={[{ required: true }]}>
            <Input placeholder="用户名" size="large"
              style={{ background: '#111', border: '1px solid #222', color: '#fff', borderRadius: 8 }} />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true }]}>
            <Input.Password placeholder="密码" size="large"
              style={{ background: '#111', border: '1px solid #222', color: '#fff', borderRadius: 8 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large" loading={loading}
              style={{ background: 'linear-gradient(90deg, #4f8ef7, #a855f7)', border: 'none', height: 44, borderRadius: 8, fontWeight: 600 }}>
              {tab === 'login' ? '登录' : '注册'}
            </Button>
          </Form.Item>
        </Form>
        <Button type="link" block icon={<GlobalOutlined />} onClick={handleGuest}
          style={{ color: '#444', marginTop: -8 }}>
          游客试用
        </Button>
      </div>
    </div>
  );
}

// ── 主应用 ──────────────────────────────────────────────────────
function MainApp({ currentUser, onLogout }: { currentUser: { username: string; role: string }; onLogout: () => void }) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [loginStates, setLoginStates] = useState<Record<number, LoginState>>({});
  const [browserInstances, setBrowserInstances] = useState<Record<number, string>>({});
  const [totpPreview, setTotpPreview] = useState<{ code: string; valid: boolean; msg: string } | null>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const [users, setUsers] = useState<CyberUser[]>([]);
  const [assignModal, setAssignModal] = useState<CyberUser | null>(null);
  const [assignKeys, setAssignKeys] = useState<string[]>([]);

  const isAdmin = currentUser.role === 'admin';
  const isGuest = currentUser.role === 'guest';

  useEffect(() => { fetchAccounts(); }, []);
  useEffect(() => { if (isAdmin) fetchUsers(); }, [isAdmin]);

  useEffect(() => {
    const handleUnload = () => {
      const ids = Object.values(browserInstances);
      if (!ids.length) return;
      navigator.sendBeacon(`${API}/logout`,
        new Blob([JSON.stringify({ instance_ids: ids })], { type: 'application/json' }));
    };
    window.addEventListener('beforeunload', handleUnload);
    return () => window.removeEventListener('beforeunload', handleUnload);
  }, [browserInstances]);

  const fetchAccounts = async () => {
    try { const res = await axios.get(`${API}/accounts/`); setAccounts(res.data); } catch { message.error('获取账号列表失败'); }
  };
  const fetchUsers = async () => {
    try { const res = await axios.get(`${API}/users/`); setUsers(res.data); } catch { }
  };

  const validateTotp = useCallback(async (secret: string) => {
    if (!secret?.trim()) { setTotpPreview(null); return; }
    try {
      const res = await axios.post(`${API}/validate-totp`, { secret });
      setTotpPreview({ code: res.data.code, valid: true, msg: '' });
    } catch (e: any) {
      setTotpPreview({ code: '', valid: false, msg: e.response?.data?.detail || '无效密钥' });
    }
  }, []);

  const handleAdd = async (values: any) => {
    try { await axios.post(`${API}/accounts/`, values); message.success('添加成功'); setIsModalVisible(false); form.resetFields(); fetchAccounts(); }
    catch (e: any) { message.error(e.response?.data?.detail || '添加失败'); }
  };
  const handleUpdate = async (values: any) => {
    if (!editingAccount) return;
    try { await axios.put(`${API}/accounts/${editingAccount.id}`, values); message.success('更新成功'); setIsEditModalVisible(false); setEditingAccount(null); editForm.resetFields(); fetchAccounts(); }
    catch { message.error('更新失败'); }
  };
  const handleDelete = async (id: number) => {
    try { await axios.delete(`${API}/accounts/${id}`); message.success('已删除'); fetchAccounts(); } catch { message.error('删除失败'); }
  };

  const handleAutoLogin = async (account: Account) => {
    const id = account.id;
    setLoginStates(prev => ({ ...prev, [id]: { status: 'running', message: '启动中...' } }));
    try {
      const res = await axios.post(`${API}/start-auto-login/${id}`);
      const taskId = res.data.task_id;
      const poll = setInterval(async () => {
        try {
          const s = await axios.get(`${API}/login-status/${taskId}`);
          const { status, result, message: msg } = s.data;
          if (status === 'completed') {
            clearInterval(poll);
            if (result?.success) { setLoginStates(prev => ({ ...prev, [id]: { status: 'success', message: result.message } })); message.success(`✓ ${result.message}`); }
            else { setLoginStates(prev => ({ ...prev, [id]: { status: 'failed', message: result?.message || '失败' } })); message.error(result?.message || '登录失败'); }
          } else if (status === 'failed') { clearInterval(poll); setLoginStates(prev => ({ ...prev, [id]: { status: 'failed', message: msg || '失败' } })); }
        } catch { }
      }, 2000);
      setTimeout(() => clearInterval(poll), 180000);
    } catch { setLoginStates(prev => ({ ...prev, [id]: { status: 'failed', message: '启动失败' } })); }
  };

  const handleOpenBrowser = async (account: Account) => {
    try {
      message.loading({ content: '正在打开...', key: `open_${account.id}` });
      const res = await axios.post(`${API}/open-browser/${account.id}`);
      setBrowserInstances(prev => ({ ...prev, [account.id]: res.data.instance_id }));
      message.success({ content: '浏览器已打开', key: `open_${account.id}` });
    } catch (e: any) { message.error({ content: e.response?.data?.detail || '打开失败', key: `open_${account.id}` }); }
  };

  const handleCloseBrowser = async (account: Account) => {
    const instId = browserInstances[account.id];
    if (!instId) return;
    try { await axios.post(`${API}/close-browser/${instId}`); setBrowserInstances(prev => { const n = { ...prev }; delete n[account.id]; return n; }); message.success('已关闭'); }
    catch { message.error('关闭失败'); }
  };

  const loginButton = (account: Account) => {
    if (isGuest) return <Tag>游客模式</Tag>;
    const state = loginStates[account.id];
    if (state?.status === 'running') return <Button size="small" disabled icon={<LoadingOutlined />}>登录中...</Button>;
    if (state?.status === 'success') return <Button size="small" style={{ background: '#52c41a', color: '#fff', border: 'none' }} onClick={() => setLoginStates(prev => ({ ...prev, [account.id]: { status: 'idle', message: '' } }))}>✓ 已登录</Button>;
    return <Button type="primary" size="small" icon={<ThunderboltOutlined />} onClick={() => handleAutoLogin(account)} danger={state?.status === 'failed'}>{state?.status === 'failed' ? '重试' : '自动登录'}</Button>;
  };

  const accountColumns = [
    { title: '平台', dataIndex: 'platform', render: (p: string) => <Tag color={{ google: 'blue', reddit: 'orange' }[p] || 'default'}>{p.toUpperCase()}</Tag> },
    { title: '账号', dataIndex: 'username' },
    { title: '2FA', dataIndex: 'two_factor_secret', render: (v: string) => v ? <Tag color="green">已配置</Tag> : <Tag>未配置</Tag> },
    { title: '备注', dataIndex: 'notes', render: (v: string) => v || '-' },
    { title: '状态', render: (_: any, r: Account) => { const s = loginStates[r.id]; if (!s || s.status === 'idle') return <span style={{ color: '#999' }}>-</span>; if (s.status === 'running') return <Progress percent={99} status="active" size="small" style={{ width: 100 }} />; if (s.status === 'success') return <span style={{ color: '#52c41a' }}>✓ 已登录</span>; return <span style={{ color: '#ff4d4f' }} title={s.message}>✗ 失败</span>; } },
    { title: '操作', render: (_: any, r: Account) => (
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {loginButton(r)}
        {!isGuest && <Button size="small" style={browserInstances[r.id] ? { background: '#fa8c16', color: '#fff', border: 'none' } : {}} onClick={() => browserInstances[r.id] ? handleCloseBrowser(r) : handleOpenBrowser(r)}>{browserInstances[r.id] ? '关闭' : '打开浏览器'}</Button>}
        {isAdmin && <>
          <Button size="small" onClick={() => { setEditingAccount(r); editForm.setFieldsValue({ ...r, password: '' }); setIsEditModalVisible(true); }}>编辑</Button>
          <Button size="small" onClick={async () => {
            try {
              const res = await fetch(`${API}/profiles/${r.id}/export`, { headers: { Authorization: `Bearer ${localStorage.getItem('cg_token')}` } });
              if (!res.ok) { const e = await res.json(); message.error(e.detail || '导出失败'); return; }
              const blob = await res.blob(); const url = URL.createObjectURL(blob);
              const a = document.createElement('a'); a.href = url; a.download = `google_${r.username.split('@')[0].toLowerCase()}.tar.gz`; a.click(); URL.revokeObjectURL(url);
            } catch { message.error('导出失败'); }
          }}>导出</Button>
          <Popconfirm title="确认删除？" onConfirm={() => handleDelete(r.id)}><Button size="small" danger>删除</Button></Popconfirm>
        </>}
      </div>
    )},
  ];

  const userColumns = [
    { title: '用户名', dataIndex: 'username' },
    { title: '角色', dataIndex: 'role', render: (r: string) => <Tag color={r === 'admin' ? 'red' : 'blue'}>{r}</Tag> },
    { title: '可访问账号', dataIndex: 'account_ids', render: (ids: number[]) => ids.length },
    { title: '操作', render: (_: any, r: CyberUser) => (
      <div style={{ display: 'flex', gap: 6 }}>
        <Button size="small" onClick={() => { setAssignModal(r); setAssignKeys(r.account_ids.map(String)); }}>分配账号</Button>
        <Popconfirm title="确认删除用户？" onConfirm={async () => { await axios.delete(`${API}/users/${r.id}`); fetchUsers(); }}><Button size="small" danger>删除</Button></Popconfirm>
      </div>
    )},
  ];

  const accountForm = (onFinish: (v: any) => void, submitText: string, isEdit = false) => (
    <Form form={isEdit ? editForm : form} onFinish={onFinish} layout="vertical">
      <Form.Item name="platform" label="平台" rules={[{ required: true }]}><Select placeholder="选择平台"><Option value="google">Google</Option><Option value="reddit">Reddit</Option><Option value="github">GitHub</Option></Select></Form.Item>
      <Form.Item name="username" label="邮箱 / 用户名" rules={[{ required: true }]}><Input placeholder="example@gmail.com" /></Form.Item>
      <Form.Item name="password" label="密码" rules={isEdit ? [] : [{ required: true }]}><Input.Password placeholder={isEdit ? '留空则不修改' : '请输入密码'} /></Form.Item>
      <Form.Item name="two_factor_secret" label="2FA 密钥" validateStatus={totpPreview ? (totpPreview.valid ? 'success' : 'error') : ''} help={totpPreview ? (totpPreview.valid ? <span style={{ color: '#52c41a' }}>✓ 当前验证码：<b>{totpPreview.code}</b></span> : <span style={{ color: '#ff4d4f' }}>✗ {totpPreview.msg}</span>) : '填入后自动验证'}>
        <Input placeholder="如 eunazvv23kro62etsj5j24tjwinua4ts" onChange={e => { if (!e.target.value.trim()) setTotpPreview(null); }} onBlur={e => validateTotp(e.target.value)} />
      </Form.Item>
      <Form.Item name="notes" label="备注"><Input.TextArea rows={2} /></Form.Item>
      <Form.Item><Button type="primary" htmlType="submit" block>{submitText}</Button></Form.Item>
    </Form>
  );

  const tabItems = [
    { key: 'accounts', label: '账号列表', children: (<>{isAdmin && <div style={{ marginBottom: 16 }}><Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>添加账号</Button></div>}<Table columns={accountColumns} dataSource={accounts} rowKey="id" bordered size="middle" /></>) },
    ...(isAdmin ? [{ key: 'users', label: '用户管理', children: <Table columns={userColumns} dataSource={users} rowKey="id" bordered size="middle" /> }] : [])
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#000', padding: '0 24px', borderBottom: '1px solid #111' }}>
        <span style={{ color: '#fff', fontWeight: 800, fontSize: 16, letterSpacing: 2 }}>⚡ CYBERGATE</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Tag color={currentUser.role === 'admin' ? 'red' : currentUser.role === 'guest' ? 'default' : 'blue'}>{currentUser.username} · {currentUser.role}</Tag>
          <Button size="small" icon={<LogoutOutlined />} onClick={onLogout} ghost>退出</Button>
        </div>
      </Header>
      <Content style={{ padding: '24px 48px' }}>
        <Tabs items={tabItems} />
      </Content>
      <Modal title="添加账号" open={isModalVisible} onCancel={() => { setIsModalVisible(false); form.resetFields(); setTotpPreview(null); }} footer={null}>{accountForm(handleAdd, '添加')}</Modal>
      <Modal title="编辑账号" open={isEditModalVisible} onCancel={() => { setIsEditModalVisible(false); setEditingAccount(null); editForm.resetFields(); setTotpPreview(null); }} footer={null}>{accountForm(handleUpdate, '保存', true)}</Modal>
      <Modal title={`分配账号给 ${assignModal?.username}`} open={!!assignModal} onCancel={() => setAssignModal(null)} onOk={async () => { if (!assignModal) return; await axios.put(`${API}/users/${assignModal.id}/accounts`, { account_ids: assignKeys.map(Number) }); message.success('已保存'); setAssignModal(null); fetchUsers(); }}>
        <Transfer dataSource={accounts.map(a => ({ key: String(a.id), title: `${a.platform} · ${a.username}` }))} targetKeys={assignKeys} onChange={keys => setAssignKeys(keys as string[])} render={item => item.title || ''} titles={['未分配', '已分配']} listStyle={{ width: 200, height: 300 }} />
      </Modal>
    </Layout>
  );
}

// ── 根组件 ──────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState<'landing' | 'auth' | 'app'>('landing');
  const [auth, setAuth] = useState<{ token: string; role: string; username: string } | null>(() => {
    const token = localStorage.getItem('cg_token');
    const role = localStorage.getItem('cg_role');
    const username = localStorage.getItem('cg_username');
    return token && role && username ? { token, role, username } : null;
  });

  const handleLogin = (token: string, role: string, username: string) => {
    localStorage.setItem('cg_token', token);
    localStorage.setItem('cg_role', role);
    localStorage.setItem('cg_username', username);
    setAuth({ token, role, username });
    setPage('app');
  };

  const handleLogout = () => {
    localStorage.removeItem('cg_token');
    localStorage.removeItem('cg_role');
    localStorage.removeItem('cg_username');
    setAuth(null);
    setPage('landing');
  };

  if (auth && page !== 'landing') return <MainApp currentUser={{ username: auth.username, role: auth.role }} onLogout={handleLogout} />;
  if (page === 'auth') return <AuthPage onLogin={handleLogin} />;
  return <LandingPage onEnter={() => { if (auth) { setPage('app'); } else { setPage('auth'); } }} />;
}
