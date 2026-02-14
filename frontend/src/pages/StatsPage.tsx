import { useState, useEffect } from 'react'
import { statsApi, seriesApi } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

interface ModalityStat {
  modality: string
  count: number
}

interface DateStat {
  date: string
  count: number
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

export function StatsPage() {
  const [modalityStats, setModalityStats] = useState<ModalityStat[]>([])
  const [dateStats, setDateStats] = useState<DateStat[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [modalityRes, dateRes, countRes] = await Promise.all([
          statsApi.modality(),
          statsApi.date(),
          seriesApi.count(),
        ])
        setModalityStats(modalityRes.data || [])
        setDateStats(dateRes.data || [])
        setTotal(countRes.data.total)
      } catch (error) {
        console.error('获取统计数据失败:', error)
      }
      setLoading(false)
    }

    fetchData()
  }, [])

  if (loading) {
    return <div className="text-center py-8">加载中...</div>
  }

  return (
    <div>
      {/* 总览卡片 */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-500">总序列数</div>
          <div className="text-3xl font-bold text-primary">{total}</div>
        </div>
        {modalityStats.slice(0, 3).map((stat, idx) => (
          <div key={stat.modality} className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-500">{stat.modality}</div>
            <div className="text-3xl font-bold" style={{ color: COLORS[idx % COLORS.length] }}>
              {stat.count}
            </div>
          </div>
        ))}
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-2 gap-6">
        {/* 模态分布饼图 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium mb-4">模态分布</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={modalityStats}
                  dataKey="count"
                  nameKey="modality"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {modalityStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 日期趋势图 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium mb-4">近期扫描趋势</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[...dateStats].reverse()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 详细数据表 */}
      <div className="bg-white rounded-lg shadow mt-6 p-6">
        <h3 className="text-lg font-medium mb-4">模态统计明细</h3>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">模态</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">数量</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">占比</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {modalityStats.map((stat, idx) => (
              <tr key={stat.modality}>
                <td className="px-6 py-4 text-sm font-medium">
                  <span
                    className="px-2 py-1 text-xs rounded"
                    style={{ backgroundColor: COLORS[idx % COLORS.length] + '20', color: COLORS[idx % COLORS.length] }}
                  >
                    {stat.modality}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm">{stat.count}</td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {total > 0 ? ((stat.count / total) * 100).toFixed(1) : 0}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
