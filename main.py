import os
import json
from typing import Dict, Any, AsyncGenerator
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime

# 导入服务
from services.stock_analyzer_service import StockAnalyzerService
from utils.logger import get_logger

# 加载环境变量
load_dotenv()

# 获取日志器
logger = get_logger()

# 创建FastAPI应用
app = FastAPI(
    title="股票分析MCP服务",
    description="基于FastAPI-MCP的股票分析服务，提供股票数据、技术分析和AI分析功能"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建股票分析服务实例
analyzer = StockAnalyzerService()

# 定义请求模型
class StockAnalysisRequest(BaseModel):
    stock_code: str
    market_type: str = "A"

# 定义API端点
@app.get(
    "/stock_analyzer", 
    operation_id="analyze_stock",
    summary="分析单只股票",
    description="通过股票代码和市场类型分析股票，返回包括价格、评分、技术分析和AI分析等综合信息"
)
async def analyze_stock(
    stock_code: str = Query(..., description="股票代码，如'600795'"),
    market_type: str = Query("A", description="市场类型，默认为'A'股，可选值：A(A股)、HK(港股)、US(美股)、ETF(场内ETF)、LOF(场内LOF)")
) -> StreamingResponse:
    """
    分析单只股票（流式API）
    
    Args:
        stock_code: 股票代码
        market_type: 市场类型，默认为'A'股
    
    Returns:
        以流式响应返回股票分析结果
    """
    logger.info(f"API调用 (流式): analyze_stock({stock_code}, {market_type})")

    async def stream_generator() -> AsyncGenerator[str, None]:
        """异步生成器，用于流式传输分析结果"""
        try:
            # 1. 获取股票数据 (直接调用 data_provider)
            cleaned_stock_code = stock_code
            if market_type == 'A': # 仅对A股进行前缀清理
                if stock_code.lower().startswith('sh') or stock_code.lower().startswith('sz'):
                    cleaned_stock_code = stock_code[2:]
                    logger.debug(f"股票代码 {stock_code} 已清理为 {cleaned_stock_code}")
            df = await analyzer.data_provider.get_stock_data(cleaned_stock_code, market_type)

            # 3. 检查数据错误
            if hasattr(df, 'error'):
                error_msg = df.error
                logger.error(f"获取股票数据时出错: {error_msg}")
                yield json.dumps({"error": error_msg, "stock_code": cleaned_stock_code, "status": "error"}) + '\n'
                return

            if df.empty:
                error_msg = f"获取到的股票 {cleaned_stock_code} 数据为空"
                logger.error(error_msg)
                yield json.dumps({"error": error_msg, "stock_code": cleaned_stock_code, "status": "error"}) + '\n'
                return

            # 4. 计算技术指标 (直接调用 indicator)
            df_with_indicators = analyzer.indicator.calculate_indicators(df)

            # 5. 计算评分 (直接调用 scorer)
            score = analyzer.scorer.calculate_score(df_with_indicators)
            recommendation = analyzer.scorer.get_recommendation(score)

            # 6. 准备基本分析结果
            latest_data = df_with_indicators.iloc[-1]
            previous_data = df_with_indicators.iloc[-2] if len(df_with_indicators) > 1 else latest_data
            price_change_value = latest_data['Close'] - previous_data['Close']
            change_percent = latest_data.get('Change_pct')
            if change_percent is None and previous_data['Close'] != 0:
                change_percent = (price_change_value / previous_data['Close']) * 100

            ma_short = latest_data.get('MA5', 0)
            ma_medium = latest_data.get('MA20', 0)
            ma_long = latest_data.get('MA60', 0)
            if ma_short > ma_medium > ma_long: ma_trend = "UP"
            elif ma_short < ma_medium < ma_long: ma_trend = "DOWN"
            else: ma_trend = "FLAT"

            macd = latest_data.get('MACD', 0)
            signal = latest_data.get('Signal', 0)
            if macd > signal: macd_signal = "BUY"
            elif macd < signal: macd_signal = "SELL"
            else: macd_signal = "HOLD"

            volume = latest_data.get('Volume', 0)
            volume_ma = latest_data.get('Volume_MA', 0)
            if volume > volume_ma * 1.5: volume_status = "HIGH"
            elif volume < volume_ma * 0.5: volume_status = "LOW"
            else: volume_status = "NORMAL"

            basic_result = {
                "stock_code": stock_code,
                "market_type": market_type,
                "analysis_date": datetime.now().strftime('%Y-%m-%d'),
                "score": score,
                "price": latest_data['Close'],
                "price_change_value": price_change_value,
                "change_percent": change_percent,
                "ma_trend": ma_trend,
                "rsi": latest_data.get('RSI', 0),
                "macd_signal": macd_signal,
                "volume_status": volume_status,
                "recommendation": recommendation,
                "ai_analysis": ""
            }
            
            # 7. Yield 基本分析结果
            yield json.dumps(basic_result) + '\n'

            # 8. 调用AI分析 (直接调用 ai_analyzer)
            async for analysis_chunk in analyzer.ai_analyzer.get_ai_analysis(df_with_indicators, cleaned_stock_code, market_type, stream=True):
                yield analysis_chunk + '\n'

        except KeyError as ke:
            error_msg = f"股票代码 {stock_code} 在数据源中不存在或格式不正确: {str(ke)}"
            logger.error(f"分析股票时出错: {error_msg}")
            yield json.dumps({"error": error_msg, "stock_code": stock_code, "status": "error"}) + '\n'
        except Exception as e:
            logger.error(f"分析股票时出错: {str(e)}")
            error_message = json.dumps({"error": str(e)})
            yield f"{error_message}\n"

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")

@app.get(
    "/stock_price", 
    operation_id="get_stock_price",
    summary="获取股票价格信息",
    description="获取指定股票的最新价格、涨跌幅等基本价格信息"
)
async def get_stock_price(
    stock_code: str = Query(..., description="股票代码，如'600795'"),
    market_type: str = Query("A", description="市场类型，默认为'A'股，可选值：A(A股)、HK(港股)、US(美股)、ETF(场内ETF)、LOF(场内LOF)")
) -> Dict[str, Any]:
    """
    获取股票价格信息
    
    Args:
        stock_code: 股票代码
        market_type: 市场类型，默认为'A'股
    
    Returns:
        股票价格信息
    """
    try:
        logger.info(f"API调用: get_stock_price({stock_code}, {market_type})")
        
        cleaned_stock_code = stock_code
        if market_type == 'A': # 仅对A股进行前缀清理
            if stock_code.lower().startswith('sh') or stock_code.lower().startswith('sz'):
                cleaned_stock_code = stock_code[2:]
                logger.debug(f"股票代码 {stock_code} 已清理为 {cleaned_stock_code}")

        # 获取股票数据
        df = await analyzer.data_provider.get_stock_data(cleaned_stock_code, market_type)
        
        # 检查是否有错误
        if hasattr(df, 'error'):
            raise HTTPException(status_code=400, detail=df.error)
        
        # 检查数据是否为空
        if df.empty:
            raise HTTPException(status_code=404, detail=f"获取到的股票 {cleaned_stock_code} 数据为空")
        
        # 获取最新数据
        latest_data = df.iloc[-1]
        previous_data = df.iloc[-2] if len(df) > 1 else latest_data
        
        # 价格变动绝对值
        price_change_value = latest_data['Close'] - previous_data['Close']
        
        # 获取涨跌幅
        change_percent = latest_data.get('Change_pct')
        
        # 如果原始数据中没有涨跌幅，才进行计算
        if change_percent is None and previous_data['Close'] != 0:
            change_percent = (price_change_value / previous_data['Close']) * 100
        
        return {
            "stock_code": stock_code,
            "market_type": market_type,
            "price": float(latest_data['Close']),
            "open": float(latest_data['Open']),
            "high": float(latest_data['High']),
            "low": float(latest_data['Low']),
            "volume": float(latest_data['Volume']),
            "price_change_value": float(price_change_value),
            "change_percent": float(change_percent) if change_percent is not None else None,
            "date": latest_data.name.strftime('%Y-%m-%d')
        }
    
    except HTTPException:
        raise
    except KeyError as ke:
        logger.error(f"获取股票价格时出错: 股票代码 {cleaned_stock_code} 在数据源中不存在或格式不正确: {str(ke)}")
        raise HTTPException(status_code=400, detail=f"股票代码 {cleaned_stock_code} 在数据源中不存在或格式不正确")
    except Exception as e:
        logger.error(f"获取股票价格时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/stock_technical_analysis", 
    operation_id="get_technical_analysis",
    summary="获取股票技术分析",
    description="获取股票的技术指标分析，包括MA趋势、RSI、MACD信号、布林带等技术指标"
)
async def get_technical_analysis(
    stock_code: str = Query(..., description="股票代码，如'600795'"),
    market_type: str = Query("A", description="市场类型，默认为'A'股，可选值：A(A股)、HK(港股)、US(美股)、ETF(场内ETF)、LOF(场内LOF)")
) -> Dict[str, Any]:
    """
    获取股票技术分析
    
    Args:
        stock_code: 股票代码
        market_type: 市场类型，默认为'A'股
    
    Returns:
        股票技术分析结果
    """
    try:
        logger.info(f"API调用: get_technical_analysis({stock_code}, {market_type})")
        
        cleaned_stock_code = stock_code
        if market_type == 'A': # 仅对A股进行前缀清理
            if stock_code.lower().startswith('sh') or stock_code.lower().startswith('sz'):
                cleaned_stock_code = stock_code[2:]
                logger.debug(f"股票代码 {stock_code} 已清理为 {cleaned_stock_code}")

        # 获取股票数据
        df = await analyzer.data_provider.get_stock_data(cleaned_stock_code, market_type)
        
        # 检查是否有错误
        if hasattr(df, 'error'):
            raise HTTPException(status_code=400, detail=df.error)
        
        # 检查数据是否为空
        if df.empty:
            raise HTTPException(status_code=404, detail=f"获取到的股票 {cleaned_stock_code} 数据为空")
        
        # 计算技术指标
        df_with_indicators = analyzer.indicator.calculate_indicators(df)
        
        # 获取最新数据
        latest_data = df_with_indicators.iloc[-1]
        
        # 确定MA趋势
        ma_short = latest_data.get('MA5', 0)
        ma_medium = latest_data.get('MA20', 0)
        ma_long = latest_data.get('MA60', 0)
        
        if ma_short > ma_medium > ma_long:
            ma_trend = "UP"
        elif ma_short < ma_medium < ma_long:
            ma_trend = "DOWN"
        else:
            ma_trend = "FLAT"
            
        # 确定MACD信号
        macd = latest_data.get('MACD', 0)
        signal = latest_data.get('Signal', 0)
        
        if macd > signal:
            macd_signal = "BUY"
        elif macd < signal:
            macd_signal = "SELL"
        else:
            macd_signal = "HOLD"
            
        # 确定成交量状态
        volume = latest_data.get('Volume', 0)
        volume_ma = latest_data.get('Volume_MA', 0)
        
        if volume > volume_ma * 1.5:
            volume_status = "HIGH"
        elif volume < volume_ma * 0.5:
            volume_status = "LOW"
        else:
            volume_status = "NORMAL"
        
        return {
            "stock_code": stock_code,
            "market_type": market_type,
            "ma_trend": ma_trend,
            "rsi": float(latest_data.get('RSI', 0)),
            "macd": float(macd),
            "macd_signal": macd_signal,
            "volume_status": volume_status,
            "bollinger_upper": float(latest_data.get('BB_Upper', 0)),
            "bollinger_middle": float(latest_data.get('BB_Middle', 0)),
            "bollinger_lower": float(latest_data.get('BB_Lower', 0))
        }
    
    except HTTPException:
        raise
    except KeyError as ke:
        logger.error(f"获取技术分析时出错: 股票代码 {cleaned_stock_code} 在数据源中不存在或格式不正确: {str(ke)}")
        raise HTTPException(status_code=400, detail=f"股票代码 {cleaned_stock_code} 在数据源中不存在或格式不正确")
    except Exception as e:
        logger.error(f"获取技术分析时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/stock_score", 
    operation_id="get_stock_score",
    summary="获取股票评分",
    description="获取股票的综合评分和投资建议"
)
async def get_stock_score(
    stock_code: str = Query(..., description="股票代码，如'600795'"),
    market_type: str = Query("A", description="市场类型，默认为'A'股，可选值：A(A股)、HK(港股)、US(美股)、ETF(场内ETF)、LOF(场内LOF)")
) -> Dict[str, Any]:
    """
    获取股票评分
    
    Args:
        stock_code: 股票代码
        market_type: 市场类型，默认为'A'股
    
    Returns:
        股票评分结果
    """
    try:
        logger.info(f"API调用: get_stock_score({stock_code}, {market_type})")
        
        cleaned_stock_code = stock_code
        if market_type == 'A': # 仅对A股进行前缀清理
            if stock_code.lower().startswith('sh') or stock_code.lower().startswith('sz'):
                cleaned_stock_code = stock_code[2:]
                logger.debug(f"股票代码 {stock_code} 已清理为 {cleaned_stock_code}")

        # 获取股票数据
        df = await analyzer.data_provider.get_stock_data(cleaned_stock_code, market_type)
        
        # 检查是否有错误
        if hasattr(df, 'error'):
            raise HTTPException(status_code=400, detail=df.error)
        
        # 检查数据是否为空
        if df.empty:
            raise HTTPException(status_code=404, detail=f"获取到的股票 {cleaned_stock_code} 数据为空")
        
        # 计算技术指标
        df_with_indicators = analyzer.indicator.calculate_indicators(df)
        
        # 计算评分
        score = analyzer.scorer.calculate_score(df_with_indicators)
        recommendation = analyzer.scorer.get_recommendation(score)
        
        return {
            "stock_code": stock_code,
            "market_type": market_type,
            "score": score,
            "recommendation": recommendation
        }
    
    except HTTPException:
        raise
    except KeyError as ke:
        logger.error(f"获取股票评分时出错: 股票代码 {cleaned_stock_code} 在数据源中不存在或格式不正确: {str(ke)}")
        raise HTTPException(status_code=400, detail=f"股票代码 {cleaned_stock_code} 在数据源中不存在或格式不正确")
    except Exception as e:
        logger.error(f"获取股票评分时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/stock_ai_analysis", 
    operation_id="get_ai_analysis",
    summary="获取股票AI分析",
    description="使用AI对股票进行深度分析，提供趋势、风险、目标价位等综合分析结果"
)
async def get_ai_analysis(
    stock_code: str = Query(..., description="股票代码，如'600795'"),
    market_type: str = Query("A", description="市场类型，默认为'A'股，可选值：A(A股)、HK(港股)、US(美股)、ETF(场内ETF)、LOF(场内LOF)")
) -> Dict[str, Any]:
    """
    获取股票AI分析
    
    Args:
        stock_code: 股票代码
        market_type: 市场类型，默认为'A'股
    
    Returns:
        股票AI分析结果
    """
    try:
        logger.info(f"API调用: get_ai_analysis({stock_code}, {market_type})")
        
        cleaned_stock_code = stock_code
        if market_type == 'A': # 仅对A股进行前缀清理
            if stock_code.lower().startswith('sh') or stock_code.lower().startswith('sz'):
                cleaned_stock_code = stock_code[2:]
                logger.debug(f"股票代码 {stock_code} 已清理为 {cleaned_stock_code}")

        # 获取股票数据
        df = await analyzer.data_provider.get_stock_data(cleaned_stock_code, market_type)
        
        # 检查是否有错误
        if hasattr(df, 'error'):
            raise HTTPException(status_code=400, detail=df.error)
        
        # 检查数据是否为空
        if df.empty:
            raise HTTPException(status_code=404, detail=f"获取到的股票 {cleaned_stock_code} 数据为空")
        
        # 计算技术指标
        df_with_indicators = analyzer.indicator.calculate_indicators(df)
        
        # 收集AI分析结果
        full_ai_analysis_text = ""
        analysis_score = None
        analysis_recommendation = None

        async for result_json_str in analyzer.ai_analyzer.get_ai_analysis(df_with_indicators, stock_code, market_type, stream=True):
            try:
                result = json.loads(result_json_str)
                
                if "ai_analysis_chunk" in result:
                    full_ai_analysis_text += result["ai_analysis_chunk"]
                
                if result.get("status") == "completed":
                    analysis_score = result.get("score")
                    analysis_recommendation = result.get("recommendation")
                    # Break after receiving the completed status, as all chunks should have been collected
                    break 
            except json.JSONDecodeError:
                # This should ideally not happen if ai_analyzer.py always yields valid JSON
                logger.error(f"Failed to decode JSON from AI analysis stream: {result_json_str}")
                continue
        
        if full_ai_analysis_text or analysis_score is not None or analysis_recommendation is not None:
            return {
                "stock_code": stock_code,
                "market_type": market_type,
                "ai_analysis": full_ai_analysis_text,
                "score": analysis_score,
                "recommendation": analysis_recommendation
            }
        else:
            raise HTTPException(status_code=404, detail="未获取到AI分析结果")
    
    except HTTPException:
        raise
    except KeyError as ke:
        logger.error(f"获取AI分析时出错: 股票代码 {cleaned_stock_code} 在数据源中不存在或格式不正确: {str(ke)}")
        raise HTTPException(status_code=400, detail=f"股票代码 {cleaned_stock_code} 在数据源中不存在或格式不正确")
    except Exception as e:
        logger.error(f"获取AI分析时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 健康检查端点
@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {"status": "ok", "message": "股票分析MCP服务正常运行"}

# 创建MCP服务
mcp = FastApiMCP(
    app,
    name="股票分析MCP服务",
    description="基于FastAPI-MCP的股票分析服务，提供股票数据、技术分析和AI分析功能"
)

# 挂载MCP服务
mcp.mount()

# 必须在所有路由定义后调用
mcp.setup_server()

# 主函数
if __name__ == "__main__":
    import uvicorn
    
    # 获取端口
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # 启动服务
    uvicorn.run("main:app", host=host, port=port, reload=True)
