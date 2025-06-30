# 股票分析 MCP 服务

## 项目概述

这是一个基于 FastAPI-MCP 的股票分析服务，旨在通过 MCP 工具函数接口提供股票相关的综合数据和分析能力，包括价格、评分、技术报告和 AI 分析。该服务整合了原有项目中的股票数据获取和分析功能，并提供了现代化的 API 接口，作为前端与后端服务之间的桥梁。

## 功能特点

- **基于 FastAPI-MCP 构建**: 支持 SSE 协议，提供强大的 API 接口。
- **丰富的股票分析工具**: 提供多种股票数据获取和分析工具函数。
- **多市场支持**: 支持 A 股、港股、美股及基金数据分析。
- **集成 AI 分析**: 结合大语言模型进行深度分析。
- **异步处理**: 利用 FastAPI 和 Python 的异步特性，提高并发处理能力。
- **流式响应**: 支持 SSE 协议，实现实时数据流推送。
- **模块化设计**: 各个服务模块职责明确，便于维护和扩展。
- **依赖注入**: 使用 FastAPI 的依赖注入系统，简化代码结构。
- **全面错误处理**: 包含详细的异常捕获和错误响应机制。
- **MCP 工具集成**: 使用 FastApiMCP 库自动将 API 转换为 MCP 工具函数。

## 安装

1.  **克隆仓库**

    ```bash
    git clone https://github.com/wbsu2003/stock-scanner-mcp.git
    cd stock-scanner-mcp
    ```

2.  **安装依赖**

    ```bash
    pip install -r requirements.txt
    ```

3.  **配置环境变量**

    复制 `.env.example` 文件为 `.env`，并填写相关配置：

    ```bash
    cp .env.example .env
    ```

    编辑 `.env` 文件，填写 API 密钥等信息。

4.  **运行服务**

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。你也可以使用 Uvicorn 启动：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker 安装与运行

如果您希望通过 Docker 部署服务，可以按照以下步骤操作：

1.  **克隆仓库**

    ```bash
    git clone https://github.com/wbsu2003/stock-scanner-mcp.git
    cd stock-scanner-mcp
    ```

2.  **构建 Docker 镜像**

    在项目根目录下执行以下命令构建 Docker 镜像：

    ```bash
    docker build -t stock-scanner-mcp .
    ```

3.  **运行 Docker 容器**

    运行容器并映射端口。请确保通过环境变量 (`-e`) 或挂载 `.env` 文件来提供必要的配置信息，例如 API 密钥。

    ```bash
    docker run -d -p 8000:8000 --name stock-scanner-mcp-app \
      -e API_KEY="您的API密钥" \
      -e API_URL="您的API地址" \
      -e API_MODEL="您的大语言模型" \
      stock-scanner-mcp
    ```
    请将 `您的API密钥` 、"您的API地址" 、"您的大语言模型" 替换为实际的值。



## 主要 API 接口

服务提供以下核心 API 接口：

-   **分析单只股票**: `GET /stock_analyzer`
    -   通过股票代码和市场类型分析股票，返回包括价格、评分、技术分析和AI分析等综合信息，支持流式响应。
-   **获取股票价格信息**: `GET /stock_price`
    -   获取指定股票的最新价格、涨跌幅等基本价格信息。
-   **获取股票技术分析**: `GET /stock_technical_analysis`
    -   获取股票的技术指标分析，包括MA趋势、RSI、MACD信号、布林带等技术指标。
-   **获取股票评分**: `GET /stock_score`
    -   获取股票的综合评分和投资建议。
-   **获取股票AI分析**: `GET /stock_ai_analysis`
    -   使用AI对股票进行深度分析，提供趋势、风险、目标价位等综合分析结果。

## MCP 工具函数

FastApiMCP 库会自动将上述 API 注册为 MCP 工具函数，可通过 `/mcp` 端点获取其定义。以下是主要 MCP 工具函数：

1.  `analyze_stock` - 分析单只股票 (对应 `GET /stock_analyzer` 接口)
2.  `get_stock_price` - 获取股票价格信息 (对应 `GET /stock_price` 接口)
3.  `get_technical_analysis` - 获取股票技术分析 (对应 `GET /stock_technical_analysis` 接口)
4.  `get_stock_score` - 获取股票评分 (对应 `GET /stock_score` 接口)
5.  `get_ai_analysis` - 获取股票AI分析 (对应 `GET /stock_ai_analysis` 接口)

这些工具函数可以直接被大语言模型调用。

## 系统架构

该 MCP 服务作为前端与后端服务之间的桥梁，通过 FastAPI 框架提供 RESTful API 和 SSE 流式响应。它整合了以下核心服务：

-   **StockDataProvider**: 负责从数据源获取股票数据。
-   **StockAnalyzerService**: 协调数据提供、指标计算、评分和 AI 分析。
-   **AIAnalyzer**: 调用大语言模型 API 进行深度分析。
-   **TechnicalIndicator**: 计算技术指标。
-   **StockScorer**: 根据技术指标评分。

## 技术特点

-   **异步处理**: 利用 FastAPI 和 Python 的异步特性，提高并发处理能力。
-   **流式响应**: 支持 SSE 协议，实现实时数据流推送。
-   **模块化设计**: 各个服务模块职责明确，便于维护和扩展。
-   **依赖注入**: 使用 FastAPI 的依赖注入系统，简化代码结构。
-   **全面错误处理**: 包含详细的异常捕获和错误响应机制。
-   **MCP 工具集成**: 使用 FastApiMCP 库自动将 API 转换为 MCP 工具函数。

## 流式 API 端点

`stock_analyzer` 接口 (`GET /stock_analyzer`) 支持流式响应，客户端可以通过标准的 HTTP 请求访问，并处理服务端发送事件（SSE）流。

FastApiMCP 的 `/mcp` 端点也提供了工具定义的流式访问能力。

## 健康检查

可以通过 `/health` 端点检查服务状态：

```
http://localhost:8000/health
```

## 使用示例

### 在 MCP 中使用工具函数

在 MCP 客户端中，可以通过以下方式使用工具函数：

```python
import mcp

# 示例：分析单只股票 (流式响应)
async for chunk in mcp.use_tool("analyze_stock", {"stock_code": "600795", "market_type": "A"}):
    print(chunk)

# 示例：获取股票价格信息
price_info = await mcp.use_tool("get_stock_price", {"stock_code": "600795", "market_type": "A"})
print(price_info)

# 示例：获取股票技术分析
tech_analysis = await mcp.use_tool("get_technical_analysis", {"stock_code": "600795", "market_type": "A"})
print(tech_analysis)

# 示例：获取股票评分
score_info = await mcp.use_tool("get_stock_score", {"stock_code": "600795", "market_type": "A"})
print(score_info)

# 示例：获取股票AI分析
ai_analysis_result = await mcp.use_tool("get_ai_analysis", {"stock_code": "600795", "market_type": "A"})
print(ai_analysis_result)
```

### 访问 API 文档

服务启动后，可以通过以下链接访问自动生成的 API 文档 (Swagger UI / OpenAPI)：

```
http://localhost:8000/docs
```


## 依赖项

-   fastapi
-   fastapi-mcp
-   mcp
-   akshare
-   pandas
-   httpx
-   python-dotenv
-   uvicorn

## 许可证

MIT
