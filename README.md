# DICOM数据管理系统

## 功能特性

- **数据扫描**: 扫描指定目录，自动识别DICOM序列
- **去重处理**: 基于SeriesInstanceUID自动去重，保留多个路径
- **数据查询**: 支持多条件筛选患者、模态、协议等
- **一键导出**: 选中序列后导出到本地，同时生成meta.json
- **统计功能**: 模态分布、扫描趋势等可视化
- **定时扫描**: 支持手动和每周自动扫描

## 快速开始

### 方式一：Docker部署（推荐）

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 方式二：本地部署

#### 后端

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 或构建生产版本
npm run build
```

### 访问界面

- 前端: http://localhost:3000
- API文档: http://localhost:8000/docs

### 3. 配置扫描路径

1. 进入"扫描配置"页面
2. 添加扫描路径（如 `/data/nas/dicom1`）
3. 点击"扫描"按钮开始扫描

### 4. 挂载NAS目录

在 `docker-compose.yml` 中添加:

```yaml
services:
  api:
    volumes:
      # 格式: 宿主机路径:容器内路径
      - /your/nas/path:/data/nas/dicom1
```

## 目录结构

```
.
├── app/                    # 后端代码
│   ├── api/               # API路由
│   ├── db/                # 数据库模型
│   ├── schemas/           # Pydantic模型
│   ├── services/          # 业务逻辑
│   └── main.py            # 入口
├── frontend/              # 前端代码
├── data/                  # 数据目录（SQLite）
├── docker-compose.yml     # 部署配置
└── Dockerfile            # 后端镜像
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| DATABASE_URL | sqlite:///app/data/dicom.db | 数据库连接 |

## 使用说明

### 数据导出

1. 在"数据查询"页面筛选需要的数据
2. 勾选要导出的序列
3. 点击"导出选中"按钮
4. 输入目标目录路径
5. 系统会将选中的序列拷贝到目标目录，每个序列一个文件夹，同时生成meta.json

### 筛选规则

在"扫描配置"页面可以设置不同模态的筛选规则：

- CT: 最大层厚(mm)
- MR: 最少图片数
- DR/DX: 最少图片数

设置后，新扫描会应用这些规则。

## API文档

启动服务后访问 http://localhost:8000/docs 查看完整API文档。

## 注意事项

1. 确保NAS路径正确挂载到容器内
2. 首次扫描可能需要较长时间（TB级数据）
3. 导出目录需要有写入权限
