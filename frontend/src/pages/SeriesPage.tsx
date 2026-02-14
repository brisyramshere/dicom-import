import { useState, useEffect } from 'react'
import { seriesApi, Series } from '@/lib/api'
import { useSearchParams } from 'react-router-dom'

export function SeriesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [series, setSeries] = useState<Series[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<string[]>([])

  // 筛选条件
  const [filters, setFilters] = useState({
    patient_id: searchParams.get('patient_id') || '',
    patient_name: searchParams.get('patient_name') || '',
    modality: searchParams.get('modality') || '',
    protocol_name: searchParams.get('protocol_name') || '',
  })

  const page = parseInt(searchParams.get('page') || '1')
  const pageSize = 20

  const fetchSeries = async () => {
    setLoading(true)
    try {
      const [listRes, countRes] = await Promise.all([
        seriesApi.list({ page, page_size: pageSize, ...filters }),
        seriesApi.count(filters),
      ])
      setSeries(listRes.data.data || [])
      setTotal(countRes.data.total)
    } catch (error) {
      console.error('获取数据失败:', error)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchSeries()
  }, [page, filters])

  const handleSearch = (newFilters: typeof filters) => {
    setFilters(newFilters)
    setSearchParams({ ...newFilters, page: '1' })
  }

  const handleSelectAll = () => {
    if (selected.length === series.length) {
      setSelected([])
    } else {
      setSelected(series.map((s) => s.id))
    }
  }

  const handleExport = async () => {
    if (selected.length === 0) return alert('请选择要导出的序列')

    const targetDir = prompt('请输入导出目录路径:', '/data/exports')
    if (!targetDir) return

    try {
      const res = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ series_ids: selected, target_dir: targetDir }),
      })
      const data = await res.json()
      alert(`导出完成！共导出 ${data.exported_count} 个序列到 ${data.target_dir}`)
    } catch (error) {
      alert('导出失败')
    }
  }

  const modalityOptions = ['CT', 'MR', 'DR', 'DX', 'CR', 'US', 'XR']

  return (
    <div>
      {/* 搜索栏 */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="grid grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="患者ID"
            value={filters.patient_id}
            onChange={(e) => handleSearch({ ...filters, patient_id: e.target.value })}
            className="px-3 py-2 border rounded-md"
          />
          <input
            type="text"
            placeholder="患者姓名"
            value={filters.patient_name}
            onChange={(e) => handleSearch({ ...filters, patient_name: e.target.value })}
            className="px-3 py-2 border rounded-md"
          />
          <select
            value={filters.modality}
            onChange={(e) => handleSearch({ ...filters, modality: e.target.value })}
            className="px-3 py-2 border rounded-md"
          >
            <option value="">全部模态</option>
            {modalityOptions.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="协议名称"
            value={filters.protocol_name}
            onChange={(e) => handleSearch({ ...filters, protocol_name: e.target.value })}
            className="px-3 py-2 border rounded-md"
          />
        </div>
      </div>

      {/* 操作栏 */}
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-gray-600">
          共 {total} 条记录，当前第 {page} 页
        </div>
        <div className="space-x-2">
          <button
            onClick={handleSelectAll}
            className="px-4 py-2 bg-gray-100 rounded-md hover:bg-gray-200"
 text-gray-700          >
            {selected.length === series.length ? '取消全选' : '全选'}
          </button>
          <button
            onClick={handleExport}
            disabled={selected.length === 0}
            className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            导出选中 ({selected.length})
          </button>
        </div>
      </div>

      {/* 数据表格 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">选择</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">患者</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">模态</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">协议</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">检查日期</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">文件数</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">设备</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                  加载中...
                </td>
              </tr>
            ) : series.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                  暂无数据
                </td>
              </tr>
            ) : (
              series.map((s) => (
                <tr
                  key={s.id}
                  className={selected.includes(s.id) ? 'bg-blue-50' : ''}
                >
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selected.includes(s.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelected([...selected, s.id])
                        } else {
                          setSelected(selected.filter((id) => id !== s.id))
                        }
                      }}
                    />
                  </td>
                  <td className="px-6 py-4 text-sm font-mono text-gray-900">{s.id}</td>
                  <td className="px-6 py-4 text-sm">
                    <div className="text-gray-900">{s.patient_name || '-'}</div>
                    <div className="text-gray-500 text-xs">{s.patient_id}</div>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className="px-2 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-800">
                      {s.modality}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{s.protocol_name || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{s.study_date || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{s.file_count}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <div className="text-xs">{s.manufacturer}</div>
                    <div className="text-xs text-gray-400">{s.manufacturer_model}</div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      <div className="flex justify-center mt-4 space-x-2">
        <button
          onClick={() => setSearchParams({ ...Object.fromEntries(searchParams), page: String(page - 1) })}
          disabled={page <= 1}
          className="px-3 py-1 border rounded disabled:opacity-50"
        >
          上一页
        </button>
        <span className="px-3 py-1">
          第 {page} / {Math.ceil(total / pageSize)} 页
        </span>
        <button
          onClick={() => setSearchParams({ ...Object.fromEntries(searchParams), page: String(page + 1) })}
          disabled={page >= Math.ceil(total / pageSize)}
          className="px-3 py-1 border rounded disabled:opacity-50"
        >
          下一页
        </button>
      </div>
    </div>
  )
}
