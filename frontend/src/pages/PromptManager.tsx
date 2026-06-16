import React, { useState, useEffect } from 'react';
import {
  Button,
  Table,
  Modal,
  Form,
  Input,
  Select,
  Tag,
  Tooltip,
  Popconfirm,
  message,
  Space,
  Card,
  Timeline,
  Empty,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  RollbackOutlined,
  EyeOutlined,
  ArrowRightOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import type { PromptItem, PromptVersion } from '../types/prompt';
import {
  createPrompt,
  updatePrompt,
  deletePrompt,
  listPrompts,
  publishPrompt,
  rollbackPrompt,
  getPromptVersions,
} from '../api/prompt';
import { useGenerationStore } from '../store/generation';
const { TextArea } = Input;
const { Option } = Select;
const categoryMap: Record<string, string> = {
 text: '文本',
 image: '图片',
 video: '视频',
};
const categoryColors: Record<string, string> = {
 text: 'blue',
 image: 'green',
 video: 'purple',
};
export default function PromptManager() {
 const [prompts, setPrompts] = useState<PromptItem[]>([]);
 const [loading, setLoading] = useState(false);
 const [modalVisible, setModalVisible] = useState(false);
 const [versionModalVisible, setVersionModalVisible] = useState(false);
 const [form] = Form.useForm();
 const [editingItem, setEditingItem] = useState<PromptItem | null>(null);
 const [currentPromptId, setCurrentPromptId] = useState<string>('');
 const [versions, setVersions] = useState<PromptVersion[]>([]);
 const [pagination, setPagination] = useState({
 page: 1,
 pageSize: 10,
 total: 0,
 });
 const store = useGenerationStore();
 const fetchPrompts = async () => {
 setLoading(true);
 try {
 const res = await listPrompts({
 page: pagination.page,
 page_size: pagination.pageSize,
 });
 setPrompts(res.data.data);
 setPagination((prev) => ({
 ...prev,
 total: res.data.total,
 totalPages: res.data.total_pages,
 }));
 }
 catch (error) {
 message.error('获取提示词列表失败');
 }
 finally {
 setLoading(false);
 }
 };
 useEffect(() => {
 fetchPrompts();
 }, [pagination.page, pagination.pageSize]);
 const handleAdd = () => {
 form.resetFields();
 setEditingItem(null);
 setModalVisible(true);
 };
 const handleEdit = (item: PromptItem) => {
    form.setFieldsValue({
      name: item.name,
      content: item.content,
      category: item.category,
      tags: item.tags.join(','),
    });
    setEditingItem(item);
    setModalVisible(true);
  };
 const handleSave = async () => {
 const values = await form.validateFields();
 try {
 if (editingItem) {
 await updatePrompt(editingItem._id, {
 name: values.name,
 content: values.content,
 category: values.category,
 tags: values.tags.split(',').map((t: string) => t.trim()).filter(Boolean),
 });
 message.success('更新成功');
 }
 else {
 await createPrompt({
 name: values.name,
 content: values.content,
 category: values.category,
 tags: values.tags.split(',').map((t: string) => t.trim()).filter(Boolean),
 });
 message.success('创建成功');
 }
 setModalVisible(false);
 fetchPrompts();
 }
 catch (error) {
 message.error(editingItem ? '更新失败' : '创建失败');
 }
 };
 const handleDelete = async (id: string) => {
 try {
 await deletePrompt(id);
 message.success('删除成功');
 fetchPrompts();
 }
 catch (error) {
 message.error('删除失败');
 }
 };
 const handlePublish = async (item: PromptItem) => {
 try {
 await publishPrompt(item._id);
 message.success(`已发布版本 v${item.version}`);
 fetchPrompts();
 }
 catch (error) {
 message.error('发布失败');
 }
 };
 const handleViewVersions = async (promptId: string) => {
 setCurrentPromptId(promptId);
 try {
 const res = await getPromptVersions(promptId);
 setVersions(res.data);
 setVersionModalVisible(true);
 }
 catch (error) {
 message.error('获取版本列表失败');
 }
 };
 const handleRollback = async (version: number) => {
 try {
 await rollbackPrompt(currentPromptId, version);
 message.success(`已回滚到版本 v${version}`);
 setVersionModalVisible(false);
 fetchPrompts();
 }
 catch (error) {
 message.error('回滚失败');
 }
 };
 const handleQuickUse = (item: PromptItem) => {
 store.setParamsWithCategory(item.category as any, { prompt: item.content });
 store.setCategory(item.category as any);
 message.success(`已将提示词"${item.name}"引入${categoryMap[item.category]}创作`);
 };
 const columns = [
 {
 title: '名称',
 dataIndex: 'name',
 key: 'name',
 ellipsis: true,
 },
 {
 title: '分类',
 dataIndex: 'category',
 key: 'category',
 render: (category: string) => (<Tag color={categoryColors[category]}>{categoryMap[category]}</Tag>),
 },
 {
 title: '版本',
 dataIndex: 'version',
 key: 'version',
 render: (version: number, record: PromptItem) => (<span>
 v{version}
 {record.published_version === version && (<Tag color="green" style={{ marginLeft: 8 }}>已发布</Tag>)}
 </span>),
 },
 {
 title: '标签',
 dataIndex: 'tags',
 key: 'tags',
 render: (tags: string[]) => tags.map((tag) => (<Tag key={tag}>{tag}</Tag>)),
 },
 {
 title: '更新时间',
 dataIndex: 'updated_at',
 key: 'updated_at',
 render: (time: string) => new Date(time).toLocaleString(),
 },
 {
 title: '操作',
 key: 'actions',
 render: (_: any, record: PromptItem) => (<Space>
 <Tooltip title="查看版本">
 <Button size="small" onClick={() => handleViewVersions(record._id)}>
 <EyeOutlined/>
 </Button>
 </Tooltip>
 {record.published_version !== record.version && (<Tooltip title="发布版本">
 <Button size="small" type="primary" onClick={() => handlePublish(record)}>
 <CheckCircleOutlined/>
 </Button>
 </Tooltip>)}
 <Tooltip title="编辑">
 <Button size="small" onClick={() => handleEdit(record)}>
 <EditOutlined/>
 </Button>
 </Tooltip>
 {record.published_version === record.version && (<Tooltip title="快速引入">
 <Button size="small" type="link" onClick={() => handleQuickUse(record)}>
 <ArrowRightOutlined/>
 </Button>
 </Tooltip>)}
 <Popconfirm title="确定删除？" onConfirm={() => handleDelete(record._id)}>
 <Button size="small" danger>
 <DeleteOutlined/>
 </Button>
 </Popconfirm>
 </Space>),
 },
 ];
 return (<div style={{ padding: 24 }}>
 <Card title="提示词管理" extra={<Button type="primary" onClick={handleAdd} icon={<PlusOutlined/>}>
 新增提示词
 </Button>}>
 <Table dataSource={prompts} columns={columns} loading={loading} pagination={{
 current: pagination.page,
 pageSize: pagination.pageSize,
 total: pagination.total,
 onChange: (page, pageSize) => setPagination({ page, pageSize, total: pagination.total }),
 }} rowKey="_id" bordered/>
 </Card>

 {/* 新增/编辑弹窗 */}
 <Modal title={editingItem ? '编辑提示词' : '新增提示词'} visible={modalVisible} onOk={handleSave} onCancel={() => setModalVisible(false)} width={700}>
 <Form form={form} layout="vertical">
 <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
 <Input placeholder="请输入提示词名称"/>
 </Form.Item>
 <Form.Item name="category" label="分类" rules={[{ required: true, message: '请选择分类' }]}>
 <Select placeholder="请选择分类">
 <Option value="text">文本创作</Option>
 <Option value="image">图片生成</Option>
 <Option value="video">视频生成</Option>
 </Select>
 </Form.Item>
 <Form.Item name="content" label="内容（支持Markdown）" rules={[{ required: true, message: '请输入提示词内容' }]}>
 <TextArea rows={12} placeholder="支持 Markdown 格式，如 **粗体**、*斜体*、# 标题等" style={{ fontFamily: 'monospace' }}/>
 </Form.Item>
 <Form.Item name="tags" label="标签">
 <Input placeholder="多个标签用逗号分隔"/>
 </Form.Item>
 </Form>
 </Modal>

 {/* 版本管理弹窗 */}
 <Modal title="版本历史" visible={versionModalVisible} onCancel={() => setVersionModalVisible(false)} width={700} footer={null}>
 {versions.length > 0 ? (<Timeline mode="left">
 {versions.map((version) => (<Timeline.Item key={version._id} color={version.comment.includes('rollback') ? 'orange' : 'green'}>
 <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
 <div>
 <span style={{ fontWeight: 'bold' }}>v{version.version}</span>
 <span style={{ marginLeft: 12 }}>
 {new Date(version.created_at).toLocaleString()}
 </span>
 {version.comment && (<span style={{ marginLeft: 12, color: '#999' }}>
 {version.comment}
 </span>)}
 </div>
 <Space>
 <Button size="small" onClick={() => navigator.clipboard.writeText(version.content)}>
 <CopyOutlined/>
 复制
 </Button>
 <Button size="small" type="primary" onClick={() => handleRollback(version.version)} icon={<RollbackOutlined/>}>
 回滚到此版本
 </Button>
 </Space>
 </div>
 <div style={{ marginTop: 8, padding: 12, background: '#fafafa', borderRadius: 4 }}>
 {version.content.length > 200 ? `${version.content.slice(0, 200)}...` : version.content}
 </div>
 </Timeline.Item>))}
 </Timeline>) : (<Empty description="暂无版本记录"/>)}
 </Modal>
 </div>);
}

