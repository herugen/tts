.PHONY: venv gen run test install-deps clean help

venv:
	@echo "🚀 创建venv..."
	python -m venv venv
	@echo "✅ 虚拟环境创建完成"
	@echo "请手动激活虚拟环境: source venv/bin/activate"

# 生成模型文件
gen:
	@echo "🔧 生成模型文件..."
	datamodel-codegen \
		--input api/oc8r.yml \
		--input-file-type openapi \
		--output app/models/oc8r.py \
		--target-python-version 3.12 \
		--reuse-model \
		--disable-timestamp \
		--output-model-type pydantic_v2.BaseModel \
		--set-default-enum-member
	datamodel-codegen \
		--input api/indextts2.yml \
		--input-file-type openapi \
		--output app/models/indextts2.py \
		--target-python-version 3.12 \
		--reuse-model \
		--disable-timestamp \
		--output-model-type pydantic_v2.BaseModel \
		--set-default-enum-member
	@echo "✅ 模型文件生成完成"

# 运行应用
run:
	@echo "🚀 启动应用..."
	uvicorn app.main:app --reload


# 安装测试依赖
install-deps:
	@echo "📦 安装依赖..."
	pip install -r requirements.txt

# 所有测试
test:
	@echo "🧪 运行所有测试..."
	python tests/scripts/run_tests.py

# 代码格式化
format:
	@echo "🎨 格式化代码..."
	black app/ tests/
	@echo "✅ 代码格式化完成"

# 代码质量检查
lint:
	@echo "🔍 代码质量检查..."
	flake8 app/ tests/
	mypy app/ tests/ --ignore-missing-imports
	@echo "✅ 代码质量检查完成"

# 清理测试文件
clean:
	@echo "🧹 清理测试文件..."
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf tests/__pycache__/
	rm -rf tests/unit/__pycache__/
	rm -rf tests/integration/__pycache__/
	rm -rf tests/utils/__pycache__/
	rm -rf tests/scripts/__pycache__/
	rm -rf app/__pycache__/
	rm -rf app/api/__pycache__/
	rm -rf app/infra/__pycache__/
	rm -rf app/models/__pycache__/
	rm -rf app/domain/__pycache__/
	rm -rf app/domain/strategies/__pycache__/
	rm -rf data
	@echo "✅ 清理完成"

# 显示帮助信息
help:
	@echo ""
	@echo "可用命令:"
	@echo ""
	@echo "  make venv              - 创建虚拟环境"
	@echo "  make install-deps      - 安装依赖"
	@echo "  make gen               - 生成模型文件"
	@echo "  make run               - 运行应用"
	@echo "  make test              - 运行所有测试"
	@echo "  make format            - 格式化代码"
	@echo "  make lint              - 代码质量检查"
	@echo "  make clean             - 清理测试文件"
	@echo "  make help              - 显示帮助信息"
	@echo ""
	@echo "使用说明:"
	@echo "  1. 首次使用: make venv && make install-deps"
	@echo "  2. 生成模型: make gen"
	@echo "  3. 运行应用: make run"
	@echo "  4. 运行测试: make test"