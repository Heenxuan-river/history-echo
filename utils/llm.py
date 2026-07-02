"""
LLM 调用封装。
支持：Claude / OpenAI / DeepSeek / 智谱GLM / 阿里通义
优先从环境变量读取 API Key，没有则启用模拟模式。
"""
import os

# === 配置 ===
# LLM_PROVIDER: claude / openai / deepseek / glm / tongyi
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "deepseek").lower()

# Claude
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# OpenAI 兼容系列 (OpenAI / DeepSeek)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")

# 智谱 GLM
GLM_API_KEY = os.environ.get("GLM_API_KEY")
GLM_MODEL = os.environ.get("GLM_MODEL", "glm-4-plus")

# 阿里通义
TONGYI_API_KEY = os.environ.get("TONGYI_API_KEY")
TONGYI_MODEL = os.environ.get("TONGYI_MODEL", "qwen-plus")


def _call_openai_compat(base_url, api_key, model, system_prompt, messages):
    """调用 OpenAI 兼容接口"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            max_tokens=2000,
        )
        return resp.choices[0].message.content
    except ImportError:
        return None
    except Exception as e:
        return f"[API 错误: {e}]"


def _call_claude(system_prompt, messages):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            system=system_prompt,
            messages=messages,
            max_tokens=2000,
        )
        return resp.content[0].text
    except Exception:
        return None


def _call_glm(system_prompt, messages):
    """调用智谱 GLM"""
    return _call_openai_compat(
        "https://open.bigmodel.cn/api/paas/v4/",
        GLM_API_KEY,
        GLM_MODEL,
        system_prompt,
        messages,
    )


def _call_tongyi(system_prompt, messages):
    """调用阿里通义千问"""
    return _call_openai_compat(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/",
        TONGYI_API_KEY,
        TONGYI_MODEL,
        system_prompt,
        messages,
    )


def chat(system_prompt, user_message):
    """统一 LLM 调用接口"""
    msgs = [{"role": "user", "content": user_message}]

    if LLM_PROVIDER == "claude" and ANTHROPIC_API_KEY:
        return _call_claude(system_prompt, msgs)
    elif LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        return _call_openai_compat(
            "https://api.openai.com/v1",
            OPENAI_API_KEY, "gpt-4o",
            system_prompt, msgs,
        )
    elif LLM_PROVIDER == "deepseek" and OPENAI_API_KEY:
        return _call_openai_compat(
            "https://api.deepseek.com",
            OPENAI_API_KEY, "deepseek-chat",
            system_prompt, msgs,
        )
    elif LLM_PROVIDER == "glm" and GLM_API_KEY:
        return _call_glm(system_prompt, msgs)
    elif LLM_PROVIDER == "tongyi" and TONGYI_API_KEY:
        return _call_tongyi(system_prompt, msgs)

    return None


def chat_with_history(system_prompt, messages):
    """多轮对话"""
    if LLM_PROVIDER == "claude" and ANTHROPIC_API_KEY:
        return _call_claude(system_prompt, messages)
    elif LLM_PROVIDER == "deepseek" and OPENAI_API_KEY:
        return _call_openai_compat(
            "https://api.deepseek.com",
            OPENAI_API_KEY, "deepseek-chat",
            system_prompt, messages,
        )
    elif LLM_PROVIDER == "glm" and GLM_API_KEY:
        return _call_glm(system_prompt, messages)
    elif LLM_PROVIDER == "tongyi" and TONGYI_API_KEY:
        return _call_tongyi(system_prompt, messages)
    return None