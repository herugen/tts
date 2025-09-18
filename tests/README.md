# 测试目录说明

## 目录结构

```
tests/
├── README.md                    # 测试说明文档
├── conftest.py                  # 测试配置和fixtures
├── unit/                        # 单元测试
│   ├── test_health.py           # 健康检查测试
│   ├── test_uploads.py          # 文件上传测试
│   ├── test_voices.py           # 音色管理测试
│   ├── test_jobs.py             # TTS任务测试
│   └── test_queue.py            # 队列状态测试
├── integration/                 # 集成测试
│   └── test_integration.py      # 端到端测试
├── utils/                       # 测试工具
│   ├── test_data_generator.py   # 测试数据生成器
│   └── simple_test.py          # 简化测试脚本
└── scripts/                     # 测试脚本
    ├── run_tests.py             # 测试运行脚本
    ├── test_coverage.py         # 覆盖率报告脚本
    └── generate_test_report.py  # 测试报告生成器
```

## 测试分类

### 单元测试 (unit/)
- 测试单个组件功能
- 使用mock隔离依赖
- 快速执行

### 集成测试 (integration/)
- 测试组件间交互
- 使用真实数据库
- 验证完整流程

### 测试工具 (utils/)
- 测试数据生成
- 简化测试脚本
- 测试辅助功能

### 测试脚本 (scripts/)
- 测试运行工具
- 覆盖率分析
- 报告生成

## 运行测试

```bash
# 运行所有测试
python tests/scripts/run_tests.py

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行简化测试
python tests/utils/simple_test.py
```
