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

## 运行服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。你也可以使用 Uvicorn 启动：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 主要 API 接口

服务提供以下核心 API 接口：

-   **获取股票数据**: `GET /stock-data/{stock_code}`
    -   获取指定股票代码的历史数据。
-   **分析单只股票**: `POST /analyze`
    -   对单只股票进行全面分析，包括技术指标计算和 AI 分析。支持流式响应模式。
-   **批量扫描股票**: `POST /scan`
    -   批量扫描多只股票，筛选出符合条件的股票。支持设置最低评分阈值和流式响应模式。
-   **批量获取股票数据**: `POST /stock-data-batch`
    -   一次性获取多只股票的历史数据。

## MCP 工具函数

FastApiMCP 库会自动将上述 API 注册为 MCP 工具函数，可通过 `/mcp` 端点获取其定义。以下是主要 MCP 工具函数：

1.  `analyze_stock` - 分析单只股票 (对应 `POST /analyze` 接口)
2.  `scan_stocks` - 批量扫描股票 (对应 `POST /scan` 接口)
3.  `get_stock_data` - 获取股票数据 (对应 `GET /stock-data/{stock_code}` 接口)

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

## SSE 端点

客户端可以通过 `/mcp` 端点进行访问，以获取实时数据流：

```
http://localhost:8000/mcp
```

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

# 示例：获取 MCP 工具定义
# response = await mcp.get_tool_definitions("http://localhost:8000/mcp")
# print(response)

# 示例：分析单只股票
# result = await mcp.use_tool("analyze_stock", {"stock_code": "000001", "market_type": "A"})
# print(result)

# 示例：批量扫描股票
# scan_results = await mcp.use_tool("scan_stocks", {"stock_codes": ["000001", "000002"], "min_score": 70})
# print(scan_results)

# 示例：获取股票历史数据
# data = await mcp.use_tool("get_stock_data", {"stock_code": "000001", "start_date": "2023-01-01", "end_date": "2023-12-31"})
# print(data)
```

### 访问 API 文档

服务启动后，可以通过以下链接访问自动生成的 API 文档 (Swagger UI / OpenAPI)：

```
http://localhost:8000/docs
```

## 未来改进方向

-   添加用户认证和权限控制。
-   增加缓存机制，提高数据获取效率。
-   实现更多市场和金融产品的支持。
-   优化 AI 分析模型和提示词。
-   添加更多技术指标和分析策略。

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
