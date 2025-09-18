.PHONY: gen run test install-deps clean help

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
	@echo "📦 安装测试依赖..."
	pip install pytest pytest-cov pytest-json-report httpx fastapi

# 所有测试
test: install-deps
	@echo "🧪 运行所有测试..."
	python tests/scripts/run_tests.py

# 清理测试文件
clean:
	@echo "🧹 清理测试文件..."
	rm -rf __pycache__/
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
	@echo "✅ 清理完成"

# 显示帮助信息
help:
	@echo ""
	@echo "可用命令:"
	@echo ""
	@echo "其他命令:"
	@echo "  make install-deps      - 安装测试依赖"
	@echo "  make clean             - 清理测试文件"
	@echo "  make gen               - 生成模型文件"
	@echo "  make run               - 运行应用"
	@echo "  make test              - 运行所有测试"
	@echo "  make help              - 显示帮助信息"