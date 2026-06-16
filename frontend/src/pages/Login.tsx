import { useState } from 'react'
import { Button, Input, Card, message, Tabs } from 'antd'
import { UserOutlined, LockOutlined, EyeOutlined, EyeInvisibleOutlined } from '@ant-design/icons'
import { register, login } from '@/api'
import { useGenerationStore } from '@/store/generation'

export default function Login() {
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login')
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    nickname: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const store = useGenerationStore()

  const handleSubmit = async () => {
    if (activeTab === 'login') {
      await handleLogin()
    } else {
      await handleRegister()
    }
  }

  const handleLogin = async () => {
    if (!formData.username || !formData.password) {
      message.warning('请输入用户名和密码')
      return
    }

    setLoading(true)
    try {
      const res = await login(formData.username, formData.password)
      if (res.code === 'success') {
        const token = res.data.token
        const user = res.data.user
        
        // 存储token到localStorage
        localStorage.setItem('token', token)
        localStorage.setItem('user', JSON.stringify(user))
        
        // 更新store
        store.setUserId(user.userId)
        
        message.success('登录成功')
        // 跳转到首页
        window.location.href = '/'
      } else {
        message.error(res.message || '登录失败')
      }
    } catch (e: any) {
      message.error(e.message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!formData.username || !formData.password || !formData.confirmPassword) {
      message.warning('请填写完整信息')
      return
    }

    if (formData.password !== formData.confirmPassword) {
      message.warning('两次输入的密码不一致')
      return
    }

    setLoading(true)
    try {
      const res = await register(formData.username, formData.password, formData.nickname)
      if (res.code === 'success') {
        message.success('注册成功，请登录')
        setActiveTab('login')
        setFormData({ ...formData, password: '', confirmPassword: '' })
      } else {
        message.error(res.message || '注册失败')
      }
    } catch (e: any) {
      message.error(e.message || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card 
        style={{ 
          width: 420, 
          boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
          borderRadius: 16
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div 
            style={{ 
              width: 80, 
              height: 80, 
              margin: '0 auto 16px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 32
            }}
          >
            <UserOutlined />
          </div>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>AIGC 创作平台</h2>
          <p style={{ color: '#999', marginTop: 8 }}>登录后开始您的AI创作之旅</p>
        </div>

        <Tabs 
          activeKey={activeTab} 
          onChange={(key) => setActiveTab(key as 'login' | 'register')}
          style={{ marginBottom: 24 }}
        >
          <Tabs.TabPane tab="登录" key="login" />
          <Tabs.TabPane tab="注册" key="register" />
        </Tabs>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Input
            prefix={<UserOutlined />}
            placeholder="用户名（4-20位字母数字）"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          />

          {activeTab === 'register' && (
            <Input
              prefix={<UserOutlined />}
              placeholder="昵称（可选）"
              value={formData.nickname}
              onChange={(e) => setFormData({ ...formData, nickname: e.target.value })}
            />
          )}

          <Input.Password
            prefix={<LockOutlined />}
            placeholder="密码（8-32位，含大小写字母和数字）"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            iconRender={(visible) => (
              visible ? <EyeOutlined onClick={() => setShowPassword(!showPassword)} /> : <EyeInvisibleOutlined onClick={() => setShowPassword(!showPassword)} />
            )}
          />

          {activeTab === 'register' && (
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="确认密码"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
            />
          )}

          <Button 
            type="primary" 
            size="large" 
            loading={loading}
            onClick={handleSubmit}
            style={{ borderRadius: 8, height: 44 }}
          >
            {activeTab === 'login' ? '登录' : '注册'}
          </Button>
        </div>

        {activeTab === 'login' && (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <a href="#" style={{ color: '#667eea', fontSize: 14 }}>忘记密码？</a>
          </div>
        )}
      </Card>
    </div>
  )
}