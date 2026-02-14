import { useState, useEffect } from 'react'
import { configApi, scanApi, filterRuleApi, ScanConfig, Scan, FilterRule } from '@/lib/api'

export function ConfigsPage() {
  const [configs, setConfigs] = useState<ScanConfig[]>([])
  const [scans, setScans] = useState<Scan[]>([])
  const [filterRules, setFilterRules] = useState<FilterRule[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'config' | 'scan' | 'filter'>('config')

  // 新建配置表单
  const [newConfig, setNewConfig] = useState({
    scan_path: '',
    description: '',
    schedule_type: 'manual',
  })

  // 新建筛选规则
  const [newRule, setNewRule] = useState({
    modality: 'CT',
    min_slice_thickness: 0,
    min_image_count: 10,
  })

  const fetchData = async () => {
    try {
      const [configRes, scanRes, ruleRes] = await Promise.all([
        configApi.list(),
        scanApi.list({ page_size: 10 }),
        filterRuleApi.list(),
      ])
      setConfigs(configRes.data || [])
      setScans(scanRes.data || [])
      setFilterRules(ruleRes.data || [])
    } catch (error) {
      console.error('获取数据失败:', error)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleCreateConfig = async () => {
    if (!newConfig.scan_path) return alert('请输入扫描路径')
    try {
      await configApi.create(newConfig)
      setNewConfig({ scan_path: '', description: '', schedule_type: 'manual' })
      fetchData()
      alert('创建成功')
    } catch (error) {
      alert('创建失败')
    }
  }

  const handleRunScan = async (configId: number) => {
    setLoading(true)
    try {
      await scanApi.run(configId)
      fetchData()
      alert('扫描完成')
    } catch (error) {
      alert('扫描失败')
    }
    setLoading(false)
  }

  const handleDeleteConfig = async (id: number) => {
    if (!confirm('确定删除?')) return
    try {
      await configApi.delete(id)
      fetchData()
    } catch (error) {
      alert('删除失败')
    }
  }

  const handleCreateRule = async () => {
    try {
      await filterRuleApi.create(newRule)
      setNewRule({ modality: 'CT', min_slice_thickness: 0, min_image_count: 10 })
      fetchData()
      alert('创建成功')
    } catch (error) {
      alert('创建失败')
    }
  }

  const handleDeleteRule = async (id: number) => {
    try {
      await filterRuleApi.delete(id)
      fetchData()
    } catch (error) {
      alert('删除失败')
    }
  }

  return (
    <div>
      {/* 标签页切换 */}
      <div className="flex border-b mb-4">
        <button
          onClick={() => setActiveTab('config')}
          className={`px-4 py-2 ${activeTab === 'config' ? 'border-b-2 border-primary font-medium' : 'text-gray-500'}`}
        >
          扫描配置
        </button>
        <button
          onClick={() => setActiveTab('scan')}
          className={`px-4 py-2 ${activeTab === 'scan' ? 'border-b-2 border-primary font-medium' : 'text-gray-500'}`}
        >
          扫描历史
        </button>
        <button
          onClick={() => setActiveTab('filter')}
          className={`px-4 py-2 ${activeTab === 'filter' ? 'border-b-2 border-primary font-medium' : 'text-gray-500'}`}
        >
          筛选规则
        </button>
      </div>

      {/* 扫描配置 */}
      {activeTab === 'config' && (
        <div>
          <div className="bg-white rounded-lg shadow p-4 mb-4">
            <h3 className="text-lg font-medium mb-4">新增扫描路径</h3>
            <div className="grid grid-cols-3 gap-4">
              <input
                type="text"
                placeholder="扫描路径 (如 /data/dicom1)"
                value={newConfig.scan_path}
                onChange={(e) => setNewConfig({ ...newConfig, scan_path: e.target.value })}
                className="px-3 py-2 border rounded-md"
              />
              <input
                type="text"
                placeholder="描述"
                value={newConfig.description}
                onChange={(e) => setNewConfig({ ...newConfig, description: e.target.value })}
                className="px-3 py-2 border rounded-md"
              />
              <select
                value={newConfig.schedule_type}
                onChange={(e) => setNewConfig({ ...newConfig, schedule_type: e.target.value })}
                className="px-3 py-2 border rounded-md"
              >
                <option value="manual">手动</option>
                <option value="weekly">每周</option>
              </select>
            </div>
            <button
              onClick={handleCreateConfig}
              className="mt-4 px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90"
            >
              添加
            </button>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">路径</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">描述</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">扫描类型</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">上次扫描</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {configs.map((c) => (
                  <tr key={c.id}>
                    <td className="px-6 py-4 text-sm font-mono">{c.scan_path}</td>
                    <td className="px-6 py-4 text-sm">{c.description || '-'}</td>
                    <td className="px-6 py-4 text-sm">{c.schedule_type === 'manual' ? '手动' : '每周'}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">{c.last_scan_at || '从未'}</td>
                    <td className="px-6 py-4 text-sm space-x-2">
                      <button
                        onClick={() => handleRunScan(c.id)}
                        disabled={loading}
                        className="text-primary hover:underline"
                      >
                        扫描
                      </button>
                      <button
                        onClick={() => handleDeleteConfig(c.id)}
                        className="text-red-600 hover:underline"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 扫描历史 */}
      {activeTab === 'scan' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">路径</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">发现序列</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">新增</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">重复</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {scans.map((s) => (
                <tr key={s.id}>
                  <td className="px-6 py-4 text-sm font-mono">{s.id}</td>
                  <td className="px-6 py-4 text-sm">{s.scan_path}</td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`px-2 py-1 text-xs rounded ${
                        s.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : s.status === 'running'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {s.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">{s.series_found}</td>
                  <td className="px-6 py-4 text-sm text-green-600">{s.series_new}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{s.series_duplicated}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{s.started_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 筛选规则 */}
      {activeTab === 'filter' && (
        <div>
          <div className="bg-white rounded-lg shadow p-4 mb-4">
            <h3 className="text-lg font-medium mb-4">新增筛选规则</h3>
            <div className="grid grid-cols-4 gap-4">
              <select
                value={newRule.modality}
                onChange={(e) => setNewRule({ ...newRule, modality: e.target.value })}
                className="px-3 py-2 border rounded-md"
              >
                <option value="CT">CT</option>
                <option value="MR">MR</option>
                <option value="DR">DR</option>
                <option value="DX">DX</option>
              </select>
              <input
                type="number"
                placeholder="最大层厚(mm)"
                value={newRule.min_slice_thickness}
                onChange={(e) => setNewRule({ ...newRule, min_slice_thickness: parseInt(e.target.value) })}
                className="px-3 py-2 border rounded-md"
              />
              <input
                type="number"
                placeholder="最少图片数"
                value={newRule.min_image_count}
                onChange={(e) => setNewRule({ ...newRule, min_image_count: parseInt(e.target.value) })}
                className="px-3 py-2 border rounded-md"
              />
              <button
                onClick={handleCreateRule}
                className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90"
              >
                添加
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">模态</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">最大层厚(mm)</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">最少图片数</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filterRules.map((r) => (
                  <tr key={r.id}>
                    <td className="px-6 py-4 text-sm font-medium">{r.modality}</td>
                    <td className="px-6 py-4 text-sm">{r.min_slice_thickness || '-'}</td>
                    <td className="px-6 py-4 text-sm">{r.min_image_count || '-'}</td>
                    <td className="px-6 py-4 text-sm">
                      <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-800">
                        {r.is_active ? '启用' : '禁用'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <button
                        onClick={() => handleDeleteRule(r.id)}
                        className="text-red-600 hover:underline"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
