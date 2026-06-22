import { useCallback, useEffect, useState } from 'react'
import {
  Alert,
  Button,
  Descriptions,
  Drawer,
  Form,
  Input,
  Modal,
  Popconfirm,
  Radio,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Timeline,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  CodeOutlined,
  EditOutlined,
  EyeOutlined,
  FileMarkdownOutlined,
  PlusOutlined,
  ReloadOutlined,
  RollbackOutlined,
  SendOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import {
  compareSkillBeforePublish,
  createDramaSkillAdmin,
  deleteDramaSkillAdmin,
  getDramaSkillAdmin,
  importRepoSkillAdmin,
  listDramaSkillsAdmin,
  listRepoSkillFolders,
  listSkillVersionsAdmin,
  previewRepoSkill,
  publishDramaSkillAdmin,
  rollbackSkillAdmin,
  updateDramaSkillAdmin,
} from '@/api/drama'
import MarkdownEditor from '@/components/knowledge/MarkdownEditor'
import SkillSideBySideDiff from '@/components/SkillSideBySideDiff'
import { buildSkillContentTemplate } from '@/constants/skillTemplate'
import type { DramaSkill, RepoSkillPreview, SkillPublishCompare, SkillRepoSyncResult } from '@/types/drama'

function showRepoSyncFeedback(
  data: (DramaSkill & SkillRepoSyncResult) | undefined,
  mode: 'import' | 'reimport',
) {
  if (!data) return
  if (data.action === 'published') {
    message.success(`已发布 ${data.skill_code} v${data.repo_version || data.version || ''}`)
    return
  }
  if (data.action === 'already_published') {
    message.info(
      `代码库 v${data.repo_version || '-'} 与线上 v${data.published_version || data.version || '-'} 均已是最新`,
    )
    return
  }
  if (data.unchanged && data.needs_publish) {
    message.warning(
      `代码库 v${data.repo_version || '-'} 已同步到草稿，但线上仍是 v${data.published_version || '旧版'}。请点击「发布」上线。`,
      6,
    )
    return
  }
  if (data.unchanged) {
    message.info(`代码库内容与当前草稿一致，无需重复拉取（v${data.repo_version || data.version || '-'}）`)
    return
  }
  message.success(mode === 'import' ? '已从代码库拉取到草稿' : '已从代码库拉取到草稿')
}

const STAGE_OPTIONS = [
  { value: 'init', label: '立项 init' },
  { value: 'concept', label: '创意 concept' },
  { value: 'outline', label: '大纲 outline' },
  { value: 'script', label: '剧本 script' },
  { value: 'character', label: '角色 character' },
  { value: 'scene', label: '场景 scene' },
  { value: 'storyboard', label: '分镜 storyboard' },
  { value: 'production', label: '生产 production' },
]

type CreateMode = 'online' | 'repo'

/** 内置 skill_code → skills/ 子目录（repo_path 为空时兜底） */
const REPO_FOLDER_BY_CODE: Record<string, string> = {
  'skill.intake': 'skill_intake',
  'skill.concept': 'skill_concept',
  'skill.character': 'skill_character',
  'skill.scene': 'skill_scene',
  'skill.storyboard': 'skill_storyboard',
  'skill.production': 'skill_production',
}

function resolveRepoFolder(row: DramaSkill): string | undefined {
  return row.repo_path || REPO_FOLDER_BY_CODE[row.skill_code]
}

export default function SkillAdminPage() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<DramaSkill[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [createModeOpen, setCreateModeOpen] = useState(false)
  const [createMode, setCreateMode] = useState<CreateMode>('online')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [repoOpen, setRepoOpen] = useState(false)
  const [repoFolders, setRepoFolders] = useState<string[]>([])
  const [selectedFolder, setSelectedFolder] = useState<string>()
  const [repoPreview, setRepoPreview] = useState<RepoSkillPreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [editing, setEditing] = useState<DramaSkill | null>(null)
  const [form] = Form.useForm()
  const [skillContentMd, setSkillContentMd] = useState('')
  const [saving, setSaving] = useState(false)
  const [compareOpen, setCompareOpen] = useState(false)
  const [compareData, setCompareData] = useState<SkillPublishCompare | null>(null)
  const [compareLoading, setCompareLoading] = useState(false)
  const [pendingPublishId, setPendingPublishId] = useState<string | null>(null)
  const [viewOpen, setViewOpen] = useState(false)
  const [viewing, setViewing] = useState<DramaSkill | null>(null)
  const [viewLoading, setViewLoading] = useState(false)
  const [rollbackOpen, setRollbackOpen] = useState(false)
  const [rollbackSkillCode, setRollbackSkillCode] = useState<string | null>(null)
  const [versions, setVersions] = useState<DramaSkill[]>([])
  const [versionsLoading, setVersionsLoading] = useState(false)
  const [pullingId, setPullingId] = useState<string | null>(null)

  const repoChangedCount = data.filter((r) => r.repo_has_changes).length

  const load = async () => {
    setLoading(true)
    try {
      const res = await listDramaSkillsAdmin({ page, page_size: 20 })
      setData((res.data as DramaSkill[]) || [])
      setTotal(res.total || 0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [page])

  const fetchRepoPreview = useCallback(async (folder: string) => {
    setPreviewLoading(true)
    try {
      const res = await previewRepoSkill(folder)
      setRepoPreview((res.data as RepoSkillPreview) || null)
    } catch (e: unknown) {
      setRepoPreview(null)
      message.error((e as { message?: string })?.message || '预览加载失败')
    } finally {
      setPreviewLoading(false)
    }
  }, [])

  useEffect(() => {
    if (repoOpen && selectedFolder) {
      fetchRepoPreview(selectedFolder)
    }
  }, [repoOpen, selectedFolder, fetchRepoPreview])

  const openCreateChooser = () => {
    setCreateMode('online')
    setCreateModeOpen(true)
  }

  const startOnlineCreate = () => {
    setCreateModeOpen(false)
    setEditing(null)
    form.resetFields()
    form.setFieldsValue({ stage: 'production' })
    setSkillContentMd(
      buildSkillContentTemplate({
        skillName: '技能名称',
        skillId: 'skill.example',
      }),
    )
    setDrawerOpen(true)
  }

  const openRepoImport = async () => {
    setCreateModeOpen(false)
    setRepoOpen(true)
    setRepoPreview(null)
    setSelectedFolder(undefined)
    try {
      const res = await listRepoSkillFolders()
      const folders = (res.data as string[]) || []
      setRepoFolders(folders)
      if (folders.length > 0) {
        setSelectedFolder(folders[0])
      }
    } catch {
      message.error('加载代码库 Skill 目录失败')
    }
  }

  const handleRepoImport = async () => {
    if (!selectedFolder || !repoPreview) return
    if (!repoPreview.valid) {
      message.error(repoPreview.validation_error || 'SKILL 内容不符合规范，无法导入')
      return
    }

    setSaving(true)
    try {
      const res = await importRepoSkillAdmin({
        folder: selectedFolder,
        stage: 'production',
        publish: false,
        target_skill_id: repoPreview.target_skill_id,
      })
      showRepoSyncFeedback(res.data as DramaSkill & SkillRepoSyncResult, 'import')
      setRepoOpen(false)
      load()
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '拉取失败')
    } finally {
      setSaving(false)
    }
  }

  const handlePullFromRepo = async (row: DramaSkill) => {
    const folder = resolveRepoFolder(row)
    if (!folder) {
      message.warning('该 Skill 未绑定代码库目录，且无可用的内置目录映射')
      return
    }
    setPullingId(row.id)
    try {
      const res = await importRepoSkillAdmin({
        folder,
        target_skill_id: row.id,
        publish: false,
      })
      showRepoSyncFeedback(res.data as DramaSkill & SkillRepoSyncResult, 'reimport')
      if (editing?.id === row.id) {
        const detail = await getDramaSkillAdmin(row.id)
        setEditing(detail.data as DramaSkill)
        setSkillContentMd(
          (detail.data as DramaSkill).skill_content_md ||
            (detail.data as DramaSkill).system_markdown ||
            '',
        )
      }
      load()
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '拉取失败')
    } finally {
      setPullingId(null)
    }
  }

  const openPublishCompare = async (skillId: string) => {
    setCompareLoading(true)
    setPendingPublishId(skillId)
    setCompareOpen(true)
    setCompareData(null)
    try {
      const res = await compareSkillBeforePublish(skillId)
      setCompareData(res.data as SkillPublishCompare)
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '加载对比失败')
      setCompareOpen(false)
      setPendingPublishId(null)
    } finally {
      setCompareLoading(false)
    }
  }

  const confirmPublish = async () => {
    if (!pendingPublishId) return
    setSaving(true)
    try {
      await publishDramaSkillAdmin(pendingPublishId)
      message.success('已发布')
      setCompareOpen(false)
      setPendingPublishId(null)
      setCompareData(null)
      setDrawerOpen(false)
      load()
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '发布失败')
    } finally {
      setSaving(false)
    }
  }

  const openView = async (row: DramaSkill) => {
    setViewLoading(true)
    setViewOpen(true)
    setViewing(null)
    try {
      const res = await getDramaSkillAdmin(row.id)
      setViewing(res.data as DramaSkill)
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '加载失败')
      setViewOpen(false)
    } finally {
      setViewLoading(false)
    }
  }

  const openRollback = async (row: DramaSkill) => {
    setRollbackSkillCode(row.skill_code)
    setRollbackOpen(true)
    setVersions([])
    setVersionsLoading(true)
    try {
      const res = await listSkillVersionsAdmin(row.skill_code)
      setVersions((res.data as DramaSkill[]) || [])
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '加载版本历史失败')
      setRollbackOpen(false)
      setRollbackSkillCode(null)
    } finally {
      setVersionsLoading(false)
    }
  }

  const handleRollback = async (versionNum: number) => {
    if (!rollbackSkillCode) return
    setSaving(true)
    try {
      await rollbackSkillAdmin(rollbackSkillCode, versionNum)
      message.success(`已回滚到版本 v${versionNum}`)
      setRollbackOpen(false)
      setRollbackSkillCode(null)
      setVersions([])
      load()
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '回滚失败')
    } finally {
      setSaving(false)
    }
  }

  const openEdit = async (row: DramaSkill) => {
    setSaving(true)
    try {
      const res = await getDramaSkillAdmin(row.id)
      const skill = res.data as DramaSkill
      setEditing(skill)
      form.setFieldsValue({
        skill_code: skill.skill_code,
        name: skill.name,
        stage: skill.stage,
        description: skill.description,
      })
      setSkillContentMd(
        skill.skill_content_md ||
          skill.system_markdown ||
          buildSkillContentTemplate({ skillName: skill.name, skillId: skill.skill_code }),
      )
      setDrawerOpen(true)
    } finally {
      setSaving(false)
    }
  }

  const insertTemplate = () => {
    const code = form.getFieldValue('skill_code') as string | undefined
    const name = form.getFieldValue('name') as string | undefined
    setSkillContentMd(
      buildSkillContentTemplate({
        skillId: code || 'skill.example',
        skillName: name || '技能名称',
      }),
    )
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    if (!skillContentMd.trim()) {
      message.warning('请填写 Skill 描述（SKILL.md 规范）')
      return
    }

    const payload = {
      name: values.name as string,
      stage: values.stage as string,
      description: (values.description as string) || '',
      skill_content_md: skillContentMd,
      source_type: 'online' as const,
    }

    setSaving(true)
    try {
      if (editing) {
        await updateDramaSkillAdmin(editing.id, payload)
        message.success('已保存草稿')
      } else {
        await createDramaSkillAdmin({
          skill_code: values.skill_code as string,
          ...payload,
        })
        message.success('已创建草稿')
      }
      setDrawerOpen(false)
      load()
    } catch (e: unknown) {
      message.error((e as { message?: string })?.message || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const columns: ColumnsType<DramaSkill> = [
    { title: 'Code', dataIndex: 'skill_code', width: 180, ellipsis: true },
    { title: '名称', dataIndex: 'name', width: 160, ellipsis: true },
    {
      title: '来源',
      dataIndex: 'source_type',
      width: 90,
      render: (_, r) => {
        const src = r.source_type || r.source
        return (
          <Tag color={src === 'repo' ? 'blue' : 'default'} icon={src === 'repo' ? <CodeOutlined /> : <FileMarkdownOutlined />}>
            {src === 'repo' ? '代码库' : '在线'}
          </Tag>
        )
      },
    },
    {
      title: '代码库',
      width: 130,
      render: (_, r) => {
        if (!r.repo_folder && !r.repo_available) return '—'
        if (r.repo_has_changes) {
          return (
            <Tag color="orange" icon={<CodeOutlined />}>
              有更新{r.repo_version ? ` · ${r.repo_version}` : ''}
            </Tag>
          )
        }
        if (r.repo_available) {
          return <Tag color="default">已同步</Tag>
        }
        return <Tag>不可用</Tag>
      },
    },
    {
      title: '标签',
      width: 140,
      ellipsis: true,
      render: (_, r) => r.skill_meta?.tag || r.description || '—',
    },
    {
      title: '阶段',
      dataIndex: 'stage',
      width: 100,
      render: (v) => <Tag>{v}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (v) => <Tag color={v === 'published' ? 'green' : 'gold'}>{v}</Tag>,
    },
    { title: '版本', dataIndex: 'version', width: 80 },
    {
      title: '操作',
      width: 360,
      render: (_, r) => (
        <Space size={4} wrap>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => openView(r)}>
            查看
          </Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(r)}>
            编辑
          </Button>
          {resolveRepoFolder(r) ? (
            <Button
              type="link"
              size="small"
              icon={<ReloadOutlined />}
              loading={pullingId === r.id}
              onClick={() => handlePullFromRepo(r)}
            >
              拉取
            </Button>
          ) : null}
          <Button
            type="link"
            size="small"
            icon={<SendOutlined />}
            onClick={() => openPublishCompare(r.id)}
          >
            发布
          </Button>
          <Button type="link" size="small" icon={<RollbackOutlined />} onClick={() => openRollback(r)}>
            回滚
          </Button>
          {!r.immutable && (
            <Popconfirm title="确定删除？" onConfirm={() => deleteDramaSkillAdmin(r.id).then(load)}>
              <Button type="link" size="small" danger>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div className="skill-hub" style={{ padding: 24 }}>
      <div className="knowledge-hub__hero" style={{ marginBottom: 20 }}>
        <div>
          <h2 className="knowledge-hub__hero-title">
            <ThunderboltOutlined /> Skill 库
          </h2>
          <p className="knowledge-hub__hero-desc">
            创作助手<strong>仅使用 Skill 库已发布</strong>的 Skill；代码库 <code>skills/</code>{' '}
            目录仅用于编辑与导入注册，运行时不会直接被读取。支持在线新建或从代码库导入后发布。
          </p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateChooser}>
          新建 Skill
        </Button>
      </div>

      {repoChangedCount > 0 ? (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message={`${repoChangedCount} 个 Skill 代码库有未同步更新`}
          description="代码库 skills/ 内容与 Skill 库草稿不一致。请使用「拉取」同步到草稿，确认后再「发布」上线。"
        />
      ) : null}

      <Table
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={data}
        pagination={{ current: page, total, pageSize: 20, onChange: setPage }}
      />

      <Modal
        title="新建 Skill"
        open={createModeOpen}
        onCancel={() => setCreateModeOpen(false)}
        footer={null}
        width={480}
      >
        <Radio.Group
          value={createMode}
          onChange={(e) => setCreateMode(e.target.value)}
          style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}
        >
          <Radio value="online">
            <strong>在线编辑</strong>
            <div style={{ color: '#888', fontSize: 12, marginLeft: 24 }}>
              在平台内按 SKILL.md 规范编写 frontmatter 与八段式描述
            </div>
          </Radio>
          <Radio value="repo">
            <strong>从代码库导入</strong>
            <div style={{ color: '#888', fontSize: 12, marginLeft: 24 }}>
              选择 skills/ 子目录并实时预览，导入后须发布，创作助手才会加载
            </div>
          </Radio>
        </Radio.Group>
        <div style={{ textAlign: 'right' }}>
          <Space>
            <Button onClick={() => setCreateModeOpen(false)}>取消</Button>
            <Button
              type="primary"
              onClick={() => (createMode === 'online' ? startOnlineCreate() : openRepoImport())}
            >
              继续
            </Button>
          </Space>
        </div>
      </Modal>

      <Modal
        className="skill-repo-import-modal"
        title="从代码库导入 Skill"
        open={repoOpen}
        onCancel={() => setRepoOpen(false)}
        footer={
          repoFolders.length > 0 ? (
            <Space>
              <Button onClick={() => setRepoOpen(false)}>取消</Button>
              <Button
                type="primary"
                loading={saving}
                disabled={!repoPreview?.valid}
                onClick={() => handleRepoImport()}
              >
                拉取到草稿
              </Button>
            </Space>
          ) : null
        }
        width={960}
        destroyOnClose
      >
        <p className="skill-repo-import-modal__hint">
          标准目录：<code>skills/&lt;folder&gt;/SKILL.md</code> +{' '}
          <code>skills/&lt;folder&gt;/scripts/</code>。选择文件夹后实时拉取预览；已导入 Skill 将走更新而非新建。
        </p>
        {repoFolders.length === 0 ? (
          <div className="skill-repo-import-modal__empty">未找到符合规范的 Skill 目录</div>
        ) : (
          <div className="skill-repo-import-layout">
            <div className="skill-repo-import-layout__sidebar">
              <div className="skill-repo-import-layout__label">选择 Skill 文件夹</div>
              <Select
                style={{ width: '100%' }}
                value={selectedFolder}
                options={repoFolders.map((f) => ({ value: f, label: f }))}
                onChange={setSelectedFolder}
              />
              {previewLoading ? (
                <div className="skill-repo-import-modal__loading">
                  <Spin size="small" /> 加载预览…
                </div>
              ) : repoPreview ? (
                <div className="skill-repo-import-meta">
                  <div className="skill-repo-import-meta__title">
                    {repoPreview.skill_name}
                    {repoPreview.registered ? (
                      <Tag color="green">已发布 {repoPreview.published_version || ''}</Tag>
                    ) : (
                      <Tag>未注册</Tag>
                    )}
                  </div>
                  <div>
                    <span className="skill-repo-import-list__label">skill_id</span>
                    <code>{repoPreview.skill_id}</code>
                  </div>
                  {repoPreview.tag ? (
                    <div>
                      <span className="skill-repo-import-list__label">标签</span>
                      {repoPreview.tag}
                    </div>
                  ) : null}
                  {repoPreview.script_files?.length ? (
                    <div>
                      <span className="skill-repo-import-list__label">脚本</span>
                      {repoPreview.script_files.join(', ')}
                    </div>
                  ) : null}
                  {!repoPreview.valid && repoPreview.validation_error ? (
                    <Alert type="error" showIcon message={repoPreview.validation_error} />
                  ) : null}
                </div>
              ) : null}
            </div>
            <div className="skill-repo-import-layout__preview">
              <div className="skill-repo-import-layout__label">SKILL.md 预览</div>
              {previewLoading ? (
                <div className="skill-repo-import-modal__loading">加载中…</div>
              ) : repoPreview?.skill_content_md ? (
                <pre className="skill-repo-import-preview">{repoPreview.skill_content_md}</pre>
              ) : (
                <div className="skill-repo-import-modal__empty">请选择文件夹</div>
              )}
            </div>
          </div>
        )}
      </Modal>

      <Modal
        title="发布前对比"
        open={compareOpen}
        onCancel={() => {
          setCompareOpen(false)
          setPendingPublishId(null)
          setCompareData(null)
        }}
        width="min(1200px, 96vw)"
        footer={
          <Space>
            <Button
              onClick={() => {
                setCompareOpen(false)
                setPendingPublishId(null)
                setCompareData(null)
              }}
            >
              取消
            </Button>
            <Button
              type="primary"
              loading={saving || compareLoading}
              disabled={!pendingPublishId}
              onClick={confirmPublish}
            >
              确认发布
            </Button>
          </Space>
        }
        destroyOnClose
      >
        {compareLoading ? (
          <div className="skill-repo-import-modal__loading">加载对比…</div>
        ) : compareData ? (
          <>
            <p className="skill-repo-import-modal__hint">
              Skill <code>{compareData.skill_code}</code>：草稿{' '}
              <Tag>{compareData.draft_version}</Tag>
              {compareData.has_published ? (
                <>
                  {' '}
                  vs 线上 <Tag color="green">{compareData.published_version}</Tag>
                </>
              ) : (
                '（尚无线上版本，首次发布）'
              )}
              {!compareData.has_changes && compareData.has_published ? (
                <Alert style={{ marginTop: 12 }} type="info" showIcon message="与线上版本内容一致" />
              ) : null}
            </p>
            {compareData.has_published ? (
              <SkillSideBySideDiff
                oldText={compareData.published_content}
                newText={compareData.draft_content}
                oldLabel={`线上 ${compareData.published_version || ''}`.trim()}
                newLabel={`草稿 ${compareData.draft_version || ''}`.trim()}
              />
            ) : (
              <SkillSideBySideDiff
                oldText=""
                newText={compareData.draft_content}
                oldLabel="线上（尚无）"
                newLabel={`草稿 ${compareData.draft_version || ''}`.trim()}
              />
            )}
          </>
        ) : null}
      </Modal>

      <Drawer
        title={editing ? `编辑 Skill · ${editing.skill_code}` : '在线新建 Skill'}
        width={920}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        destroyOnClose
        extra={
          <Space>
            {editing && resolveRepoFolder(editing) ? (
              <Button
                icon={<ReloadOutlined />}
                loading={pullingId === editing.id}
                onClick={() => handlePullFromRepo(editing)}
              >
                拉取
              </Button>
            ) : null}
            <Button onClick={() => setDrawerOpen(false)}>取消</Button>
            <Button type="primary" loading={saving} onClick={() => handleSave()}>
              保存草稿
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="skill_code"
            label="Skill Code（与 frontmatter skill_id 一致）"
            rules={[{ required: true, pattern: /^[a-z][a-z0-9._-]+$/, message: '小写英文+点号/下划线' }]}
          >
            <Input placeholder="skill_art_tianshuqitan" disabled={!!editing} />
          </Form.Item>
          <Form.Item name="name" label="名称（可与 frontmatter skill_name 同步）" rules={[{ required: true }]}>
            <Input placeholder="如：上美天书奇谭风格出图" />
          </Form.Item>
          <Form.Item name="stage" label="适用阶段" rules={[{ required: true }]}>
            <Select options={STAGE_OPTIONS} />
          </Form.Item>
          <Form.Item name="description" label="简短说明（可选，通常用 frontmatter tag）">
            <Input placeholder="AI绘画/国风风格" />
          </Form.Item>
          {editing && resolveRepoFolder(editing) ? (
            <Alert
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
              message={`代码库目录 skills/${resolveRepoFolder(editing)}，可使用「拉取」同步 SKILL.md 到草稿，再单独「发布」上线`}
            />
          ) : null}
          <Form.Item
            label={
              <Space>
                <span>Skill 描述（SKILL.md 标准）</span>
                <Button type="link" size="small" onClick={insertTemplate}>
                  插入空模板
                </Button>
              </Space>
            }
            required
          >
            <MarkdownEditor value={skillContentMd} onChange={setSkillContentMd} height={480} />
            <div style={{ marginTop: 8, color: '#888', fontSize: 12 }}>
              须包含 frontmatter（skill_name / skill_id / version / author / update_time / tag）及八个章节标题。
            </div>
          </Form.Item>
        </Form>
      </Drawer>

      <Drawer
        title={viewing ? `查看 Skill · ${viewing.skill_code}` : '查看 Skill'}
        width={920}
        open={viewOpen}
        onClose={() => {
          setViewOpen(false)
          setViewing(null)
        }}
        destroyOnClose
      >
        {viewLoading ? (
          <div className="skill-repo-import-modal__loading">
            <Spin /> 加载中…
          </div>
        ) : viewing ? (
          <>
            <Descriptions column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="名称">{viewing.name}</Descriptions.Item>
              <Descriptions.Item label="阶段">{viewing.stage}</Descriptions.Item>
              <Descriptions.Item label="来源">
                {(viewing.source_type || viewing.source) === 'repo' ? '代码库' : '在线'}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={viewing.status === 'published' ? 'green' : 'gold'}>{viewing.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="版本">{viewing.version}</Descriptions.Item>
              {viewing.repo_path ? (
                <Descriptions.Item label="代码库目录">{viewing.repo_path}</Descriptions.Item>
              ) : null}
            </Descriptions>
            <MarkdownEditor
              value={
                viewing.skill_content_md ||
                viewing.system_markdown ||
                ''
              }
              onChange={() => {}}
              readOnly
              height={560}
            />
          </>
        ) : null}
      </Drawer>

      <Modal
        title={rollbackSkillCode ? `版本回滚 · ${rollbackSkillCode}` : '版本回滚'}
        open={rollbackOpen}
        onCancel={() => {
          setRollbackOpen(false)
          setRollbackSkillCode(null)
          setVersions([])
        }}
        footer={null}
        width={720}
        destroyOnClose
      >
        {versionsLoading ? (
          <div className="skill-repo-import-modal__loading">
            <Spin /> 加载版本历史…
          </div>
        ) : versions.length > 0 ? (
          <Timeline
            items={versions.map((v) => ({
              color: v.status === 'published' ? 'green' : v.status === 'draft' ? 'gold' : 'gray',
              children: (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                  <div>
                    <strong>v{v.version}</strong>
                    <Tag style={{ marginLeft: 8 }}>{v.status}</Tag>
                    {v.source_type === 'repo' || v.source === 'repo' ? (
                      <Tag color="blue" icon={<CodeOutlined />}>
                        代码库
                      </Tag>
                    ) : null}
                  </div>
                  {v.status === 'published' ? (
                    <Tag color="green">当前线上</Tag>
                  ) : (
                    <Popconfirm
                      title={`确定回滚到 v${v.version}？`}
                      description="将把该历史版本重新设为线上版本"
                      onConfirm={() => handleRollback(v.version_num ?? Number.parseInt(v.version, 10))}
                    >
                      <Button size="small" type="primary" icon={<RollbackOutlined />} loading={saving}>
                        回滚到此版本
                      </Button>
                    </Popconfirm>
                  )}
                </div>
              ),
            }))}
          />
        ) : (
          <Alert type="info" showIcon message="暂无版本记录" />
        )}
      </Modal>
    </div>
  )
}
